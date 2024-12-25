# myapp/management/commands/fetch_docker_stats.py

import docker
import traceback
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = "Collect Docker stats and store them in the Django cache."

    def handle(self, *args, **options):
        """
        This command fetches Docker stats for all containers and stores
        them in the cache under the 'docker_stats' key.
        """
        self.stdout.write("Starting to fetch Docker stats...")
        client = docker.from_env()

        container_data = []
        containers = client.containers.list(all=True)

        for container in containers:
            try:
                if container.status == 'running':
                    stats = container.stats(stream=False)
                    memory_usage = self.calculate_memory_usage(stats)
                    cpu_usage = self.calculate_cpu_usage(stats)
                    uptime = self.format_uptime(container.attrs['State']['StartedAt'])
                else:
                    memory_usage = "N/A"
                    cpu_usage = "N/A"
                    uptime = "N/A"

                container_data.append({
                    'id': container.short_id,
                    'name': container.name,
                    'image': container.image.tags[0] if container.image.tags else "Unknown",
                    'ports': self.format_ports(container.attrs.get('NetworkSettings', {}).get('Ports', {})),
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'uptime': uptime,
                    'status': container.status,
                })
            except Exception as e:
                self.stderr.write(f"Error fetching stats for container {container.name}: {e}")
                self.stderr.write(traceback.format_exc())

        # Cache the data for 10 seconds (adjust the timeout as needed)
        cache.set('docker_stats', container_data, timeout=10)
        self.stdout.write("Successfully cached Docker stats.")

    def calculate_memory_usage(self, stats):
        try:
            mem_usage = stats['memory_stats']['usage']
            mem_limit = stats['memory_stats']['limit']

            current_usage, cur_unit = self.format_memory_size(mem_usage)
            max_limit, max_unit = self.format_memory_size(mem_limit)

            return f"{current_usage}{cur_unit} / {max_limit}{max_unit}"
        except KeyError:
            return "N/A"

    def format_memory_size(self, bytes_value):
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = bytes_value
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return round(size, 2), units[unit_index]

    def calculate_cpu_usage(self, stats):
        try:
            cpu_stats = stats['cpu_stats']
            precpu_stats = stats['precpu_stats']

            total_usage = cpu_stats['cpu_usage']['total_usage']
            pre_total_usage = precpu_stats['cpu_usage']['total_usage']

            system_cpu_usage = cpu_stats.get('system_cpu_usage', 0)
            pre_system_cpu_usage = precpu_stats.get('system_cpu_usage', 0)

            cpu_delta = total_usage - pre_total_usage
            system_delta = system_cpu_usage - pre_system_cpu_usage

            if system_delta > 0 and cpu_delta > 0:
                num_cpus = len(cpu_stats['cpu_usage'].get('percpu_usage', []))
                cpu_usage = (cpu_delta / system_delta) * num_cpus * 100.0
                return f"{round(cpu_usage, 2)} %"

            return 'N/A'
        except ZeroDivisionError:
            return 0.0

    def format_ports(self, ports_dict):
        formatted_ports = []
        for port, bindings in ports_dict.items():
            if bindings:
                for binding in bindings:
                    port_num = port.split("/")[0]
                    formatted_ports.append(f"{port_num}:{binding['HostPort']}")
            else:
                formatted_ports.append(port)
        return ", ".join(formatted_ports)

    def format_uptime(self, started_at):
        try:
            started_time = datetime.strptime(started_at.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            now_time = datetime.utcnow()
            delta = now_time - started_time

            if delta.days > 0:
                return f"{delta.days} days"
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                return f"{hours} hours"
            elif delta.seconds >= 60:
                minutes = delta.seconds // 60
                return f"{minutes} minutes"
            else:
                return "Just now"
        except Exception:
            return "N/A"
