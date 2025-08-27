from django.core.management.base import BaseCommand
from api.tunnel_manager import tunnel_manager, container_manager
from api.models import Session


class Command(BaseCommand):
    help = 'Manage SSH tunnels and Docker containers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['cleanup', 'status', 'restart_all', 'sync_sessions'],
            help='Action to perform',
            required=True
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'cleanup':
            self.stdout.write('Cleaning up dead tunnels...')
            cleaned_count = tunnel_manager.cleanup_dead_tunnels()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleaned up {cleaned_count} dead tunnels')
            )

        elif action == 'status':
            self.stdout.write('Getting tunnel status...')
            tunnel_status = tunnel_manager.get_all_tunnel_status()
            
            self.stdout.write(f"\nActive Tunnels: {len(tunnel_status)}")
            for session_id, status in tunnel_status.items():
                self.stdout.write(f"  Session {session_id[:8]}: Port {status['port']}, Active: {status['active']}")
            
            # Container status
            self.stdout.write("\nContainer Status:")
            for session_id in tunnel_status.keys():
                container_status = container_manager.get_container_status(session_id)
                if container_status['exists']:
                    self.stdout.write(f"  Session {session_id[:8]}: {container_status['status']}")

        elif action == 'restart_all':
            self.stdout.write('Restarting all tunnels for active sessions...')
            active_sessions = Session.objects.filter(status='ACTIVE')
            restarted = 0
            failed = 0

            for session in active_sessions:
                if tunnel_manager.restart_tunnel(str(session.id)):
                    restarted += 1
                    self.stdout.write(f"  ✓ Restarted tunnel for session {str(session.id)[:8]}")
                else:
                    failed += 1
                    self.stdout.write(f"  ✗ Failed to restart tunnel for session {str(session.id)[:8]}")

            self.stdout.write(
                self.style.SUCCESS(f'Restarted {restarted} tunnels, {failed} failed')
            )

        elif action == 'sync_sessions':
            self.stdout.write('Syncing session status with tunnel status...')
            active_sessions = Session.objects.filter(status='ACTIVE')
            updated = 0

            for session in active_sessions:
                tunnel_active = tunnel_manager.is_tunnel_active(str(session.id))
                
                if tunnel_active and session.connection_status != 'CONNECTED':
                    session.connection_status = 'CONNECTED'
                    session.save()
                    updated += 1
                    self.stdout.write(f"  ✓ Updated session {str(session.id)[:8]} to CONNECTED")
                elif not tunnel_active and session.connection_status == 'CONNECTED':
                    session.connection_status = 'DISCONNECTED'
                    session.save()
                    updated += 1
                    self.stdout.write(f"  ✓ Updated session {str(session.id)[:8]} to DISCONNECTED")

            self.stdout.write(
                self.style.SUCCESS(f'Updated {updated} session statuses')
            )
