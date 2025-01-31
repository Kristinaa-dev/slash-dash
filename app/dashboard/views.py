# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import TimeSeriesData, MetricType, LogEntry, Node
from collections import defaultdict
from django.db.models.functions import TruncDate
from django.db.models import DateField, Max, Min
from django.db import models
from itertools import groupby
from django.contrib.auth import login
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
import psutil
import platform
import docker
import datetime
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import time
import concurrent.futures
from .models import AlertRule


def is_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(is_admin)
def terminal_view(request):
    return render(request, "dashboard/terminal.html")

def get_services_data():
    services = []

    # For Unix-like systems, list running processes as services
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
            services.append({
                'name': proc.info['name'],
                'display_name': proc.info['name'],
                'status': proc.info['status'],
                'pid': proc.info['pid'],
                'username': proc.info['username'],
                'binpath': '',
                'description': '',
            })
    except Exception as e:
        pass

    return services

# DOCKER CONTAINER MANAGEMENT

# Create a Docker client
client = docker.from_env()

# Docker monitor view

from django.core.cache import cache
import concurrent.futures
import time

def docker_monitor(request):
    container_data = cache.get('docker_stats')
    if container_data:
        return render(request, 'dashboard/docker_monitor.html', {'containers': container_data})

    containers = client.containers.list(all=True)
    container_data = []

    def fetch_stats(container):
        stats = container.stats(stream=False)
        return {
            'id': container.short_id,
            'name': container.name,
            'image': container.image.tags[0] if container.image.tags else "Unknown",
            'ports': format_ports(container.attrs['NetworkSettings'].get('Ports', {})),
            'cpu_usage': calculate_cpu_usage(stats),
            'memory_usage': calculate_memory_usage(stats),
            'uptime': format_uptime(container.attrs['State']['StartedAt']) if container.status == 'running' else 'N/A',
            'status': container.status,
        }

    running = [c for c in containers if c.status == 'running']
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for res in executor.map(fetch_stats, running):
            container_data.append(res)

    for c in containers:
        if c.status != 'running':
            container_data.append({
                'id': c.short_id,
                'name': c.name,
                'image': c.image.tags[0] if c.image.tags else "Unknown",
                
                'ports': format_ports(c.attrs['NetworkSettings'].get('Ports', {})),
                'cpu_usage': 'N/A',
                'memory_usage': 'N/A',
                'uptime': 'N/A',
                'status': c.status,
            })

    cache.set('docker_stats', container_data, timeout=30)
    # print(f"Total time: {time.time() - start_time:.2f}s")
    return render(request, 'dashboard/docker_monitor.html', {'containers': container_data})

def get_docker_stats(request):
    container_data = cache.get('docker_stats') or []
    return JsonResponse(container_data, safe=False)

def calculate_memory_usage(stats):
    try:
        # Extract memory usage and limit
        mem_usage = stats['memory_stats']['usage']
        mem_limit = stats['memory_stats']['limit']

        # Convert to human-readable units
        current_usage, cur_unit = format_memory_size(mem_usage)
        max_limit, max_unit = format_memory_size(mem_limit)

        # Return formatted string
        return f"{current_usage}{cur_unit} / {max_limit}{max_unit}"
    except KeyError:
        return "N/A"

def format_memory_size(bytes_value):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = bytes_value
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return round(size, 2), units[unit_index]



def format_ports(ports_dict):
    formatted_ports = []
    for port, bindings in ports_dict.items():
        if bindings:
            for binding in bindings:
                port = port.split("/")[0]
                formatted_ports.append(f"{port}:{binding['HostPort']}")
        else:
            formatted_ports.append(port)
    return ", ".join(formatted_ports)




