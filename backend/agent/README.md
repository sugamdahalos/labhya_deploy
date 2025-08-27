# Labhya GPU Agent

The Labhya GPU Agent is a unified application that provides GPU rental services by managing Docker containers and SSH tunnels. It combines both GUI and headless operation modes.

## Features

- **GPU Container Management**: Creates GPU-enabled Docker containers for renters
- **SSH Tunnel Management**: Establishes reverse SSH tunnels for secure access
- **Real-time Monitoring**: Tracks GPU usage and container metrics
- **Dual Mode Operation**: GUI launcher and headless command-line modes
- **System Requirements Check**: Validates WSL2, Ubuntu, Docker installation
- **Automatic Authentication**: JWT token management with refresh

## System Requirements

### Windows Host
- Windows 10/11 with WSL2 enabled
- Ubuntu 22.04 LTS installed in WSL2
- Docker Desktop with WSL2 backend
- NVIDIA GPU with compatible drivers
- Python 3.8+

### Network
- Internet connection for backend API communication
- SSH access to tunnel server (for production)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd backend/agent
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the agent**:
   ```bash
   copy config.env.template .env
   # Edit .env with your settings
   ```

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

- `LABHYA_API_URL`: Backend server URL (default: http://localhost:8000)
- `LABHYA_AGENT_EMAIL`: Agent account email
- `LABHYA_AGENT_PASSWORD`: Agent account password
- `TUNNEL_SERVER_HOST`: SSH tunnel server hostname
- `TUNNEL_USER`: SSH tunnel username

### Agent Account Setup

1. Create an agent account in the backend admin panel
2. Note the email and password for configuration
3. Ensure the account has appropriate permissions

## Usage

### Quick Start Options

#### **Option 1: Python Startup Script (Recommended)**
```bash
python start_agent.py
```
This provides an interactive setup with dependency installation and mode selection.

#### **Option 2: Direct Agent Execution**

**GUI Mode:**
```bash
python launcher.py
```

**Headless Mode:**
```bash
python combined_agent.py --email agent@example.com --password yourpassword
```

**System Check:**
```bash
python combined_agent.py --check
```

#### **Option 3: Windows Batch File**
Double-click `start_agent.bat` in Windows Explorer, or run:
```cmd
start_agent.bat
```
**Note:** Do NOT run `python start_agent.bat` - batch files should not be executed with Python!

### Detailed Usage Instructions

### GUI Mode (Recommended for Desktop)

1. **Start the launcher**:
   ```bash
   python launcher.py
   ```
   Or double-click `start_agent.bat`

2. **Configure settings** in the GUI:
   - Server URL
   - Email/Password
   - System requirements check

3. **Start the agent** using the GUI button

### Headless Mode (For Servers)

1. **Check system requirements**:
   ```bash
   python combined_agent.py --check
   ```

2. **Start the agent**:
   ```bash
   python combined_agent.py --email agent@example.com --password yourpassword
   ```

3. **Or use environment variables**:
   ```bash
   set LABHYA_AGENT_EMAIL=agent@example.com
   set LABHYA_AGENT_PASSWORD=yourpassword
   python combined_agent.py
   ```

### Windows Batch Script

Use the provided batch script for easy startup:
```bash
start_agent.bat
```

## Architecture

### Core Components

- **AgentCore**: Main agent functionality
- **HTTPClient**: API communication with token refresh
- **GPUMonitor**: NVIDIA GPU monitoring
- **SystemChecker**: System requirements validation
- **GUI Launcher**: Optional GUI interface

### Workflow

1. **Startup**: System check → Authentication → Host registration
2. **Session Polling**: Continuously polls for new session requests
3. **Container Creation**: Creates GPU-enabled Docker containers
4. **Tunnel Setup**: Establishes reverse SSH tunnels
5. **Monitoring**: Reports real-time metrics to backend
6. **Cleanup**: Proper shutdown of containers and tunnels

## Docker Container

The agent creates containers with:
- NVIDIA GPU access (`--gpus all`)
- SSH server for remote access
- Ubuntu 22.04 base with CUDA support
- Resource limits (memory, CPU)
- Automatic cleanup on session end

## SSH Tunnels

Reverse SSH tunnels provide:
- Secure access through firewall/NAT
- Dynamic port allocation
- Automatic reconnection
- Session isolation

## Monitoring

The agent reports:
- GPU utilization and memory usage
- Container CPU/memory usage
- Network and disk I/O
- Session connection status

## Troubleshooting

### Common Issues

1. **WSL2 not enabled**:
   ```bash
   dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```

2. **Docker not running**:
   - Start Docker Desktop
   - Enable WSL2 integration

3. **GPU not detected**:
   - Install NVIDIA drivers
   - Install NVIDIA Container Toolkit

4. **Authentication failed**:
   - Check email/password
   - Verify backend is running
   - Check network connectivity

### Logs

Check the log file for detailed information:
- GUI mode: Logs displayed in the interface
- Headless mode: `labhya_agent.log` file

## Development

### File Structure
```
agent/
├── combined_agent.py    # Main agent implementation
├── launcher.py          # GUI launcher
├── requirements.txt     # Python dependencies
├── start_agent.bat     # Windows startup script
├── config.env.template # Configuration template
└── README.md           # This file
```

### API Endpoints Used
- `POST /api/token/` - Authentication
- `POST /api/token/refresh/` - Token refresh
- `POST /api/hosts/register/` - Host registration
- `GET /api/sessions/pending/{host_id}/` - Session polling
- `PUT /api/sessions/{session_id}/status/` - Status updates
- `POST /api/sessions/{session_id}/metrics/` - Metrics reporting

## Security

- JWT token authentication
- Secure SSH tunnels
- Container isolation
- Resource limits
- Automatic cleanup

## License

This project is part of the Labhya GPU Rental Platform for CSIT 7th semester, Tribhuvan University.
