# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import TimeSeriesData, MetricType, LogEntry
from collections import defaultdict
from django.db.models.functions import TruncDate
from django.db.models import DateField, Max, Min
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

def docker_monitor(request):
    # Get all running containers
    containers = client.containers.list(all=True)

    # Collect data for each container
    container_data = []
    for container in containers:
        stats = container.stats(stream=False)
        
        container_info = {
            'name': container.name,
            'status': container.status,
            'cpu_usage': calculate_cpu_usage(stats),
            'memory_usage': calculate_memory_usage(stats),
            'network_io': calculate_network_io(stats),
            'disk_io': calculate_disk_io(stats),
            'restart_count': container.attrs['RestartCount'],
            'ports': container.attrs['NetworkSettings']['Ports'],
            'uptime': container.attrs['State']['StartedAt'],
            'health_status': container.attrs['State'].get('Health', {}).get('Status', 'N/A')
        }
        container_data.append(container_info)

    # Send the container data to the template
    return render(request, 'dashboard/docker_monitor.html', {'containers': container_data})

# Helper function for calculating CPU usage
def calculate_cpu_usage(stats):
    try:
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        cpu_usage = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0
        return round(cpu_usage, 2)
    except (KeyError, ZeroDivisionError):
        return 'N/A'

# Helper function for calculating memory usage
def calculate_memory_usage(stats):
    try:
        mem_usage = stats['memory_stats']['usage']
        mem_limit = stats['memory_stats']['limit']
        return round((mem_usage / mem_limit) * 100.0, 2)
    except KeyError:
        return 'N/A'

# Helper function for calculating network I/O
def calculate_network_io(stats):
    try:
        networks = stats.get('networks', {})
        io_data = {}
        for interface, data in networks.items():
            io_data[interface] = {
                'rx_bytes': data['rx_bytes'],
                'tx_bytes': data['tx_bytes']
            }
        return io_data
    except KeyError:
        return {}

# Helper function for calculating disk I/O
def calculate_disk_io(stats):
    try:
        # Safely extract the disk IO data, ensuring it's not None
        disk_io_data = stats.get('blkio_stats', {}).get('io_service_bytes_recursive', [])
        if disk_io_data is None:
            return {}

        io_data = {}
        for item in disk_io_data:
            io_data[item.get('op', 'Unknown')] = item.get('value', 0)
        return io_data
    except KeyError:
        return {}

# DB TEST
@login_required
def dashboard(request):
    # Define time range (last 10 minutes)
    end_time = timezone.now()
    start_time = end_time - datetime.timedelta(minutes=10)

    # Get metric types
    metrics = MetricType.objects.all()

    data = {}
    for metric in metrics:
        # Retrieve data points for each metric within the last 10 minutes
        data_points = TimeSeriesData.objects.filter(
            metric_type=metric,
            timestamp__range=(start_time, end_time)
        ).order_by('timestamp')

        # Prepare data for Chart.js
        data[metric.name] = {
            'timestamps': [dp.timestamp.strftime("%H:%M:%S") for dp in data_points],
            'values': [dp.value for dp in data_points],
            'unit': metric.unit,
        }

    context = {'data': data}
    return render(request, 'dashboard/index.html', context)

def latest_data(request):
    metrics = MetricType.objects.all()

    data = {}
    for metric in metrics:
        # Get the latest data point for each metric
        latest_data_point = TimeSeriesData.objects.filter(
            metric_type=metric
        ).order_by('-timestamp').first()

        if latest_data_point:
            data[metric.name] = {
                'timestamp': latest_data_point.timestamp.strftime("%H:%M:%S"),
                'value': latest_data_point.value,
                'unit': metric.unit,
            }

    return JsonResponse(data)

# LOGS

def logs(request):
    # Find the highest priority level among the logs
    lowest_priority = LogEntry.objects.all().aggregate(Min('priority'))['priority__min']
    
    if lowest_priority is not None:
        # Filter logs with only the lowest priority level and order them by date
        logs = LogEntry.objects.filter(priority=lowest_priority).order_by('-timestamp')
        
        # Group logs by date
        grouped_logs = {}
        for log in logs:
            date_str = log.timestamp.date()
            if date_str not in grouped_logs:
                grouped_logs[date_str] = []
            grouped_logs[date_str].append(log)
    else:
        # If there are no logs, set grouped_logs to an empty dictionary
        grouped_logs = {}
    
    return render(request, 'dashboard/logs.html', {'grouped_logs': grouped_logs})




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
# views.py

def custom_logout(request):
    logout(request)
    return redirect('login')
