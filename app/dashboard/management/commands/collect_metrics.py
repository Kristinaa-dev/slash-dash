from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import MetricType, TimeSeriesData
import psutil
import time

class Command(BaseCommand):
    help = 'Collect system metrics periodically'

    def handle(self, *args, **options):
        metrics = {
            'cpu_usage': MetricType.objects.get_or_create(name='cpu_usage', defaults={'unit': '%'})[0],
            'memory_usage': MetricType.objects.get_or_create(name='memory_usage', defaults={'unit': '%'})[0],
            'network_io': MetricType.objects.get_or_create(name='network_io', defaults={'unit': 'bytes'})[0],
            'disk_space_available': MetricType.objects.get_or_create(name='disk_space_available', defaults={'unit': '%'})[0],
            'server_uptime': MetricType.objects.get_or_create(name='server_uptime', defaults={'unit': 'seconds'})[0],
        }

        try:
            timestamp = timezone.now()

            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            net_io = psutil.net_io_counters()
            disk_usage_info = psutil.disk_usage('/')
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_seconds = int(uptime_seconds)

            total_network_io = net_io.bytes_sent + net_io.bytes_recv
            free_disk_percentage = round((disk_usage_info.free / disk_usage_info.total) * 100, 1)

            TimeSeriesData.objects.bulk_create([
                TimeSeriesData(metric_type=metrics['cpu_usage'], timestamp=timestamp, value=cpu_usage),
                TimeSeriesData(metric_type=metrics['memory_usage'], timestamp=timestamp, value=memory_usage),
                TimeSeriesData(metric_type=metrics['network_io'], timestamp=timestamp, value=total_network_io),
                TimeSeriesData(metric_type=metrics['disk_space_available'], timestamp=timestamp, value=free_disk_percentage),
                TimeSeriesData(metric_type=metrics['server_uptime'], timestamp=timestamp, value=uptime_seconds),
            ])

            self.stdout.write(f"Metrics collected at {timestamp}")
        except KeyboardInterrupt:
            self.stdout.write("Data collection stopped.")
