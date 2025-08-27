#!/usr/bin/env python3
"""
Combined Labhya GPU Agent
Unified agent that combines GUI launcher and core agent functionality
"""

import os
import sys
import time
import json
import logging
import threading
import subprocess
import platform
import socket
import signal
from typing import Dict, List, Optional, Any
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
BASE_URL = os.getenv('LABHYA_API_URL', 'http://localhost:8000')
AGENT_EMAIL = os.getenv('LABHYA_AGENT_EMAIL', '')
AGENT_PASSWORD = os.getenv('LABHYA_AGENT_PASSWORD', '')
# Tunnel server: prefer explicit env var; if unset or left as placeholder,
# derive hostname from BASE_URL so local testing works (e.g. http://localhost:8000)
_env_tunnel_host = os.getenv('TUNNEL_SERVER_HOST', '')
if not _env_tunnel_host or _env_tunnel_host.strip() == 'your-server.com':
    # parse host from BASE_URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(BASE_URL)
        TUNNEL_SERVER_HOST = parsed.hostname or 'localhost'
    except Exception:
        TUNNEL_SERVER_HOST = 'localhost'
else:
    TUNNEL_SERVER_HOST = _env_tunnel_host

TUNNEL_USER = os.getenv('TUNNEL_USER', 'tunnel-user')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('labhya_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client with token refresh capability"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate with the API"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login/",
                json={'email': email, 'password': password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access']
                self.refresh_token = data['refresh']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token"""
        if not self.refresh_token:
            return False
            
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/refresh/",
                json={'refresh': self.refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                logger.info("Token refreshed successfully")
                return True
            else:
                logger.error(f"Token refresh failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a request with automatic token refresh"""
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code == 401:
            logger.info("Token expired, attempting refresh...")
            if self.refresh_access_token():
                response = self.session.request(method, url, **kwargs)
        
        return response
    
    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        return self.request('DELETE', url, **kwargs)


class GPUMonitor:
    """GPU monitoring functionality"""
    
    @staticmethod
    def get_gpu_info() -> List[Dict]:
        """Get GPU information using nvidia-smi"""
        try:
            cmd = [
                'nvidia-smi', 
                '--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu',
                '--format=csv,noheader,nounits'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"nvidia-smi error: {result.stderr}")
                return []
            
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 7:
                        gpus.append({
                            'index': int(parts[0]),
                            'name': parts[1],
                            'memory_total': int(parts[2]),
                            'memory_used': int(parts[3]),
                            'memory_free': int(parts[4]),
                            'utilization': int(parts[5]),
                            'temperature': int(parts[6])
                        })
            
            return gpus
            
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
            return []


class SystemChecker:
    """System requirements checker for WSL2, Ubuntu, Docker, etc."""
    
    @staticmethod
    def _wsl_cmd() -> str:
        """Get WSL command path"""
        system_root = os.environ.get('SystemRoot', r'C:\Windows')
        candidates = [
            os.path.join(system_root, 'Sysnative', 'wsl.exe'),
            os.path.join(system_root, 'System32', 'wsl.exe'),
            'wsl',
        ]
        
        for c in candidates:
            try:
                if c == 'wsl':
                    return c
                if os.path.exists(c):
                    return c
            except Exception:
                continue
        
        return 'wsl'
    
    @staticmethod
    def check_wsl_enabled() -> bool:
        """Check if WSL is enabled"""
        try:
            r = subprocess.run([SystemChecker._wsl_cmd(), "--status"], 
                             capture_output=True, text=True)
            return r.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def check_ubuntu_installed() -> bool:
        """Check if Ubuntu is installed in WSL"""
        try:
            # Try direct Ubuntu-22.04 test
            r = subprocess.run([SystemChecker._wsl_cmd(), "-d", "Ubuntu-22.04", "--", "true"], 
                              capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return True
            
            # Try listing distributions
            r = subprocess.run([SystemChecker._wsl_cmd(), "-l", "-q"], 
                              capture_output=True, text=True, encoding='utf-16')
            if r.returncode == 0 and r.stdout.strip():
                lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
                return any(ln.lower().startswith("ubuntu") for ln in lines)
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def check_docker_installed() -> bool:
        """Check if Docker is installed"""
        try:
            r = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            return r.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def check_docker_running() -> bool:
        """Check if Docker is running"""
        try:
            r = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            return r.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def check_system_requirements() -> dict:
        """Check all system requirements and return status"""
        if platform.system() != 'Windows':
            return {
                'wsl_ok': False, 'ubuntu_ok': False, 'docker_installed': False,
                'docker_running': False, 'all_ok': False, 
                'message': 'Windows required for this agent'
            }
        
        wsl_ok = SystemChecker.check_wsl_enabled()
        ubuntu_ok = SystemChecker.check_ubuntu_installed()
        docker_installed = SystemChecker.check_docker_installed()
        docker_running = SystemChecker.check_docker_running() if docker_installed else False
        
        all_ok = all([wsl_ok, ubuntu_ok, docker_installed, docker_running])
        
        missing = []
        if not wsl_ok: missing.append('WSL2')
        if not ubuntu_ok: missing.append('Ubuntu')
        if not docker_installed: missing.append('Docker Desktop')
        elif not docker_running: missing.append('Docker (start it)')
        
        message = "All requirements met" if all_ok else f"Missing: {', '.join(missing)}"
        
        return {
            'wsl_ok': wsl_ok, 'ubuntu_ok': ubuntu_ok, 'docker_installed': docker_installed,
            'docker_running': docker_running, 'all_ok': all_ok, 'message': message
        }


class AgentCore:
    """Core agent functionality"""
    
    def __init__(self, base_url: str, use_signal_handlers: bool = True):
        self.base_url = base_url
        self.http_client = HTTPClient(base_url)
        self.running = False
        self.host_id = None
        self.poll_thread = None
        self.active_containers = {}
        self.active_tunnels = {}
        self.metrics_threads = {}
        
        # Setup signal handlers only if requested (not in GUI mode)
        if use_signal_handlers:
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
            except ValueError as e:
                logger.warning(f"Could not set signal handlers: {e}")
                # This is expected when running in non-main thread
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate with the backend"""
        return self.http_client.authenticate(email, password)
    
    def register_host(self) -> bool:
        """Register this host with the backend or update existing host"""
        try:
            # First, check if host already exists
            try:
                response = self.http_client.get(f"{self.base_url}/api/hosts/current/")
                if response.status_code == 200:
                    # Host exists, get the host ID and update GPU info
                    data = response.json()
                    self.host_id = data['id']
                    logger.info(f"Host already registered with ID: {self.host_id}")
                    
                    # Now register/update GPUs for this host
                    return self.register_gpus()
            except Exception:
                # Host doesn't exist, continue with registration
                pass
            
            # Get system information
            gpu_info = GPUMonitor.get_gpu_info()
            
            if not gpu_info:
                logger.error("No GPUs detected. This agent requires NVIDIA GPUs.")
                return False

            host_data = {
                'platform': platform.system(),
                'architecture': platform.machine(),
                'gpu_count': len(gpu_info),
                'gpu_details': gpu_info,
                'status': 'online'
            }

            response = self.http_client.post(
                f"{self.base_url}/api/hosts/register/",
                json=host_data
            )

            if response.status_code == 201:
                data = response.json()
                self.host_id = data['id']
                logger.info(f"Host registered successfully with ID: {self.host_id}")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # Host exists but we failed to get it above, try again
                response = self.http_client.get(f"{self.base_url}/api/hosts/current/")
                if response.status_code == 200:
                    data = response.json()
                    self.host_id = data['id']
                    logger.info(f"Retrieved existing host ID: {self.host_id}")
                    return self.register_gpus()
                else:
                    logger.error("Host exists but cannot retrieve host information")
                    return False
            else:
                logger.error(f"Host registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering host: {e}")
            return False
    
    def register_gpus(self) -> bool:
        """Register GPUs for the current host"""
        try:
            if not self.host_id:
                logger.error("Cannot register GPUs: Host ID not set")
                return False
                
            gpu_info = GPUMonitor.get_gpu_info()
            
            if not gpu_info:
                logger.error("No GPUs detected")
                return False
            
            logger.info(f"Detected {len(gpu_info)} GPUs: {[gpu.get('name', 'Unknown') for gpu in gpu_info]}")
            
            # Check existing GPUs first
            try:
                existing_response = self.http_client.get(f"{self.base_url}/api/gpus/?host={self.host_id}")
                existing_gpus = []
                if existing_response.status_code == 200:
                    response_data = existing_response.json()
                    # Handle both list and paginated response formats
                    if isinstance(response_data, list):
                        existing_gpus = response_data
                    elif isinstance(response_data, dict) and 'results' in response_data:
                        existing_gpus = response_data['results']
                    elif isinstance(response_data, dict):
                        # Handle single object response
                        existing_gpus = [response_data]
                    else:
                        existing_gpus = []
                    logger.info(f"Found {len(existing_gpus)} existing GPUs for this host")
                else:
                    logger.warning(f"Could not retrieve existing GPUs: HTTP {existing_response.status_code}")
                    existing_gpus = []
            except Exception as e:
                logger.warning(f"Could not check existing GPUs: {e}")
                existing_gpus = []
            
            # Register each GPU
            success_count = 0
            skipped_count = 0
            for gpu_data in gpu_info:
                gpu_name = gpu_data.get('name', 'Unknown GPU')
                gpu_location = f"GPU {gpu_data.get('index', 0)}"
                
                # Check if GPU already exists
                gpu_exists = False
                for existing_gpu in existing_gpus:
                    if isinstance(existing_gpu, dict):
                        existing_name = existing_gpu.get('gpu_name', '')
                        existing_location = existing_gpu.get('gpu_location', '')
                        if existing_name == gpu_name and existing_location == gpu_location:
                            gpu_exists = True
                            break
                
                if gpu_exists:
                    logger.info(f"GPU {gpu_name} at {gpu_location} already exists, skipping")
                    skipped_count += 1
                    continue
                
                # Convert memory from bytes to GB and ensure it's an integer
                memory_gb = int(gpu_data.get('memory_total', 0) / (1024**3)) if gpu_data.get('memory_total') else 0
                
                gpu_payload = {
                    'host': self.host_id,
                    'gpu_name': gpu_name,
                    'gpu_model': gpu_name,
                    'gpu_memory': memory_gb,
                    'gpu_price': 1.0,  # Default price per hour
                    'gpu_availability': True,
                    'gpu_location': gpu_location
                }
                
                response = self.http_client.post(
                    f"{self.base_url}/api/gpus/",
                    json=gpu_payload
                )
                
                if response.status_code in [200, 201]:
                    success_count += 1
                    logger.info(f"GPU {gpu_name} registered successfully")
                else:
                    logger.warning(f"Failed to register GPU {gpu_name}: {response.status_code} - {response.text}")
            
            total_gpus = success_count + skipped_count
            if total_gpus > 0:
                logger.info(f"GPU registration complete: {success_count} new, {skipped_count} existing, {len(gpu_info)} total detected")
                return True
            else:
                logger.error("Failed to register any GPUs")
                return False
                
        except Exception as e:
            logger.error(f"Error registering GPUs: {e}")
            return False

    def _ensure_ssh_key_and_register(self):
        """Ensure an SSH keypair exists and upload the public key to backend for operator approval"""
        try:
            ssh_dir = Path.home() / '.ssh'
            ssh_dir.mkdir(parents=True, exist_ok=True)
            key_path = ssh_dir / 'labhya_tunnel'
            pub_path = ssh_dir / 'labhya_tunnel.pub'

            # Generate key if missing
            if not key_path.exists() or not pub_path.exists():
                logger.info(f"Generating SSH keypair at {key_path}")
                subprocess.run(['ssh-keygen', '-t', 'ed25519', '-f', str(key_path), '-N', ''], check=True)

            # Read public key
            pubkey = pub_path.read_text().strip()

            # Upload to backend so operator can approve & deploy to EC2
            if self.host_id and pubkey:
                try:
                    resp = self.http_client.post(
                        f"{self.base_url}/api/hosts/{self.host_id}/upload_key/",
                        json={'public_key': pubkey}
                    )
                    if resp.status_code in (200, 201):
                        logger.info("Uploaded agent public key to backend for approval")
                    else:
                        logger.warning(f"Failed to upload public key: {resp.status_code} - {resp.text}")
                except Exception as e:
                    logger.warning(f"Error uploading public key to backend: {e}")

        except Exception as e:
            logger.warning(f"SSH key generation/registration failed: {e}")
    
    def get_host_info(self) -> dict:
        """Get current host information"""
        try:
            response = self.http_client.get(f"{self.base_url}/api/hosts/current/")
            
            if response.status_code == 200:
                data = response.json()
                self.host_id = data['id']
                return data
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Failed to get host info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting host info: {e}")
            return None
    
    def start(self, skip_auth: bool = False) -> bool:
        """Start the agent"""
        logger.info("Starting Labhya GPU Agent...")
        
        # Check system requirements
        requirements = SystemChecker.check_system_requirements()
        if not requirements['all_ok']:
            logger.error(f"System requirements not met: {requirements['message']}")
            return False
        
        # Authenticate only if not already authenticated
        if not skip_auth and not self.http_client.access_token:
            if not self.authenticate(AGENT_EMAIL, AGENT_PASSWORD):
                logger.error("Authentication failed")
                return False

        # Register host
        if not self.register_host():
            logger.error("Host registration failed")
            return False

        # Ensure SSH key exists for tunneling and register public key with backend
        try:
            self._ensure_ssh_key_and_register()
        except Exception as e:
            logger.warning(f"Could not generate/register SSH key: {e}")
        
        # Start polling for sessions
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_sessions)
        self.poll_thread.daemon = True
        self.poll_thread.start()
        
        logger.info("Agent started successfully")
        return True
    
    def stop(self):
        """Stop the agent"""
        logger.info("Stopping agent...")
        self.running = False
        
        # Stop all active sessions
        self.stop_all_sessions()
        
        # Wait for polling thread to finish
        if self.poll_thread and self.poll_thread.is_alive():
            self.poll_thread.join(timeout=5)
        
        logger.info("Agent stopped")
    
    def _poll_sessions(self):
        """Poll for new sessions to start"""
        while self.running:
            try:
                response = self.http_client.get(
                    f"{self.base_url}/api/hosts/{self.host_id}/sessions/"
                )
                
                if response.status_code == 200:
                    sessions = response.json()
                    
                    for session in sessions:
                        if session['status'] == 'PENDING':
                            self.start_session(session)
                
                elif response.status_code != 404:
                    logger.warning(f"Session polling failed: {response.status_code}")
                
            except Exception as e:
                logger.error(f"Error polling sessions: {e}")
            
            if self.running:
                time.sleep(5)
    
    def start_session(self, session_data: Dict):
        """Start a GPU session with Docker container and SSH tunnel"""
        session_id = session_data.get('id')
        try:
            if not session_id:
                raise ValueError('session id missing')
            logger.info(f"Starting session {session_id}")
            
            # Step 1: Create Docker container with GPU access
            container_info = self._create_gpu_container(session_id)
            if not container_info:
                self._update_session_status(session_id, 'FAILED', 'Failed to create Docker container')
                return
            
            # Step 2: Get container SSH port
            container_ssh_port = container_info.get('ssh_port', 22)
            
            # Step 3: Create reverse SSH tunnel
            tunnel_info = self._create_reverse_tunnel(session_id, container_ssh_port)
            if not tunnel_info or isinstance(tunnel_info, dict) and tunnel_info.get('error'):
                # Log the error and fallback to direct host-mapped port so renter can still connect
                err = None
                if isinstance(tunnel_info, dict):
                    err = tunnel_info.get('error')

                logger.warning(f"Tunnel creation failed for session {session_id}, falling back to direct container port. err={err}")

                # Update session with direct host connection details
                fallback_details = {
                    'ssh_host': None,  # let backend determine host or leave blank
                    'ssh_port': container_ssh_port,
                    'ssh_username': 'ubuntu',
                    'connection_status': 'CONNECTED',
                    'connection_error': err
                }

                if 'ssh_password' in container_info and container_info['ssh_password']:
                    fallback_details['ssh_password'] = container_info['ssh_password']

                # Use host IP so renter can connect; try to use explicit host from ENV or BASE_URL
                try:
                    # If server and agent are same machine in dev, setting ssh_host to host's IP may help
                    fallback_details['ssh_host'] = socket.gethostname()
                except Exception:
                    fallback_details['ssh_host'] = 'localhost'

                self._update_session_status(session_id, 'ACTIVE', None, fallback_details)
                # Start metrics reporting even on fallback
                self._start_metrics_thread(session_id)
                logger.info(f"Session {session_id} started in fallback mode (direct host port {container_ssh_port})")
                return
            
            # Step 4: Update session with connection details
            connection_details = {
                'ssh_host': 'localhost',  # Accessible via tunnel on server
                'ssh_port': tunnel_info['remote_port'],
                'ssh_username': 'ubuntu',
                'connection_status': 'CONNECTED'
            }

            # Include password if container provided it
            if 'ssh_password' in container_info and container_info['ssh_password']:
                connection_details['ssh_password'] = container_info['ssh_password']
            
            self._update_session_status(session_id, 'ACTIVE', None, connection_details)
            
            # Start metrics reporting
            self._start_metrics_thread(session_id)
            
            logger.info(f"Session {session_id} started successfully")
            logger.info(f"SSH Connection: ssh ubuntu@{TUNNEL_SERVER_HOST} -p {tunnel_info['remote_port']}")
            
        except Exception as e:
            logger.error(f"Failed to start session {session_id if session_id else '<unknown>'}: {e}")
            if session_id:
                self._update_session_status(session_id, 'FAILED', str(e))
    
    def _create_gpu_container(self, session_id: str) -> Optional[Dict]:
        """Create Docker container with GPU access and SSH server"""
        try:
            container_name = f"labhya-session-{session_id[:8]}"
            
            # Find available port for SSH (prefer random selection to avoid races)
            ssh_port = self._pick_random_available_port(2222, 2300)
            if not ssh_port:
                logger.error("No available ports for container SSH")
                return None
                
            # Docker run command with GPU support; retry on host port conflicts
            image = os.getenv('AGENT_GPU_IMAGE', 'labhya/ssh-gpu:dev')

            # If a previous container with this name exists (stale), remove it first
            try:
                existing = subprocess.run(['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.ID}}'], capture_output=True, text=True)
                if existing.returncode == 0 and existing.stdout.strip():
                    existing_id = existing.stdout.strip().splitlines()[0]
                    logger.info(f"Found existing container {existing_id} with name {container_name}, removing it")
                    subprocess.run(['docker', 'rm', '-f', existing_id], capture_output=True, text=True)
            except Exception as e:
                logger.warning(f"Could not check/remove existing container {container_name}: {e}")

            max_attempts = 6
            attempt = 0
            result = None

            while attempt < max_attempts:
                attempt += 1
                docker_cmd = [
                    'docker', 'run', '-d',
                    '--name', container_name,
                    '--gpus', 'all',
                    '-p', f'{ssh_port}:22',
                    '--memory', '4g',
                    '--cpus', '2',
                    '-e', 'NVIDIA_VISIBLE_DEVICES=all',
                    image
                ]

                result = subprocess.run(docker_cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    break

                stderr = (result.stderr or '').lower()
                # If port conflict, pick a new port and retry
                if 'port is already allocated' in stderr or 'bind for' in stderr or 'already in use' in stderr:
                    logger.warning(f"Port {ssh_port} already in use, trying a new port (attempt {attempt}/{max_attempts})")
                    new_port = self._pick_random_available_port(2222, 2300)
                    if not new_port or new_port == ssh_port:
                        logger.error("No alternate ports available after port conflict")
                        break
                    ssh_port = new_port
                    time.sleep(0.2)
                    continue

                # Other error: don't retry
                logger.error(f"Failed to create container: {result.stderr}")
                break

            if not result or result.returncode != 0:
                return None
            
            container_id = result.stdout.strip()
            
            # Wait for container to be ready
            time.sleep(3)
            
            # Verify container is running
            check_cmd = ['docker', 'inspect', '--format={{.State.Running}}', container_id]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.stdout.strip() != 'true':
                logger.error(f"Container failed to start properly")
                return None
            
            logger.info(f"Container {container_name} created successfully on port {ssh_port}")

            # Generate random password for ubuntu user and set it inside container
            # ensure password variable is always defined even if setting it fails
            password = None

            try:
                import secrets, string
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for _ in range(12))

                # Ensure ubuntu user exists and set password
                subprocess.run([
                    'docker', 'exec', container_id,
                    'bash', '-c', "useradd -m ubuntu || true && echo 'ubuntu:'\"" + password + "\" | chpasswd"
                ], check=False)

                # Start ssh service
                subprocess.run([
                    'docker', 'exec', container_id,
                    'bash', '-c', 'service ssh start || /usr/sbin/sshd || true'
                ], check=False)
            except Exception as e:
                logger.warning(f"Could not set password in container {container_name}: {e}")

            return {
                'container_id': container_id,
                'container_name': container_name,
                'ssh_port': ssh_port,
                'ssh_password': password
            }
            
        except Exception as e:
            logger.error(f"Error creating GPU container: {e}")
            return None
    
    def _stop_container(self, session_id: str):
        """Stop and remove Docker container"""
        try:
            container_name = f"labhya-session-{session_id[:8]}"
            
            # Stop container
            subprocess.run(['docker', 'stop', container_name], 
                         capture_output=True)
            
            # Remove container
            subprocess.run(['docker', 'rm', container_name], 
                         capture_output=True)
            
            logger.info(f"Container {container_name} stopped and removed")
            
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
    
    def _create_reverse_tunnel(self, session_id: str, local_port: int) -> Optional[Dict]:
        """Create reverse SSH tunnel to server"""
        try:
            # Find available remote port
            remote_port = self._find_available_remote_port()
            if not remote_port:
                logger.error("No available remote ports for tunnel")
                return None
            
            # Create SSH tunnel command
            # Request a public bind (0.0.0.0) for the remote forward and
            # use ExitOnForwardFailure so ssh exits immediately when the
            # server refuses the requested remote bind. Also request
            # GatewayPorts to hint the server to allow non-loopback binds.
            tunnel_cmd = [
                'ssh', '-N',
                '-R', f'0.0.0.0:{remote_port}:localhost:{local_port}',
                '-o', 'ExitOnForwardFailure=yes',
                '-o', 'GatewayPorts=yes',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ServerAliveInterval=30',
                '-o', 'ServerAliveCountMax=3',
                f'{TUNNEL_USER}@{TUNNEL_SERVER_HOST}'
            ]

            # Start tunnel process and stream its stdout/stderr into the agent log
            process = subprocess.Popen(
                tunnel_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Collect stderr/stdout lines for diagnostics
            stderr_lines = []
            stdout_lines = []

            def _stream_reader(stream, collector, prefix):
                try:
                    for line in iter(stream.readline, ''):
                        if not line:
                            break
                        collector.append(line)
                        logger.info(f"SSH tunnel [{session_id}] {prefix}: {line.strip()}")
                except Exception as e:
                    logger.debug(f"Error reading SSH {prefix}: {e}")

            # Start background readers
            threading.Thread(target=_stream_reader, args=(process.stderr, stderr_lines, 'ERR'), daemon=True).start()
            threading.Thread(target=_stream_reader, args=(process.stdout, stdout_lines, 'OUT'), daemon=True).start()
            
            # Store tunnel info
            tunnel_info = {
                'process': process,
                'remote_port': remote_port,
                'local_port': local_port,
                'session_id': session_id
            }
            
            self.active_tunnels[session_id] = tunnel_info
            
            # Give tunnel time to establish and fail fast if binding is disallowed
            timeout = 5
            waited = 0
            interval = 0.2
            while waited < timeout:
                if process.poll() is not None:
                    break
                time.sleep(interval)
                waited += interval

            # If process exited, capture stderr content for the error message
            if process.poll() is not None:
                joined_err = ''.join(stderr_lines) if stderr_lines else None
                logger.error(f"Tunnel process exited early (poll={process.poll()}), stderr: {joined_err}")
                # Return error information so caller can decide to fallback
                return {'error': joined_err}
            
            logger.info(f"Reverse tunnel created: {remote_port} -> localhost:{local_port}")
            
            return tunnel_info
            
        except Exception as e:
            logger.error(f"Error creating reverse tunnel: {e}")
            return None
    
    def _find_available_port(self, start_port: int, end_port: int) -> Optional[int]:
        """Find an available local port"""
        for port in range(start_port, end_port):
            try:
                # Bind to 0.0.0.0 to check availability on all interfaces
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        return None

    def _pick_random_available_port(self, start_port: int, end_port: int, attempts: int = 100) -> Optional[int]:
        """Pick a random available port in the given range by attempting to bind.

        This is more robust on platforms where sequential scanning may give
        false negatives due to transient bindings.
        """
        import random
        tried = set()
        for _ in range(attempts):
            port = random.randint(start_port, end_port - 1)
            if port in tried:
                continue
            tried.add(port)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        return None
    
    def _find_available_remote_port(self) -> Optional[int]:
        """Find an available remote port (using random selection from valid range)"""
        try:
            # Use a common port range for SSH tunnels (10000-65000)
            import random
            for _ in range(100):  # Try up to 100 times
                port = random.randint(10000, 65000)
                # Simple check - in a real scenario this would need server-side validation
                return port
            return 22000  # fallback port
                
        except Exception as e:
            logger.error(f"Error finding available remote port: {e}")
            return None
    
    def stop_session(self, session_id: str):
        """Stop a GPU session"""
        try:
            logger.info(f"Stopping session {session_id}")
            
            # Stop tunnel
            if session_id in self.active_tunnels:
                tunnel_info = self.active_tunnels[session_id]
                process = tunnel_info['process']
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                del self.active_tunnels[session_id]
                logger.info(f"Tunnel for session {session_id} stopped")
            
            # Stop container
            self._stop_container(session_id)
            
            # Update session status
            self._update_session_status(session_id, 'STOPPED')
            
            logger.info(f"Session {session_id} stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping session {session_id}: {e}")
    
    def _start_metrics_thread(self, session_id: str):
        """Start metrics monitoring thread for a session"""
        if session_id in self.metrics_threads:
            return  # Thread already running
            
        stop_event = threading.Event()
        
        def monitor_metrics():
            container_name = f"labhya-session-{session_id[:8]}"
            
            while not stop_event.is_set():
                try:
                    # Get GPU metrics
                    gpu_metrics = GPUMonitor.get_gpu_info()
                    
                    # Get container metrics
                    container_metrics = self._get_container_metrics(container_name)
                    
                    # Combine metrics
                    metrics = {
                        'gpu': gpu_metrics,
                        'container': container_metrics,
                        'timestamp': time.time()
                    }
                    
                    # Send to backend
                    self._send_metrics(session_id, metrics)
                    
                except Exception as e:
                    logger.error(f"Error in metrics monitoring: {e}")
                
                if stop_event.is_set():
                    break
                    
                stop_event.wait(30)
        
        thread = threading.Thread(target=monitor_metrics)
        thread.daemon = True
        thread.start()
        
        self.metrics_threads[session_id] = {
            'thread': thread,
            'stop_event': stop_event
        }
    
    def _get_container_metrics(self, container_name: str) -> Dict:
        """Get Docker container metrics"""
        try:
            # Get container stats
            stats_cmd = ['docker', 'stats', '--no-stream', '--format', 
                        'table {{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}', 
                        container_name]
            
            result = subprocess.run(stats_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {}
            
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return {}
            
            # Parse stats (skip header)
            stats_line = lines[1]
            parts = stats_line.split(',')
            
            if len(parts) >= 4:
                return {
                    'cpu_percent': parts[0].strip(),
                    'memory_usage': parts[1].strip(),
                    'network_io': parts[2].strip(),
                    'block_io': parts[3].strip()
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting container metrics: {e}")
            return {}
    
    def _send_metrics(self, session_id: str, metrics: Dict):
        """Send metrics to backend"""
        try:
            response = self.http_client.post(
                f"{self.base_url}/api/sessions/{session_id}/update_gpu_metrics/",
                json=metrics
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to send metrics: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending metrics: {e}")
    
    def _update_session_status(self, session_id: str, status: str, error_message: Optional[str] = None, connection_details: Optional[Dict] = None):
        """Update session status in backend"""
        try:
            data = {'status': status}
            
            if error_message:
                data['connection_error'] = error_message
            
            if connection_details:
                data.update(connection_details)
            
            # Patch the session resource so we can update the session.status as well
            # (update_connection_status only updates connection_status and doesn't
            # change the session.status, which caused retries). Use PATCH to /sessions/<id>/
            response = self.http_client.request(
                'PATCH',
                f"{self.base_url}/api/sessions/{session_id}/",
                json=data
            )

            if response.status_code in (200, 202):
                logger.info(f"Session {session_id} status updated to {status}")
            else:
                logger.error(f"Failed to update session status: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error updating session status: {e}")
    
    def stop_all_sessions(self):
        """Stop all active sessions"""
        logger.info("Stopping all active sessions...")
        
        # Stop all metrics threads
        for session_id, thread_info in self.metrics_threads.items():
            thread_info['stop_event'].set()
        
        # Stop all tunnels and containers
        for session_id in list(self.active_tunnels.keys()):
            self.stop_session(session_id)
        
        # Clear tracking
        self.metrics_threads.clear()
        self.active_tunnels.clear()
        
        logger.info("All sessions stopped")


def main():
    """Main entry point"""
    global AGENT_EMAIL, AGENT_PASSWORD, BASE_URL
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Labhya GPU Agent')
    parser.add_argument('--check', action='store_true', help='Check system requirements')
    parser.add_argument('--email', help='Agent email')
    parser.add_argument('--password', help='Agent password')
    parser.add_argument('--server', help='Server URL')
    
    args = parser.parse_args()
    
    if args.check:
        requirements = SystemChecker.check_system_requirements()
        print(f"System Requirements: {requirements['message']}")
        for key, value in requirements.items():
            if key != 'message':
                print(f"  {key}: {'✓' if value else '✗'}")
        return
    
    # Get configuration
    email = args.email or AGENT_EMAIL
    password = args.password or AGENT_PASSWORD
    server = args.server or BASE_URL
    
    if not email or not password:
        print("Error: Email and password required")
        print("Set LABHYA_AGENT_EMAIL and LABHYA_AGENT_PASSWORD environment variables")
        print("or use --email and --password arguments")
        return
    
    # Update global credentials
    AGENT_EMAIL = email
    AGENT_PASSWORD = password
    BASE_URL = server
    
    # Create and start agent
    agent = AgentCore(server)
    
    if agent.start():
        try:
            # Keep running until interrupted
            while agent.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            agent.stop()
    else:
        logger.error("Failed to start agent")


if __name__ == '__main__':
    main()
