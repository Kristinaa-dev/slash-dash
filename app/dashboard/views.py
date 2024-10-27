# views.py
from django.shortcuts import render
from django.http import JsonResponse
import psutil
import platform
import docker


def terminal_view(request):
    return render(request, "dashboard/terminal.html")

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
