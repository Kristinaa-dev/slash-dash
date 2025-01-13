from django.core.management.base import BaseCommand
from django.utils.timezone import now
from dashboard.models import MetricType, TimeSeriesData, Node
import requests

class Command(BaseCommand):
    help = "Collect system metrics from all registered nodes (except Control) and store them in the database."

    def handle(self, *args, **options):
        # Retrieve all nodes except the 'Control' node
        nodes = Node.objects.exclude(name="Control")
        if not nodes.exists():
            self.stdout.write(self.style.WARNING("No nodes found to collect data from."))
            return

        # Retrieve or create metric types
        metrics = {
            'cpu_usage': MetricType.objects.get_or_create(name='cpu_usage', defaults={'unit': '%'})[0],
            'memory_usage': MetricType.objects.get_or_create(name='memory_usage', defaults={'unit': '%'})[0],
            'network_io': MetricType.objects.get_or_create(name='network_io', defaults={'unit': 'bytes'})[0],
            'disk_used': MetricType.objects.get_or_create(name='disk_used', defaults={'unit': '%'})[0],
            'server_uptime': MetricType.objects.get_or_create(name='server_uptime', defaults={'unit': 'seconds'})[0],
        }

        # Iterate over each node and collect metrics
        for node in nodes:
            # self.stdout.write(f"Collecting data from {node.name} ({node.ip_address})...")
            try:
                response = requests.get(f"http://{node.ip_address}:5000/collect", timeout=10)
                response.raise_for_status()
                data = response.json()
                node.status = "online"
                node.save(update_fields=["status"])
                node.last_check_in = now()
                node.save(update_fields=["last_check_in"])
                # Parse the collected data
                timestamp = now()

                # Bulk create TimeSeriesData records
                TimeSeriesData.objects.bulk_create([
                    TimeSeriesData(node=node, metric_type=metrics['cpu_usage'], timestamp=timestamp, value=data.get('cpu_usage', 0)),
                    TimeSeriesData(node=node, metric_type=metrics['memory_usage'], timestamp=timestamp, value=data.get('memory_usage', 0)),
                    TimeSeriesData(node=node, metric_type=metrics['network_io'], timestamp=timestamp, value=data.get('network_io', 0)),
                    TimeSeriesData(node=node, metric_type=metrics['disk_used'], timestamp=timestamp, value=data.get('disk_used', 0)),
                    TimeSeriesData(node=node, metric_type=metrics['server_uptime'], timestamp=timestamp, value=data.get('server_uptime', 0)),
                ])

                # self.stdout.write(self.style.SUCCESS(f"Metrics collected successfully for node: {node.name}"))
            except requests.RequestException as e:
                node.status = "offline"
                node.save(update_fields=["status"])
                self.stdout.write(self.style.ERROR(f"Failed to collect data from {node.name}: {e}"))
