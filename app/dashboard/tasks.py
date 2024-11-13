# dashboard/tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def run_collect_metrics():
    call_command("collect_metrics")
    call_command("fetch_system_logs")
