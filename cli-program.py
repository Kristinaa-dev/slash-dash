import psutil

def cpu_percent(t):
    return psutil.cpu_percent(interval=t)
def memory_percent():
    return psutil.virtual_memory().percent


t = 0.1

for i in range(200):
    print(cpu_percent(t), memory_percent())
