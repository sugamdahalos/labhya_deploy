This small development Docker image provides an SSH-ready Ubuntu container suitable for local agent testing.

Usage

Build locally:

```
# From repository root
docker build -t labhya/ssh-gpu:dev ./dev-images/ssh-gpu
```

Run a container for quick manual testing:

```
docker run --rm -d --name labhya-test -p 2222:22 labhya/ssh-gpu:dev
# Connect: ssh ubuntu@localhost -p 2222 (password: ubuntu)
```

Notes

- The image uses `ubuntu:22.04` as base and enables password auth in sshd. The agent will normally set a random password inside the container after creation.
- For GPU passthrough testing, replace the base image with an appropriate NVIDIA/CUDA image and run the agent host with Docker + NVIDIA runtime available.