def format_uptime(started_at):
    try:
        started_time = datetime.strptime(started_at.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        started_time = started_time.replace(tzinfo=None)
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
    except Exception as e:
        return "N/A"

@csrf_exempt
def container_action(request, action, container_id):
    try:
        container = client.containers.get(container_id)

        if action == 'start':
            container.start()
        elif action == 'stop':
            container.stop()
        elif action == 'restart':
            container.restart()
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

        return JsonResponse({'status': f'{action.capitalize()}ed successfully'})
    except docker.errors.NotFound:
        return JsonResponse({'error': 'Container not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    

# Helper function for calculating CPU usage
def calculate_cpu_usage(stats):
    try:
        # Check if container is running
        # print(stats['status'])
        # Extract relevant stats
        cpu_stats = stats['cpu_stats']
        precpu_stats = stats['precpu_stats']

        # Total CPU usage (current and previous)
        total_usage = cpu_stats['cpu_usage']['total_usage']
        pre_total_usage = precpu_stats['cpu_usage']['total_usage']

        # System CPU usage (current and previous)
        system_cpu_usage = cpu_stats.get('system_cpu_usage', 0)
        pre_system_cpu_usage = precpu_stats.get('system_cpu_usage', 0)

        # Calculate deltas
        cpu_delta = total_usage - pre_total_usage
        system_delta = system_cpu_usage - pre_system_cpu_usage

        # Check for division by zero
        if system_delta > 0 and cpu_delta > 0:
            # Number of CPUs available to the container
            num_cpus = len(cpu_stats['cpu_usage'].get('percpu_usage', []))

            # Calculate CPU usage as a percentage
            cpu_usage = (cpu_delta / system_delta) * num_cpus * 100.0
            return f"{round(cpu_usage, 2)} %"

        return 'N/A'  # Return 0.0 if no meaningful usage is detected
    except ZeroDivisionError:
        # Handle edge cases of division by zero
        return 0.0


# DB TEST
@login_required

# LOGS
def logs(request):
    from datetime import datetime
    selected_date = request.GET.get('date')
    search_term = request.GET.get('search')
    selected_priority = request.GET.get('priority')

    logs = LogEntry.objects.all()
    
    if selected_priority and selected_priority != 'all':
        try:
            priority_value = int(selected_priority)
            logs = logs.filter(priority=priority_value)
        except ValueError:
            pass
    else:
        pass
    if selected_date != None:
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date=date_obj)
        except ValueError:
            pass  
        
    if search_term != None and search_term != "None":
        logs = logs.filter(
            models.Q(message__icontains=search_term) |
            models.Q(service__icontains=search_term)
        )

    logs = logs.order_by('-timestamp')[:19]

    unique_priorities = LogEntry.PRIORITY_CHOICES

    return render(request, 'dashboard/logs.html', {
        'logs': logs,
        'unique_priorities': unique_priorities,
        'selected_priority': selected_priority,
        'selected_date': selected_date,
        'search_term': search_term,
    })


# Login 

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # "Stay Logged In" functionality
            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)  # Session expires on browser close
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            return redirect('dashboard')
        else:
            form.errors.clear()
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})

# LOGOUT

def custom_logout(request):
    logout(request)
    return redirect('login')

import libvirt
import subprocess

def check_service_status(service_name):
    try:
        # Run a systemctl command to check the service status
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:  # Service is running
            return 'running'
        elif result.returncode == 3:  # Service is stopped
            return 'stopped'
        else:
            return 'unknown'
    except Exception as e:
        return 'error'



def alerts_number():
    alerts_count = (
        AlertRule.objects
        .filter(is_active=True)
        .values('node__name')
        .annotate(alert_count=Count('id'))
        .order_by('-alert_count')[:3]
    )
    return alerts_count
    


