from django.contrib.auth.models import User
from django.utils import timezone
from api.models import Host, GPU, Renter, Session

HOST_EMAIL = 'dahal@gmail.com'
RENTER_USERNAME = 'dev_renter'
RENTER_EMAIL = 'dev_renter@example.com'
RENTER_PASSWORD = 'renterpass'

host = Host.objects.filter(user__email=HOST_EMAIL).first()
if not host:
    print('ERROR: Host not found for', HOST_EMAIL)
    raise SystemExit(1)

gpus = GPU.objects.filter(host=host, gpu_availability=True)
if not gpus.exists():
    print('ERROR: No available GPUs found for host', HOST_EMAIL)
    raise SystemExit(1)

gpu = gpus.first()
print('Using GPU:', gpu.id, gpu.gpu_name)

user, created = User.objects.get_or_create(username=RENTER_USERNAME, defaults={'email': RENTER_EMAIL})
if created:
    user.set_password(RENTER_PASSWORD)
    user.save()
    print('Created renter user', RENTER_USERNAME)
else:
    print('Using existing user', RENTER_USERNAME)

renter, _ = Renter.objects.get_or_create(user=user)

start_time = timezone.now()

session = Session.objects.create(
    gpu=gpu,
    renter=renter,
    host=host,
    start_time=start_time,
    status='PENDING',
    connection_status='CONNECTING'
)

print('SESSION_CREATED', session.id)
