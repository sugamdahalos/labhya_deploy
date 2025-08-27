# Generated migration to add deployment fields to HostKey
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_add_hostkey'),
    ]

    operations = [
        migrations.AddField(
            model_name='hostkey',
            name='deployment_status',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='hostkey',
            name='deployment_log',
            field=models.TextField(blank=True, null=True),
        ),
    ]
