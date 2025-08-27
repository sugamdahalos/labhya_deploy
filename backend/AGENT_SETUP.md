# Labhya Compute - Host Agent Configuration Guide

## Prerequisites

1. **Windows 10/11** with WSL2 enabled
2. **Ubuntu 22.04** installed in WSL2
3. **Docker Desktop** with WSL2 integration enabled
4. **NVIDIA GPU** with drivers installed
5. **SSH access** to your EC2 server

## Setup Instructions

### 1. Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required: API Configuration
LABHYA_API_URL=http://your-ec2-server.com:8000/api
LABHYA_USER=your-host-email@example.com
LABHYA_PASS=your-password

# Required: SSH Tunnel Configuration
LABHYA_TUNNEL_HOST=your-ec2-server.com
LABHYA_TUNNEL_USER=ubuntu
LABHYA_SSH_KEY=C:\Users\YourName\.ssh\id_rsa

# Optional: Advanced Configuration
LABHYA_TUNNEL_BASE_PORT=2200
```

### 2. SSH Key Setup

Generate SSH key pair and add to your EC2 server:

```bash
# On Windows (PowerShell or Git Bash)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Copy public key to EC2 server
ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@your-ec2-server.com
```

### 3. WSL2 Setup

Ensure WSL2 has NVIDIA drivers and Docker access:

```bash
# In WSL2 Ubuntu
# Install NVIDIA drivers for WSL2
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda-repo-wsl-ubuntu-12-2-local_12.2.0-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-2-local_12.2.0-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-2-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda

# Test GPU access
nvidia-smi
```

### 4. Docker Configuration

Ensure Docker Desktop has WSL2 integration enabled:
- Open Docker Desktop
- Go to Settings → Resources → WSL Integration
- Enable integration with Ubuntu-22.04

Test Docker with GPU:
```bash
# In WSL2
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

### 5. Running the Agent

#### GUI Mode (Recommended for setup):
```bash
python agent_app.py
```

#### Headless Mode (For production):
```bash
python agent_app.py --headless
```

## Agent Workflow

1. **Login**: Agent authenticates with your Django backend
2. **GPU Registration**: Detects and registers your GPU
3. **Session Monitoring**: Polls for new rental sessions
4. **Container Management**: Creates Docker containers with GPU access
5. **Tunnel Creation**: Establishes reverse SSH tunnels to your server
6. **Resource Cleanup**: Automatically cleans up when sessions end

## Local dev image (optional)

For local testing it's convenient to use a small SSH-ready container image included in the repository under `dev-images/ssh-gpu`.

Build it from the repo root:

```
docker build -t labhya/ssh-gpu:dev ./dev-images/ssh-gpu
```

Then either set the environment variable `AGENT_GPU_IMAGE=labhya/ssh-gpu:dev` before starting the agent, or edit your launch script. This image enables the agent to create an SSH-ready container without requiring a custom upstream image.


## Troubleshooting

### Common Issues:

1. **GPU not detected**:
   - Ensure NVIDIA drivers are installed in WSL2
   - Run `nvidia-smi` in WSL2 to test

2. **Docker issues**:
   - Ensure Docker Desktop is running
   - Enable WSL2 integration in Docker Desktop settings
   - Test with: `docker run hello-world`

3. **SSH tunnel failures**:
   - Check SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
   - Test SSH connection: `ssh ubuntu@your-ec2-server.com`
   - Ensure port 2200-3200 range is open on EC2

4. **Container creation fails**:
   - Check Docker daemon is running in WSL2
   - Ensure sufficient disk space
   - Check Docker logs: `docker logs container-name`

### Log Files:

- Agent logs are displayed in the GUI
- Docker container logs: `docker logs labhya-session-XXXXXXXX`
- SSH tunnel status can be checked in the agent GUI

## Security Notes

1. **SSH Keys**: Keep your private keys secure and use strong passphrases
2. **Firewall**: Ensure only necessary ports are open on your EC2 server
3. **Container Security**: Containers run with limited privileges
4. **Network**: All connections are encrypted via SSH tunnels

## Performance Tips

1. **GPU Memory**: Monitor GPU memory usage to avoid OOM errors
2. **Container Resources**: Limit container resources if needed
3. **Network**: Use SSD storage for better container performance
4. **Monitoring**: Check agent logs regularly for any issues

## Support

For issues or questions:
1. Check the agent logs first
2. Ensure all prerequisites are met
3. Test individual components (Docker, SSH, GPU) separately
4. Contact support with specific error messages
