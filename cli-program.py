import docker
import time

# Initialize the Docker client
client = docker.from_env()

# Function to create and start a container
def create_container(name, command):
    print(f"Creating container: {name}")
    container = client.containers.run(
        "alpine",                # Using Alpine Linux for simplicity
        command=command,         # Command to run inside the container
        name=name,               # Container name
        detach=True,             # Run container in detached mode
        auto_remove=True,        # Automatically remove the container when stopped
        tty=True                 # Allocate a pseudo-TTY for the container
    )
    return container

# Create 5 containers with low CPU usage
containers = []
for i in range(5):
    container_name = f"test_container_{i+1}"
    # Simple command to generate CPU load and logs
    command = "sh -c 'while true; do echo \"Log from container $HOSTNAME\"; sleep 2; done'"
    container = create_container(container_name, command)
    containers.append(container)

# Print the running containers
for container in containers:
    print(f"Container {container.name} is running with ID {container.short_id}")

# Let the containers run for a while to generate logs and CPU usage
try:
    print("Containers are running. Press Ctrl+C to stop...")
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("\nStopping containers...")
    for container in containers:
        container.stop()

print("All containers stopped.")