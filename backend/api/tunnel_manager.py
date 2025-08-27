import subprocess
import threading
import time
import logging
import socket
import json
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from .models import Session

logger = logging.getLogger(__name__)

class SSHTunnelManager:
    """
    Manages reverse SSH tunnels for GPU rental sessions
    """
    
    def __init__(self):
        self.active_tunnels: Dict[str, subprocess.Popen] = {}
        self.tunnel_ports: Dict[str, int] = {}
        self.base_port = getattr(settings, 'SSH_TUNNEL_BASE_PORT', 2200)
        self.max_ports = getattr(settings, 'SSH_TUNNEL_MAX_PORTS', 1000)
        
    def create_tunnel(self, session_id: str, host_ip: str, host_port: int = 22, 
                     host_username: str = 'ubuntu', private_key_path: str = None) -> Optional[Tuple[int, str]]:
        """
        Create a reverse SSH tunnel for a session
        
        Args:
            session_id: UUID of the session
            host_ip: IP address of the host machine
            host_port: SSH port on host machine (default 22)
            host_username: Username for SSH connection
            private_key_path: Path to SSH private key
            
        Returns:
            Tuple of (local_port, connection_string) if successful, None if failed
        """
        try:
            # Find available port
            local_port = self._find_available_port()
            if not local_port:
                logger.error(f"No available ports for session {session_id}")
                return None
            
            # Build SSH command for reverse tunnel
            ssh_command = [
                'ssh', '-N', '-R', 
                f'{local_port}:localhost:{host_port}',
                f'{host_username}@{host_ip}',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'ServerAliveInterval=30',
                '-o', 'ServerAliveCountMax=3',
                '-o', 'ExitOnForwardFailure=yes'
            ]
            
            # Add private key if provided
            if private_key_path:
                ssh_command.extend(['-i', private_key_path])
            
            # Start the tunnel process
            process = subprocess.Popen(
                ssh_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            # Give it a moment to establish
            time.sleep(3)
            
            # Check if process is still running (tunnel established)
            if process.poll() is None:
                self.active_tunnels[session_id] = process
                self.tunnel_ports[session_id] = local_port
                
                connection_string = f"ssh {host_username}@localhost -p {local_port}"
                
                logger.info(f"Tunnel created for session {session_id} on port {local_port}")
                return local_port, connection_string
            else:
                stderr = process.stderr.read().decode()
                logger.error(f"Tunnel failed for session {session_id}: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating tunnel for session {session_id}: {str(e)}")
            return None
    
    def close_tunnel(self, session_id: str) -> bool:
        """Close a tunnel for a session"""
        try:
            if session_id in self.active_tunnels:
                process = self.active_tunnels[session_id]
                process.terminate()
                
                # Wait for process to terminate
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                
                del self.active_tunnels[session_id]
                if session_id in self.tunnel_ports:
                    del self.tunnel_ports[session_id]
                
                logger.info(f"Tunnel closed for session {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error closing tunnel for session {session_id}: {str(e)}")
        return False
    
    def get_tunnel_port(self, session_id: str) -> Optional[int]:
        """Get the local port for a session's tunnel"""
        return self.tunnel_ports.get(session_id)
    
    def is_tunnel_active(self, session_id: str) -> bool:
        """Check if tunnel is active for a session"""
        if session_id not in self.active_tunnels:
            return False
        
        process = self.active_tunnels[session_id]
        return process.poll() is None
    
    def get_tunnel_status(self, session_id: str) -> Dict:
        """Get detailed tunnel status"""
        if session_id not in self.active_tunnels:
            return {
                'active': False,
                'port': None,
                'process_id': None
            }
        
        process = self.active_tunnels[session_id]
        return {
            'active': process.poll() is None,
            'port': self.tunnel_ports.get(session_id),
            'process_id': process.pid,
            'return_code': process.returncode
        }
    
    def _find_available_port(self) -> Optional[int]:
        """Find an available port starting from base_port"""
        for port in range(self.base_port, self.base_port + self.max_ports):
            if self._is_port_available(port) and port not in self.tunnel_ports.values():
                return port
        return None
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def cleanup_dead_tunnels(self):
        """Clean up any dead tunnel processes"""
        dead_sessions = []
        for session_id, process in self.active_tunnels.items():
            if process.poll() is not None:
                dead_sessions.append(session_id)
        
        for session_id in dead_sessions:
            logger.warning(f"Cleaning up dead tunnel for session {session_id}")
            self.close_tunnel(session_id)
        
        return len(dead_sessions)
    
    def get_all_tunnel_status(self) -> Dict:
        """Get status of all tunnels"""
        return {
            session_id: self.get_tunnel_status(session_id)
            for session_id in self.active_tunnels.keys()
        }
    
    def restart_tunnel(self, session_id: str) -> bool:
        """Restart a tunnel for a session"""
        try:
            # Get session details
            session = Session.objects.get(id=session_id)
            
            # Close existing tunnel
            self.close_tunnel(session_id)
            
            # Create new tunnel
            result = self.create_tunnel(
                session_id=session_id,
                host_ip=session.ssh_host,
                host_port=session.ssh_port or 22,
                host_username=session.ssh_username or 'ubuntu'
            )
            
            if result:
                local_port, connection_string = result
                # Update session with new connection details
                session.ssh_port = local_port
                session.connection_status = 'CONNECTED'
                session.connection_error = None
                session.last_connected = timezone.now()
                session.save()
                
                logger.info(f"Tunnel restarted for session {session_id}")
                return True
            else:
                session.connection_status = 'ERROR'
                session.connection_error = 'Failed to restart tunnel'
                session.save()
                return False
                
        except Session.DoesNotExist:
            logger.error(f"Session {session_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error restarting tunnel for session {session_id}: {str(e)}")
            return False


# Global tunnel manager instance
tunnel_manager = SSHTunnelManager()


class DockerContainerManager:
    """
    Manages Docker containers for GPU access
    """
    
    def __init__(self):
        self.active_containers: Dict[str, str] = {}  # session_id -> container_id
    
    def create_gpu_container(self, session_id: str, gpu_id: str, image: str = "nvidia/cuda:11.8-devel-ubuntu20.04") -> Optional[str]:
        """
        Create a Docker container with GPU access
        
        Args:
            session_id: Session UUID
            gpu_id: GPU device ID
            image: Docker image to use
            
        Returns:
            Container ID if successful, None if failed
        """
        try:
            # Docker command to create container with GPU access
            docker_command = [
                'docker', 'run', '-d',
                '--gpus', f'device={gpu_id}',
                '--name', f'session-{session_id[:8]}',
                '--restart', 'unless-stopped',
                '-p', '22',  # Expose SSH port
                image
            ]
            
            result = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            container_id = result.stdout.strip()
            self.active_containers[session_id] = container_id
            
            logger.info(f"Container created for session {session_id}: {container_id[:12]}")
            return container_id
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create container for session {session_id}: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error creating container for session {session_id}: {str(e)}")
            return None
    
    def stop_container(self, session_id: str) -> bool:
        """Stop and remove container for session"""
        try:
            if session_id not in self.active_containers:
                return True
            
            container_id = self.active_containers[session_id]
            
            # Stop container
            subprocess.run(['docker', 'stop', container_id], check=True)
            
            # Remove container
            subprocess.run(['docker', 'rm', container_id], check=True)
            
            del self.active_containers[session_id]
            
            logger.info(f"Container stopped for session {session_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop container for session {session_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error stopping container for session {session_id}: {str(e)}")
            return False
    
    def get_container_status(self, session_id: str) -> Dict:
        """Get container status"""
        if session_id not in self.active_containers:
            return {'exists': False}
        
        try:
            container_id = self.active_containers[session_id]
            result = subprocess.run(
                ['docker', 'inspect', container_id, '--format', '{{.State.Status}}'],
                capture_output=True,
                text=True,
                check=True
            )
            
            status = result.stdout.strip()
            return {
                'exists': True,
                'container_id': container_id,
                'status': status,
                'running': status == 'running'
            }
            
        except subprocess.CalledProcessError:
            # Container doesn't exist
            del self.active_containers[session_id]
            return {'exists': False}


# Global container manager instance
container_manager = DockerContainerManager()
