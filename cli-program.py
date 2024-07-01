import psutil
import os

import subprocess

print(subprocess.run(["ls", "-l"]))
# can also use the subprocess call function
# probably faster then the os module and also safer


def cpu_percent(t):
    return psutil.cpu_percent(interval=t)
def memory_percent():
    return psutil.virtual_memory().percent
def disk_percent():
    return psutil.disk_usage('/').percent



t = 0.1

def alert(what, value):
    print(f"Alert: {what} is {value}")


for i in range(20):
    if cpu_percent(t) > 90:
        alert("CPU", cpu_percent(t))
    if memory_percent() > 90:
        alert("Memory", memory_percent())
    print(cpu_percent(t), memory_percent())

os.system("ls -l")
print(os.system("ls -l"))        