# dashboard/tasks.py
from celery import shared_task
from django.core.management import call_command
from django.core.cache import cache
from .views import calculate_memory_usage, calculate_cpu_usage, format_ports, format_uptime
import docker

from .models import AlertRule, TimeSeriesData, LogEntry
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


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
    
    
    
    
def compare(value, threshold, operator):
    if operator == '>':
        return value > threshold
    elif operator == '<':
        return value < threshold
    elif operator == '=':
        return value == threshold
    elif operator == '>=':
        return value >= threshold
    elif operator == '<=':
        return value <= threshold
    elif operator == '!=':
        return value != threshold


# @shared_task
# def check_alert_rules2    ():
#     """
#     Periodic Celery task that:
#     1. Iterates over active AlertRules
#     2. Fetches the latest metric value for that node & metric
#     3. Compares the value against the threshold
#     4. If threshold is crossed:
#        - Send email to user
#        - Create a LogEntry with the alert info
#     """
#     now = timezone.now()
#     active_rules = AlertRule.objects.filter(is_active=True).select_related('node', 'metric_type', 'user')

#     for rule in active_rules:
#         # Get the latest TimeSeriesData entry for this node & metric
#         latest_data = (TimeSeriesData.objects
#                        .filter(node=rule.node, metric_type=rule.metric_type)
#                        .order_by('-timestamp')
#                        .first())

#         if not latest_data:
#             # No data for this metric yet; skip
#             continue

#         # Compare the latest metric value with the threshold
#         if compare(latest_data.value, rule.threshold, rule.comparison_type):
#             # Threshold is violated, create a log entry and send an email

#             log_msg = (f"Threshold exceeded for metric '{rule.metric_type.name}' "
#                        f"on node '{rule.node.name}'. Value={latest_data.value} "
#                        f"Threshold={rule.comparison_type} {rule.threshold}")

#             # 1. Log the event
#             LogEntry.objects.create(
#                 timestamp=now,
#                 hostname=rule.node.name,
#                 service="AlertService",
#                 priority=4,  # Warning or 3 for Error, etc.
#                 message=log_msg,
#             )

#             # 2. Send an email notification
#             subject = f"Alert: {rule.metric_type.name} threshold exceeded on {rule.node.name}"
#             email_body = (
#                 f"Dear {rule.user.username},\n\n"
#                 f"{log_msg}\n\n"
#                 "Best regards,\nYour Monitoring System"
#             )

#             send_mail(
#                 subject,
#                 email_body,
#                 settings.DEFAULT_FROM_EMAIL,  # or some other from address
#                 [rule.user.email],
#                 fail_silently=False
#             )