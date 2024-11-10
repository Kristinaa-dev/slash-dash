from django.core.management.base import BaseCommand
from dashboard.models import MetricType, TimeSeriesData
from django.utils import timezone
import psutil
import time

class Command(BaseCommand):
    help = 'Collect system metrics periodically'

    def handle(self, *args, **options):
        # Initialize or get MetricType instances
        metrics = {
            'cpu_usage': MetricType.objects.get_or_create(name='cpu_usage', defaults={'unit': '%'})[0],
            'memory_usage': MetricType.objects.get_or_create(name='memory_usage', defaults={'unit': '%'})[0],
            'network_io': MetricType.objects.get_or_create(name='network_io', defaults={'unit': 'bytes'})[0],
            'disk_io': MetricType.objects.get_or_create(name='disk_io', defaults={'unit': 'bytes'})[0],
        }

        try:
            
            timestamp = timezone.now()

            # Collect metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            net_io = psutil.net_io_counters()
            disk_io = psutil.disk_io_counters()

            total_network_io = net_io.bytes_sent + net_io.bytes_recv
            total_disk_io = disk_io.read_bytes + disk_io.write_bytes

            # Save metrics
            TimeSeriesData.objects.bulk_create([
                TimeSeriesData(metric_type=metrics['cpu_usage'], timestamp=timestamp, value=cpu_usage),
                TimeSeriesData(metric_type=metrics['memory_usage'], timestamp=timestamp, value=memory_usage),
                TimeSeriesData(metric_type=metrics['network_io'], timestamp=timestamp, value=total_network_io),
                TimeSeriesData(metric_type=metrics['disk_io'], timestamp=timestamp, value=total_disk_io),
            ])

            self.stdout.write(f"Metrics collected at {timestamp}")
            # time.sleep(9)  # Adjust the sleep time to achieve the desired collection interval

        except KeyboardInterrupt:
            self.stdout.write("Data collection stopped.")
