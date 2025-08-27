from django.core.management.base import BaseCommand
from api.models import HostKey
import subprocess, logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Deploy approved HostKey public keys to local tunnel host"

    def handle(self, *args, **options):
        qs = HostKey.objects.filter(status='APPROVED', deployment_status__isnull=True)
        for hk in qs:
            pubkey = hk.public_key.strip()
            # allow host model to carry port config if present
            base_port = getattr(hk.host, 'ssh_tunnel_base_port', 22000)
            port_count = getattr(hk.host, 'ssh_tunnel_port_count', 1000)
            # Prefer to run the deploy script via sudo (labhya user has NOPASSWD sudoers entry).
            # This avoids permission denied issues when the script is owned by root.
            # use absolute path to sudo to avoid PATH differences under systemd
            cmd = [
                '/usr/bin/sudo', '/opt/labhya/deploy_tunnel_host.sh',
                pubkey, str(base_port), str(port_count)
            ]
            try:
                logger.info("Deploying key for host %s", hk.host.id)
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                hk.deployment_status = 'DEPLOYED'
                hk.deployment_log = out
                hk.save()
            except subprocess.CalledProcessError as e:
                logger.error("Failed to deploy key %s: %s", hk.id, e.output)
                hk.deployment_status = 'FAILED'
                hk.deployment_log = e.output
                hk.save()
