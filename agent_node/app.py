# agent.py
# Minimal Flask application representing the agent node.

from flask import Flask, request, jsonify
from datetime import datetime
import socket
import os

# Import the secret token from config or environment
try:
    from config import SECRET_TOKEN
except ImportError:
    # Fallback if config.py does not exist or SECRET_TOKEN is not defined
    SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "default-secret-token")

app = Flask(__name__)

# In-memory tracking. In a real system, use a database (SQLite, Redis, etc.).
LAST_PING = None
ACCESS_REVOKED = False

def verify_token(token):
    """Check if the provided token matches the SECRET_TOKEN.
       In production, consider stronger security practices (JWT, SSL, etc.)."""
    return token == SECRET_TOKEN

@app.route("/ping", methods=["GET"])
def ping():
    """
    Health check endpoint the control node can call to verify the agent is online.
    Checks a simple Bearer token for authorization.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized: missing or invalid Authorization header"}), 401

    # Extract the token
    token = auth_header.replace("Bearer ", "")
    if not verify_token(token):
        return jsonify({"error": "Unauthorized: invalid token"}), 403

    if ACCESS_REVOKED:
        return jsonify({"status": "offline", "reason": "access_revoked"}), 403

    global LAST_PING
    LAST_PING = datetime.utcnow()

    # Return agent hostname for clarity
    hostname = socket.gethostname()
    return jsonify({
        "status": "online",
        "agent_hostname": hostname,
        "last_ping": LAST_PING.isoformat()
    }), 200

@app.route("/revoke", methods=["POST"])
def revoke():
    """
    Endpoint to manually revoke agent access (for demonstration).
    In reality, the control node might set a flag in the DB,
    and the agent can check it. Or the agent might poll the control node.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized: missing or invalid Authorization header"}), 401

    token = auth_header.replace("Bearer ", "")
    if not verify_token(token):
        return jsonify({"error": "Unauthorized: invalid token"}), 403

    global ACCESS_REVOKED
    ACCESS_REVOKED = True
    return jsonify({"message": "Access revoked."}), 200

if __name__ == "__main__":
    # Run Flask app on 0.0.0.0 so it’s accessible from outside the container/host
    app.run(host="0.0.0.0", port=5000, debug=True)
