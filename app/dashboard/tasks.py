# dashboard/tasks.py
from celery import shared_task
from django.core.management import call_command
from django.core.cache import cache
from .views import calculate_memory_usage, calculate_cpu_usage, format_ports, format_uptime
import docker

@shared_task
def run_collect_metrics():
    call_command("collect_metrics")
    call_command("fetch_system_logs")
    
@shared_task
def cache_docker_stats():
    call_command("fetch_docker_stats")