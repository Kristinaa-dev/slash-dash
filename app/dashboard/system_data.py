import psutil
import socket

def retrieve_system_data():
    """
    Gathers CPU, memory, and disk usage from psutil,
    along with hostname and IP address. Returns a dict.
    """
    cpu_usage = psutil.cpu_percent(interval=1)
    
    mem = psutil.virtual_memory()
    mem_usage = mem.percent
    
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent

    # Get hostname and IP address for example
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    # Hard-coded example for region & status. Adjust as needed.
    node = {
        'hostname': hostname,
        'ip_address': ip_address,
        'region': 'US East',
        'status': 'online',
        'type': 'control',    # Could be 'control', 'agent', 'database', etc.

        # Usage percentages
        'cpu_usage': cpu_usage,
        'mem_usage': mem_usage,
        'disk_usage': disk_usage,
    }

    return node
