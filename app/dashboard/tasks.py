# dashboard/tasks.py
from celery import shared_task
from django.core.management import call_command
from django.core.cache import cache
from .views import calculate_memory_usage, calculate_cpu_usage, format_ports, format_uptime
import docker

@shared_task
def run_collect_metrics():
    call_command("collect_metrics")
    
@shared_task
def run_collect_logs():
    call_command("fetch_system_logs")    
    
@shared_task
def update_docker_stats():
    client = docker.from_env()
    containers = client.containers.list(all=True)
    data_list = []
    for container in containers:
        # Only call stats for running containers
        if container.status == 'running':
            stats = container.stats(stream=False)
            data_list.append({
                'id': container.short_id,
                'name': container.name,
                'status': container.status,
                'cpu_usage': calculate_cpu_usage(stats),
                'memory_usage': calculate_memory_usage(stats),
                'uptime': format_uptime(container.attrs['State']['StartedAt']),
                'ports': format_ports(container.attrs['NetworkSettings']['Ports']),
            })
        else:
            data_list.append({
                'id': container.short_id,
                'name': container.name,
                'status': container.status,
                'cpu_usage': 'N/A',
                'memory_usage': 'N/A',
                'uptime': 'N/A',
                'ports': format_ports(container.attrs['NetworkSettings']['Ports']),
            })
    cache.set('docker_stats', data_list, timeout=30)
    
@shared_task
def collect_node_data():
    call_command("collect_node_data")
    
@shared_task    
def ping_nodes():
    call_command("ping_nodes")