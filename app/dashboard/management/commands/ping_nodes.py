import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Node  # Adjust the import to your app's models


class Command(BaseCommand):
    help = 'Checks the status of nodes and updates their status in the database.'

    def handle(self, *args, **kwargs):
        nodes = Node.objects.all()
        for node in nodes:
            try:
                response = requests.get(f"http://{node.ip_address}:5000/ping", timeout=2)
                if response.status_code == 200:
                    node.status = "online"
                    node.last_check_in = timezone.now()
                else:
                    node.status = "offline"
            except requests.exceptions.RequestException:
                node.status = "offline"
            node.save()
