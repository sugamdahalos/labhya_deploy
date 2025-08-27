# Labhya GPU Agent Setup Guide

## Quick Setup

### 1. Create Host Account
1. Go to http://localhost:3001/register (or your frontend URL)
2. Create a **Host** account (not renter)
3. Remember your email and password

### 2. Configure Agent
1. Copy `.env.example` to `.env`
2. Update `LABHYA_AGENT_EMAIL` and `LABHYA_AGENT_PASSWORD` with your host credentials
3. Ensure `LABHYA_API_URL` points to your backend (default: http://localhost:8000)

### 3. Run Agent
```bash
# Windows
start_agent.bat

# Or directly with Python
python start_agent.py
```

## Troubleshooting

### Authentication Error 404
- Make sure the backend server is running at http://localhost:8000
- Check that you created a **Host** account (not renter)
- Verify the email/password in `.env` file

### No GPUs Detected
- Make sure NVIDIA drivers are installed
- Run `nvidia-smi` to verify GPU detection
- Check that Docker is installed for container management

### Connection Issues
- Ensure ports 22000-65000 are available for SSH tunnels
- Check firewall settings
- Verify backend server is accessible

## Features
- Automatic GPU detection using nvidia-smi
- Docker container management for sessions
- SSH reverse tunneling for remote access
- Real-time GPU metrics reporting
- Session status updates to backend
