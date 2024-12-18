# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import TimeSeriesData, MetricType, LogEntry
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


#TODO: Loading takes 5 sec need to optimize 
# The slow down is in the for loop
import time

def docker_monitor(request):
    start_time = time.time()
    containers = client.containers.list(all=True)
    print(f"Fetched containers: {time.time() - start_time:.2f}s")

    container_data = []

    for container in containers:
        container_start = time.time()
        stats = container.stats(stream=False)
        print(f"Stats fetched for {container.name}: {time.time() - container_start:.2f}s")

        if container.status == 'running':
            uptime = format_uptime(container.attrs['State']['StartedAt'])
        else:
            uptime = 'N/A'

        memory_usage = calculate_memory_usage(stats)

        container_data.append({
            'id': container.short_id,
            'name': container.name,
            'image': container.image.tags[0] if container.image.tags else "Unknown",
            'ports': format_ports(container.attrs.get('NetworkSettings', {}).get('Ports', {})),
            'cpu_usage': calculate_cpu_usage(stats),
            'memory_usage': memory_usage,
            'uptime': uptime,
            'status': container.status,
        })
    print(f"Total time: {time.time() - start_time:.2f}s")
    return render(request, 'dashboard/docker_monitor.html', {'containers': container_data})


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
        # Parse the ISO8601 timestamp
        started_time = datetime.strptime(started_at.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        started_time = started_time.replace(tzinfo=None)  # Ensure timezone compatibility
        now_time = datetime.utcnow()

        # Calculate the difference
        delta = now_time - started_time

        # Convert to days, hours, or minutes
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
            'timestamps': [dp.timestamp.strftime("%H:%M") for dp in data_points],
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
                'timestamp': latest_data_point.timestamp.strftime("%H:%M"),
                'value': latest_data_point.value,
                'unit': metric.unit,
            }

    return JsonResponse(data)

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
        
    if search_term != None:
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
