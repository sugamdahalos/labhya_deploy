Dev image notes:

- The agent expects to be able to run `docker run --gpus all ...` when starting containers. On non-GPU machines this will still create containers but without GPU devices unless you use an NVIDIA-enabled host and the NVIDIA Container Toolkit.
- To override the image used by the agent, set the AGENT_GPU_IMAGE environment variable before starting the agent, for example:

```powershell
$env:AGENT_GPU_IMAGE = 'labhya/ssh-gpu:dev'
python backend/agent/combined_agent.py --email you@example.com --password secret
```

- For CI or remote testing, build and push the image to a registry and set AGENT_GPU_IMAGE to the registry-tagged image.