@login_required
def dashboard(request): 
    end_time = timezone.now()
    start_time = end_time - timezone.timedelta(minutes=15)
    # Fetch metrics data 
    metrics = MetricType.objects.filter(name__in=['cpu_usage', 'memory_usage'])
    data = {}
    for metric in metrics:
        data_points = TimeSeriesData.objects.filter(
            metric_type=metric,
            timestamp__range=(start_time, end_time)
        ).order_by('timestamp')[:15]
        data[metric.name] = {
            'timestamps': [dp.timestamp.strftime("%H:%M") for dp in data_points],
            'values': [dp.value for dp in data_points],
            'unit': metric.unit,
        }
    # Fetch KVM VM status
    vm_data = []
    try:
        conn = libvirt.open("qemu:///system")
        if conn is None:
            raise Exception("Failed to open connection to qemu:///system")
        
        domains = conn.listAllDomains()
        for domain in domains[:3]:
            vm_data.append({
                'name': domain.name(),
                'status': 'running' if domain.isActive() else 'stopped'
            })
        conn.close()
    except Exception as e:
        vm_data = [{'name': 'Error', 'status': str(e)}]

    priority_counts = (
        LogEntry.objects
        .values('priority')
        .annotate(count=Count('id'))
    )
    
    # 2. Create a map for all possible priorities (based on your PRIORITY_CHOICES) with a default count of 0
    priority_map = {level: 0 for (level, label) in LogEntry.PRIORITY_CHOICES}
    for item in priority_counts:
        priority_map[item['priority']] = item['count']
    
    # 3. Prepare the data for Chart.js
    #    We'll keep the order of the priority choices as defined in your model
    priorities = [label for (level, label) in LogEntry.PRIORITY_CHOICES]
    counts = [priority_map[level] for (level, label) in LogEntry.PRIORITY_CHOICES]

    # Check NGINX and Apache status
    nginx_status = check_service_status('nginx')
    apache_status = check_service_status('apache2')  # Use 'httpd' for Red Hat-based distros
    postgres_status = check_service_status('postgresql')
    alerts = alerts_number()[:3]
    context = {
        'data': data,
        'vms': vm_data,
        'services': {
            'nginx': nginx_status,
            'apache': apache_status,
            'postgres': postgres_status,
        },
        'alerts': alerts,
        'priority_labels': priorities,
        'priority_data': counts,

    }
    return render(request, 'dashboard/index.html', context)

def latest_data(request):
    from math import floor
    metrics = MetricType.objects.all()
    data = {}

    for metric in metrics:
        latest_data_point = TimeSeriesData.objects.filter(
            metric_type=metric
        ).order_by('-timestamp').first()

        if latest_data_point:
            value = latest_data_point.value
            if metric.name == 'server_uptime':
                total_seconds = int(value)
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60

                if days > 0:
                    display_value = f"{days}d {hours}h"
                elif hours > 0:
                    display_value = f"{hours}h {minutes}m"
                elif minutes > 0:
                    display_value = f"{minutes}m {seconds}s"
                else:
                    display_value = f"{seconds}s"
            else:
                display_value = value

            if metric.name in ['cpu_usage', 'memory_usage']:
                data[metric.name] = {
                    'timestamp': latest_data_point.timestamp.strftime("%H:%M"),
                    'value': display_value,
                    'unit': metric.unit,
                }
            else:
                data[metric.name] = {
                    'value': display_value,
                    'unit': metric.unit,
                }

    return JsonResponse(data)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import requests
import time
from .models import Node
import socket

