Developer images directory

This folder contains small helper images used for local development and testing. Currently included:

- `ssh-gpu` - minimal Ubuntu image with sshd and a default `ubuntu` user. Build with:

```
docker build -t labhya/ssh-gpu:dev ./dev-images/ssh-gpu
```

Additions

- When running agents locally for integration testing, prefer setting `AGENT_GPU_IMAGE=labhya/ssh-gpu:dev` so the agent can create SSH-ready containers without needing a custom upstream image.
