# myapp/management/commands/create_fake_alerts.py

import random
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Alert

class Command(BaseCommand):
    help = "Create a bunch of fake Alerts for testing."

    def add_arguments(self, parser):
        parser.add_argument('--num', type=int, default=50,
                            help='Number of fake alerts to create.')

    def handle(self, *args, **options):
        num = options['num']
        severities = ['info', 'warning', 'critical']

        now = timezone.now()
        start_time = now - datetime.timedelta(days=2)  # We'll randomly place them in last 2 days

        for i in range(num):
            random_severity = random.choice(severities)
            # Random time between start_time and now
            random_timestamp = start_time + datetime.timedelta(
                seconds=random.randint(0, int((now - start_time).total_seconds()))
            )
            msg = f"This is a test alert (#{i+1}) with severity {random_severity}"
            Alert.objects.create(
                timestamp=random_timestamp,
                severity=random_severity,
                message=msg,
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {num} fake alerts.")
        )
