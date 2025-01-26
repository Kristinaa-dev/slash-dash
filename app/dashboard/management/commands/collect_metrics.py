from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import MetricType, TimeSeriesData, Node
import psutil
import time

class Command(BaseCommand):
    help = 'Collect system metrics periodically'

    def handle(self, *args, **options):
        # Retrieve or create metric types
        
        metrics = {
            'cpu_usage': MetricType.objects.get_or_create(name='cpu_usage', defaults={'unit': '%'})[0],
            'memory_usage': MetricType.objects.get_or_create(name='memory_usage', defaults={'unit': '%'})[0],
            'network_io': MetricType.objects.get_or_create(name='network_io', defaults={'unit': 'bytes'})[0],
            'disk_used': MetricType.objects.get_or_create(name='disk_used', defaults={'unit': '%'})[0],
            'server_uptime': MetricType.objects.get_or_create(name='server_uptime', defaults={'unit': 'seconds'})[0],
        }

        # Retrieve or create the Node named "Control"
        node, created = Node.objects.get_or_create(
            name='Control',
            defaults={
                'ip_address': '127.0.0.1',
                'node_type': 'Control',
                'location': 'Europe',        # Adjust as needed
                'ssh_username': 'root',      # Set a default username
                'ssh_password': 'password',  # Set a default password
                'status': 'online',
            }
        )
        if created:
            self.stdout.write("Created 'Control' Node since it did not exist.")

        try:
            timestamp = timezone.now()

            # Collect metrics using psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            net_io = psutil.net_io_counters()
            disk_usage_info = psutil.disk_usage('/')
            uptime_seconds = int(time.time() - psutil.boot_time())
            total_network_io = net_io.bytes_sent + net_io.bytes_recv
            disk_used = round((disk_usage_info.used / disk_usage_info.total) * 100, 1)

            # Create TimeSeriesData records individually to trigger the post_save signal
            TimeSeriesData.objects.create(
                node=node,
                metric_type=metrics['cpu_usage'],
                timestamp=timestamp,
                value=cpu_usage
            )
            TimeSeriesData.objects.create(
                node=node,
                metric_type=metrics['memory_usage'],
                timestamp=timestamp,
                value=memory_usage
            )
            TimeSeriesData.objects.create(
                node=node,
                metric_type=metrics['network_io'],
                timestamp=timestamp,
                value=total_network_io
            )
            TimeSeriesData.objects.create(
                node=node,
                metric_type=metrics['disk_used'],
                timestamp=timestamp,
                value=disk_used
            )
            TimeSeriesData.objects.create(
                node=node,
                metric_type=metrics['server_uptime'],
                timestamp=timestamp,
                value=uptime_seconds
            )

            self.stdout.write(f"Metrics collected at {timestamp} for node: {node.name}")

        except KeyboardInterrupt:
            self.stdout.write("Data collection stopped.")
