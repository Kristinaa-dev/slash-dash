# views.py
from django.shortcuts import render
from django.http import JsonResponse
import psutil
import platform
import docker

def get_services_data():
    services = []

    if platform.system() == 'Windows':
        # For Windows systems
        try:
            for service in psutil.win_service_iter():
                service_info = service.as_dict()
                services.append({
                    'name': service_info['name'],
                    'display_name': service_info['display_name'],
                    'status': service_info['status'],
                    'pid': service_info.get('pid', None),
                    'username': service_info.get('username', ''),
                    'binpath': service_info.get('binpath', ''),
                    'description': service_info.get('description', ''),
                })
        except Exception as e:
            # Handle exception if needed
            pass
    else:
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
            # Handle exception if needed
            pass

    return services

def get_system_data():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')

    services = get_services_data()

    return {
        'cpu_usage': cpu_usage,
        'memory_info': memory_info.total,
        'memory_used': memory_info.used,
        'memory_free': memory_info.free,
        'memory_percent': memory_info.percent,
        'disk_total': disk_info.total,
        'disk_used': disk_info.used,
        'disk_free': disk_info.free,
        'services': services,  # Include services data
    }

def index(request):
    context = get_system_data()
    return render(request, 'dashboard/index.html', context)

def system_data(request):
    data = get_system_data()
    return JsonResponse(data)


# DOCKER CONTAINER MANAGEMENT


# Initialize Docker client
client = docker.from_env()

def get_docker_containers():
    containers = []
    try:
        for container in client.containers.list(all=True):
            containers.append({
                'id': container.short_id,
                'name': container.name,
                'status': container.status,
                'ports': container.ports,
                'image': container.image.tags,
            })
    except Exception as e:
        pass
    return containers

def docker_monitor_view(request):
    containers = get_docker_containers()
    context = {
        'containers': containers
    }
    return render(request, 'dashboard/docker_monitor.html', context)

def container_logs_view(request, container_id):
    container = client.containers.get(container_id)
    logs = container.logs().decode()
    return JsonResponse({'logs': logs})
