#!/usr/bin/env python3
"""
GPU Host Agent for Labhya Compute Platform

This agent runs on host machines with GPUs and:
1. Establishes reverse SSH tunnel to the main server
2. Monitors GPU status and reports metrics
3. Manages Docker containers for renters
4. Handles session lifecycle

Installation:
1. Install dependencies: pip install requests psutil nvidia-ml-py
2. Configure settings in config section
3. Run: python host_agent.py
"""

import os
import sys
import time
import json
import socket
import logging
import requests
import subprocess
import threading
from datetime import datetime
from typing import Dict, Optional, List

try:
    import psutil
    import pynvml
except ImportError:
    print("Error: Required packages not installed.")
    print("Please install: pip install psutil nvidia-ml-py requests")
    sys.exit(1)

# Configuration
CONFIG = {
    "server_url": "https://your-server.com/api",  # Your EC2 server URL
    "auth_token": "your_jwt_token_here",  # JWT token for authentication
    "host_id": "your_host_uuid_here",  # Host UUID from registration
    "ssh_user": "ubuntu",  # SSH username for connections
    "ssh_port": 22,  # SSH port
    "report_interval": 30,  # Seconds between status reports
    "log_level": "INFO",
    "tunnel_server": "your-ec2-server.com",  # EC2 server for reverse tunnels
    "tunnel_user": "ubuntu",  # Username on tunnel server
    "tunnel_key": "/path/to/ssh/private/key"  # SSH private key path
}

