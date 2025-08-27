#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'labhya_compute.settings')
django.setup()

from api.models import GPU, Host

print("=== HOST DATA ===")
hosts = Host.objects.all()
for host in hosts:
    print(f"Host: {host.user.email} (ID: {host.id})")

print("\n=== GPU DATA ===")
gpus = GPU.objects.all()
for gpu in gpus:
    print(f"GPU: {gpu.gpu_name}")
    print(f"Available: {gpu.gpu_availability}")
    print(f"Price: ${gpu.gpu_price}")
    print(f"Host: {gpu.host.user.email}")
    print(f"Host ID: {gpu.host.id}")
    print("---")

print(f"\n=== AVAILABLE GPUS (gpu_availability=True) ===")
available_gpus = GPU.objects.filter(gpu_availability=True)
print(f"Count: {available_gpus.count()}")
for gpu in available_gpus:
    print(f"- {gpu.gpu_name} (${gpu.gpu_price}/hr) - Host: {gpu.host.user.email}")