import psutil
from datetime import datetime
from django.utils import timezone
from django.utils.timesince import timesince
# import pytz
@login_required
def node_list(request):
    # Retrieve all nodes from the database
    nodes = Node.objects.all()
    node_data = {}

    for node in nodes:
        # Example: Force the Control node to always be "online" (if that is your requirement)
        if node.node_type == 'Control' and node.name == 'Control':
            node.status = 'online'
            node.last_check_in = timezone.now()
            node.save()

        # Gather latest metrics if node is online
        if node.status == 'offline':
            metrics = {}
        else:
            latest_metrics = (
                TimeSeriesData.objects
                .filter(node=node)
                .order_by('-timestamp')[:5]
            )
            metrics = {metric.metric_type.name: metric.value for metric in latest_metrics}

        node_data[node.name] = {
            "ip_address": node.ip_address,
            "status": node.status,
            "node_type": node.node_type,
            "location": node.location,
            "last_check_in": node.last_check_in,
            "metrics": metrics,
        }

    # Gather specific data for control node (if desired)
    online_nodes_count = Node.objects.filter(status='online').count()
    offline_nodes_count = Node.objects.filter(status='offline').count()
    hostname = socket.gethostname()

    
    tz_aware_boot_time = timezone.make_aware(datetime.fromtimestamp(psutil.boot_time()))
    uptime = timesince(tz_aware_boot_time, timezone.now())
    
    control_node = Node.objects.get(name='Control')  # or you can remove this if unused
    
    control_node_data = {
        "hostname": hostname,
        "ip": control_node.ip_address,
        "status": control_node.status,
        "uptime": uptime,
        "last_check_in": control_node.last_check_in,
        "online_nodes": online_nodes_count,
        "offline_nodes": offline_nodes_count,
        "total_nodes": online_nodes_count + offline_nodes_count,
    }
    # Build up your node_data dictionary

    def sort_key(item):
        """
        item is a tuple: (node_name, data_dict)
        data_dict has keys: "node_type", "status", ...
        """
        node_name, data = item
        # Priority for node_type 'Control' => 0
        # Priority for status 'online' => 1
        # Priority for everything else (offline, etc.) => 2
        if data['node_type'] == 'Control' and data['status'] == 'online':
            return 0
        elif data['status'] == 'online':
            return 1
        elif data['status'] == 'offline' and data['node_type'] == 'Control':
            return 2
        return 3

    # Sort node_data by our custom key
    sorted_node_data = sorted(node_data.items(), key=sort_key)
    # Pass sorted data to the template.
    # Notice now it’s a list of tuples, so adjust your template loop accordingly.
    context = {
        "nodes": nodes,  # if you still need the raw queryset
        "node_data": sorted_node_data,
        "control_node": control_node_data,
        "latest_alert_trig": "",
    }

    return render(request, "dashboard/node_list.html", context)



import paramiko
from django.shortcuts import render, redirect
from .forms import NodeForm
from .models import Node


def add_node(request):
    if request.method == "POST":
        form = NodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("node_list")
    else:
        form = NodeForm()

    return render(request, "dashboard/add_node.html", {"form": form})

def test_ssh_connection(ip, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)
        ssh.close()
        print("Connection successful")
        return True
    except Exception as e:
        return False

def get_node_data(request):
    nodes = Node.objects.all()
    node_list_data = []
    print("Getting node data...")
    for node in nodes:
        latest_metrics = TimeSeriesData.objects.filter(node=node).order_by('-timestamp')[:5]
        metrics = {metric.metric_type.name: metric.value for metric in latest_metrics}
        node_list_data.append({
            "name": node.name,
            "ip_address": node.ip_address,
            "status": node.status,
            "node_type": node.node_type,
            "location": node.location,
            "last_check_in": str(node.last_check_in),
            "metrics": metrics,
        })
    return JsonResponse(node_list_data, safe=False)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import AlertRuleForm
from .models import AlertRule

@login_required
def alert_list(request):
    alerts_queryset = AlertRule.objects.all()
    METRIC_LABELS = {
        'CPU Usage': 'cpu_usage',
        'Memory Usage': 'memory_usage',
        'Disk Used': 'disk_used',
    }

    alerts = []
    for alert in alerts_queryset:
        metric_name = METRIC_LABELS.get(alert.metric_type.name, alert.metric_type.name)
        threshold_str = f"{alert.comparison_type} {alert.threshold}%"
        
        alerts.append({
            'id': alert.id,
            'metric_label': metric_name,
            'threshold_str': threshold_str,
            'is_active': alert.is_active,
            'severity': alert.get_severity_display(),
            'cooldown': alert.cooldown_minutes,
            'last_triggered': alert.last_triggered_at.strftime("%Y-%m-%d %H:%M") if alert.last_triggered_at else 'Never',
        })

    if request.method == 'POST':
        form = AlertRuleForm(request.POST)
        if form.is_valid():
            alert_rule = form.save(commit=False)
            alert_rule.user = request.user
            alert_rule.save()
            messages.success(request, "Alert rule created successfully!")
            return redirect('alert_list')
    else:
        form = AlertRuleForm()

    return render(request, 'dashboard/alert_list.html', {
        'form': form,
        'alerts': alerts,
    })