# Setup logging
logging.basicConfig(
    level=getattr(logging, CONFIG["log_level"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('host_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HostAgent')


class GPUMonitor:
    """Monitor GPU status and usage"""
    
    def __init__(self):
        try:
            pynvml.nvmlInit()
            self.device_count = pynvml.nvmlDeviceGetCount()
            logger.info(f"Initialized GPU monitoring for {self.device_count} devices")
        except Exception as e:
            logger.error(f"Failed to initialize GPU monitoring: {e}")
            self.device_count = 0
    
    def get_gpu_info(self) -> List[Dict]:
        """Get comprehensive GPU information"""
        gpus = []
        
        try:
            for i in range(self.device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # Basic info
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                # Utilization
                try:
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = utilization.gpu
                    memory_util = utilization.memory
                except:
                    gpu_util = 0
                    memory_util = 0
                
                # Temperature
                try:
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temperature = 0
                
                # Power
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # Convert to watts
                except:
                    power = 0
                
                gpu_info = {
                    'device_id': i,
                    'name': name,
                    'memory_total': memory_info.total // (1024**2),  # MB
                    'memory_used': memory_info.used // (1024**2),   # MB
                    'memory_free': memory_info.free // (1024**2),   # MB
                    'gpu_utilization': gpu_util,
                    'memory_utilization': memory_util,
                    'temperature': temperature,
                    'power_usage': power,
                    'timestamp': datetime.now().isoformat()
                }
                
                gpus.append(gpu_info)
                
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
        
        return gpus


class TunnelManager:
    """Manage SSH tunnels to the main server"""
    
    def __init__(self):
        self.active_tunnels = {}
        self.tunnel_processes = {}
    
    def create_reverse_tunnel(self, session_id: str, local_port: int, remote_port: int) -> bool:
        """Create reverse SSH tunnel for a session"""
        try:
            # SSH command for reverse tunnel
            ssh_command = [
                'ssh', '-N', '-R',
                f'{remote_port}:localhost:{local_port}',
                f'{CONFIG["tunnel_user"]}@{CONFIG["tunnel_server"]}',
                '-i', CONFIG["tunnel_key"],
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'ServerAliveInterval=30',
                '-o', 'ServerAliveCountMax=3'
            ]
            
            process = subprocess.Popen(
                ssh_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to establish
            time.sleep(2)
            
            if process.poll() is None:
                self.tunnel_processes[session_id] = process
                self.active_tunnels[session_id] = {
                    'local_port': local_port,
                    'remote_port': remote_port,
                    'process_id': process.pid
                }
                logger.info(f"Created tunnel for session {session_id}: {local_port} -> {remote_port}")
                return True
            else:
                stderr = process.stderr.read().decode()
                logger.error(f"Tunnel failed for session {session_id}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating tunnel for session {session_id}: {e}")
            return False
    
    def close_tunnel(self, session_id: str) -> bool:
        """Close tunnel for a session"""
        try:
            if session_id in self.tunnel_processes:
                process = self.tunnel_processes[session_id]
                process.terminate()
                process.wait(timeout=5)
                
                del self.tunnel_processes[session_id]
                if session_id in self.active_tunnels:
                    del self.active_tunnels[session_id]
                
                logger.info(f"Closed tunnel for session {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error closing tunnel for session {session_id}: {e}")
        return False


class DockerManager:
    """Manage Docker containers for GPU access"""
    
    def create_gpu_container(self, session_id: str, gpu_id: int, image: str = "nvidia/cuda:11.8-devel-ubuntu20.04") -> Optional[str]:
        """Create Docker container with GPU access"""
        try:
            container_name = f"labhya-session-{session_id[:8]}"
            
            docker_command = [
                'docker', 'run', '-d',
                '--name', container_name,
                '--gpus', f'device={gpu_id}',
                '--restart', 'unless-stopped',
                '--shm-size', '8g',
                '-p', '22',  # SSH port
                image,
                '/bin/bash', '-c', 'service ssh start && tail -f /dev/null'
            ]
            
            result = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                check=True
            )

            container_id = result.stdout.strip()
            logger.info(f"Created container {container_name} for session {session_id}")

            # Generate a random SSH password for the 'ubuntu' user
            import secrets, string
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for _ in range(12))

            # Try to ensure SSH server is installed and running, and set password
            try:
                # Install openssh-server (may already be present)
                subprocess.run([
                    'docker', 'exec', container_name,
                    'bash', '-c', 'apt-get update && apt-get install -y openssh-server >/dev/null'
                ], check=False)

                # Ensure /var/run/sshd exists
                subprocess.run([
                    'docker', 'exec', container_name,
                    'bash', '-c', 'mkdir -p /var/run/sshd'
                ], check=False)

                # Create or update ubuntu user password
                subprocess.run([
                    'docker', 'exec', container_name,
                    'bash', '-c', f"useradd -m ubuntu || true && echo 'ubuntu:{password}' | chpasswd"
                ], check=False)

                # Start ssh service inside container
                subprocess.run([
                    'docker', 'exec', container_name,
                    'bash', '-c', 'service ssh start || /usr/sbin/sshd || true'
                ], check=False)
            except Exception as e:
                logger.warning(f"Could not fully configure SSH in container {container_name}: {e}")

            # Return container id and generated password so the agent can update the session
            return container_id, password
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create container for session {session_id}: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error creating container for session {session_id}: {e}")
            return None
    
    def stop_container(self, session_id: str) -> bool:
        """Stop and remove container"""
        try:
            container_name = f"labhya-session-{session_id[:8]}"
            
            # Stop container
            subprocess.run(['docker', 'stop', container_name], check=True)
            
            # Remove container
            subprocess.run(['docker', 'rm', container_name], check=True)
            
            logger.info(f"Stopped container for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping container for session {session_id}: {e}")
            return False


class HostAgent:
    """Main host agent class"""
    
    def __init__(self):
        self.gpu_monitor = GPUMonitor()
        self.tunnel_manager = TunnelManager()
        self.docker_manager = DockerManager()
        self.running = False
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {CONFIG["auth_token"]}',
            'Content-Type': 'application/json'
        })
    
    def start(self):
        """Start the host agent"""
        logger.info("Starting Labhya GPU Host Agent...")
        self.running = True
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()
        
        # Start session management thread
        session_thread = threading.Thread(target=self._session_management_loop, daemon=True)
        session_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()
    
    def stop(self):
        """Stop the host agent"""
        logger.info("Stopping host agent...")
        self.running = False
        
        # Close all tunnels
        for session_id in list(self.tunnel_manager.active_tunnels.keys()):
            self.tunnel_manager.close_tunnel(session_id)
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get GPU info
                gpu_info = self.gpu_monitor.get_gpu_info()
                
                # Report to server
                self._report_gpu_status(gpu_info)
                
                # Sleep until next report
                time.sleep(CONFIG["report_interval"])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def _session_management_loop(self):
        """Manage active sessions"""
        while self.running:
            try:
                # Check for new sessions
                self._check_new_sessions()
                
                # Check session status
                self._check_session_status()
                
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in session management loop: {e}")
                time.sleep(10)
    
    def _report_gpu_status(self, gpu_info: List[Dict]):
        """Report GPU status to server"""
        try:
            response = self.session.post(
                f"{CONFIG['server_url']}/hosts/{CONFIG['host_id']}/update_gpu_status/",
                json={'gpus': gpu_info}
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to report GPU status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error reporting GPU status: {e}")
    
    def _check_new_sessions(self):
        """Check for new sessions assigned to this host"""
        try:
            response = self.session.get(
                f"{CONFIG['server_url']}/hosts/{CONFIG['host_id']}/sessions/",
                params={'status': 'PENDING'}
            )
            
            if response.status_code == 200:
                sessions = response.json()
                for session in sessions:
                    self._handle_new_session(session)
                    
        except Exception as e:
            logger.error(f"Error checking new sessions: {e}")
    
    def _handle_new_session(self, session: Dict):
        """Handle a new session"""
        session_id = session['id']
        gpu_id = session['gpu']['device_id'] if 'device_id' in session['gpu'] else 0
        
        logger.info(f"Handling new session {session_id}")
        
        # Create Docker container (returns (container_id, ssh_password) on success)
        container_result = self.docker_manager.create_gpu_container(session_id, gpu_id)

        if container_result:
            # Unpack result
            if isinstance(container_result, tuple) or isinstance(container_result, list):
                container_id, ssh_password = container_result
            else:
                container_id = container_result
                ssh_password = None

            # Create reverse tunnel
            local_port = 22  # SSH port in container
            remote_port = 2200 + int(session_id.replace('-', '')[:4], 16) % 1000  # Generate unique port

            if self.tunnel_manager.create_reverse_tunnel(session_id, local_port, remote_port):
                # Update session status with SSH credentials so frontend can show them
                extra = {
                    'ssh_port': remote_port,
                    'container_id': container_id,
                    'ssh_host': CONFIG.get('tunnel_server', 'localhost')
                }
                if ssh_password:
                    extra['ssh_password'] = ssh_password

                self._update_session_status(session_id, 'ACTIVE', extra)
            else:
                self._update_session_status(session_id, 'FAILED', {
                    'error': 'Failed to create tunnel'
                })
        else:
            self._update_session_status(session_id, 'FAILED', {
                'error': 'Failed to create container'
            })
    
    def _check_session_status(self):
        """Check status of active sessions"""
        try:
            response = self.session.get(
                f"{CONFIG['server_url']}/hosts/{CONFIG['host_id']}/sessions/",
                params={'status': 'ACTIVE'}
            )
            
            if response.status_code == 200:
                sessions = response.json()
                for session in sessions:
                    session_id = session['id']
                    
                    # Check if tunnel is still active
                    if session_id not in self.tunnel_manager.active_tunnels:
                        # Session ended, clean up
                        self.docker_manager.stop_container(session_id)
                        self.tunnel_manager.close_tunnel(session_id)
                        
        except Exception as e:
            logger.error(f"Error checking session status: {e}")
    
    def _update_session_status(self, session_id: str, status: str, extra_data: Dict = None):
        """Update session status on server"""
        try:
            data = {'status': status}
            if extra_data:
                data.update(extra_data)
            
            response = self.session.patch(
                f"{CONFIG['server_url']}/sessions/{session_id}/",
                json=data
            )
            
            if response.status_code == 200:
                logger.info(f"Updated session {session_id} status to {status}")
            else:
                logger.warning(f"Failed to update session status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error updating session status: {e}")


def main():
    """Main entry point"""
    # Validate configuration
    required_configs = ['server_url', 'auth_token', 'host_id']
    missing_configs = [key for key in required_configs if not CONFIG.get(key) or CONFIG[key] == f"your_{key}_here"]
    
    if missing_configs:
        logger.error(f"Missing required configuration: {missing_configs}")
        logger.error("Please update the CONFIG section with your actual values")
        sys.exit(1)
    
    # Check if running as root for Docker access
    if os.geteuid() != 0:
        logger.warning("Not running as root. Docker commands may fail.")
    
    # Create and start agent
    agent = HostAgent()
    agent.start()


if __name__ == "__main__":
    main()
