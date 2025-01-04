from flask import Flask, jsonify
from datetime import datetime
import socket

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
    LAST_PING = datetime.utcnow()

    return jsonify({
        "status": "online",
        "agent_hostname": socket.gethostname(),
        "last_ping": LAST_PING.isoformat()
    }), 200

if __name__ == "__main__":
    # Run Flask on 0.0.0.0:5000
    app.run(host="0.0.0.0", port=5000, debug=True)
