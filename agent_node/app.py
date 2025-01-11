from flask import Flask, jsonify
# from datetime import datetime
import socket
import psutil
import time
import datetime



app = Flask(__name__)

# We’ll keep a global variable to track the last ping time for demonstration
LAST_PING = None

@app.route("/ping", methods=["GET"])
def ping():
    """
    Minimal endpoint that returns a JSON response indicating the agent is online.
    No token checks here, so not very secure. 
    """
    global LAST_PING
    LAST_PING = datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z'


    return jsonify({
        "status": "online",
        "agent_hostname": socket.gethostname(),
        "last_ping": LAST_PING
    }), 200

@app.route('/collect', methods=['GET'])
def collect_metrics():
    # Use UTC timestamp
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z'

    # Collect system metrics
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    net_io = psutil.net_io_counters()
    disk_usage_info = psutil.disk_usage('/')
    uptime_seconds = int(time.time() - psutil.boot_time())

    # Calculate additional metrics
    total_network_io = net_io.bytes_sent + net_io.bytes_recv
    disk_used = round((disk_usage_info.free / disk_usage_info.total), 1)

    # Prepare the metrics dictionary
    metrics = {
        'timestamp': timestamp,
        'cpu_usage': cpu_usage,
        'memory_usage_percent': memory_usage,
        'network_io': total_network_io,
        'disk_usage': disk_used,  # WRONG NAME
        'server_uptime': uptime_seconds
    }

    # Return the metrics as JSON
    return jsonify(metrics)


if __name__ == "__main__":
    # Run Flask on 0.0.0.0:5000
    app.run(host="0.0.0.0", port=5000, debug=True)