from django.shortcuts import render
from django.db.models import Count
from .models import LogEntry

def log_priority_chart():
    # 1. Aggregate counts of LogEntry by priority
    priority_counts = (
        LogEntry.objects
        .values('priority')
        .annotate(count=Count('id'))
    )
    
    # 2. Create a map for all possible priorities (based on your PRIORITY_CHOICES) with a default count of 0
    priority_map = {level: 0 for (level, label) in LogEntry.PRIORITY_CHOICES}
    for item in priority_counts:
        priority_map[item['priority']] = item['count']
    
    # 3. Prepare the data for Chart.js
    #    We'll keep the order of the priority choices as defined in your model
    labels = [label for (level, label) in LogEntry.PRIORITY_CHOICES]
    data = [priority_map[level] for (level, label) in LogEntry.PRIORITY_CHOICES]
    
    # 4. Pass the labels and data to the template
    context = {
        'labels2': labels,  # e.g. ["Debug", "Info", "Notice", "Warning", ...]
        'data': data,      # e.g. [10, 25, 3, 7, ...]
    }
    
    return context


# views.py
# views.py
from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def combined_alert_view(request):
    import datetime
    import json
    from django.utils import timezone
    from datetime import timedelta
    from .forms import AlertRuleForm
    from .models import AlertRule, Alert

    def get_bucket_size_in_minutes(duration: timedelta, target_buckets: int = 25) -> int:
        """
        Same logic for dynamic bucket size...
        """
        total_minutes = duration.total_seconds() / 60.0
        bucket_size = int(total_minutes / target_buckets)
        if bucket_size <= 1:
            return 1
        elif bucket_size <= 5:
            return 5
        elif bucket_size <= 15:
            return 15
        elif bucket_size <= 30:
            return 30
        elif bucket_size <= 60:
            return 60
        elif bucket_size <= 120:
            return 120
        elif bucket_size <= 240:
            return 240
        else:
            return int(bucket_size // 60 * 60)

    # 1. Handle form submission for creating new alert rule
    if request.method == 'POST':
        form = AlertRuleForm(request.POST)
        if form.is_valid():
            alert_rule = form.save(commit=False)
            alert_rule.user = request.user  # If user association is needed
            alert_rule.save()
            messages.success(request, "Alert rule created successfully!")
            return redirect('combined_alert_view')
    else:
        form = AlertRuleForm()

    # 2. Get all alert rules for the list
    #    Group them by node so we can display them in tabs.
    alerts_queryset = AlertRule.objects.select_related('node', 'metric_type').all()

    # Example function that returns a textual metric label
    METRIC_LABELS = {
        'CPU Usage': 'cpu_usage',
        'Memory Usage': 'memory_usage',
        'Disk Used': 'disk_used',
    }

    # Group by node
    grouped_alerts = defaultdict(list)
    for alert_rule in alerts_queryset:
        node_name = str(alert_rule.node)
        grouped_alerts[node_name].append(alert_rule)

    # Sort so that active alerts come first
    for node_name in grouped_alerts:
        grouped_alerts[node_name].sort(key=lambda ar: not ar.is_active)

    # Ensure "Control" is always first
    grouped_alerts = dict(sorted(grouped_alerts.items(), key=lambda item: item[0] != "Control"))

    # 3. Parse chart time range from GET or default to last 24 hours
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=24)

    if 'start_time' in request.GET:
        try:
            parsed_start = datetime.datetime.fromisoformat(request.GET['start_time'])
            if not timezone.is_aware(parsed_start):
                parsed_start = timezone.make_aware(parsed_start)
            start_time = parsed_start
        except ValueError:
            pass

    if 'end_time' in request.GET:
        try:
            parsed_end = datetime.datetime.fromisoformat(request.GET['end_time'])
            if not timezone.is_aware(parsed_end):
                parsed_end = timezone.make_aware(parsed_end)
            end_time = parsed_end
        except ValueError:
            pass

    if end_time <= start_time:
        end_time = start_time + timedelta(hours=24)

    duration = end_time - start_time
    bucket_size_minutes = get_bucket_size_in_minutes(duration)

    # 4. Build time slots
    time_slots = []
    current = start_time
    while current < end_time:
        time_slots.append(current)
        current += timedelta(minutes=bucket_size_minutes)
    if not time_slots or time_slots[-1] < end_time:
        time_slots.append(end_time)

    # 5. Aggregate chart data
    chart_data = []
    for i in range(len(time_slots) - 1):
        slot_start = time_slots[i]
        slot_end = time_slots[i + 1]
        alerts_in_slot = Alert.objects.filter(timestamp__gte=slot_start, timestamp__lt=slot_end)
        chart_data.append({
            'time': slot_start.isoformat(),
            'info': alerts_in_slot.filter(severity='info').count(),
            'warning': alerts_in_slot.filter(severity='warning').count(),
            'critical': alerts_in_slot.filter(severity='critical').count(),
        })

    # 6. Prepare Chart.js datasets
    datasets = [
        {
            'label': 'Info',
            'data': [x['info'] for x in chart_data],
            'borderColor': '#3B82F6',
            'backgroundColor': '#3b82f610',
            'borderWidth': 3,
            'stack': 'stack_0'
        },
        {
            'label': 'Warning',
            'data': [x['warning'] for x in chart_data],
            'backgroundColor': '#eab20810',
            'borderColor': '#EAB308',
            'borderWidth': 3,
            'stack': 'stack_0'
        },
        {
            'label': 'Critical',
            'data': [x['critical'] for x in chart_data],
            'backgroundColor': '#ef444410',
            'borderColor': '#EF4444',
            'borderWidth': 3,
            'stack': 'stack_0'
        }
    ]

    context = {
        'form': form,
        'grouped_alerts': dict(grouped_alerts),  # convert defaultdict to a regular dict
        'start_time': start_time.isoformat(timespec='minutes'),
        'end_time': end_time.isoformat(timespec='minutes'),
        'labels': json.dumps([x['time'] for x in chart_data]),
        'datasets': json.dumps(datasets),
    }

    return render(request, 'dashboard/combined_alerts.html', context)

@login_required
def toggle_alert_active(request, alert_id):
    """
    Simple view to toggle the is_active field of an AlertRule.
    """
    alert_rule = get_object_or_404(AlertRule, id=alert_id, user=request.user)
    alert_rule.is_active = not alert_rule.is_active
    alert_rule.save()
    messages.success(request, f"Alert '{alert_rule.metric_type}' toggled to {alert_rule.is_active}.")
    return redirect('combined_alert_view')

@login_required
def edit_alert(request, alert_id):
    """
    Allow editing an existing alert rule.
    """
    from .forms import AlertRuleForm
    alert_rule = get_object_or_404(AlertRule, id=alert_id, user=request.user)

    if request.method == 'POST':
        form = AlertRuleForm(request.POST, instance=alert_rule)
        if form.is_valid():
            form.save()
            messages.success(request, "Alert rule updated successfully!")
            return redirect('combined_alert_view')
    else:
        form = AlertRuleForm(instance=alert_rule)

    return render(request, 'dashboard/edit_alert.html', {'form': form, 'alert_rule': alert_rule})
    