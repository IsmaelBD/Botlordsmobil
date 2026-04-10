"""
ui/web/app.py — Web Control Dashboard
Flask + Socket.IO dashboard to monitor and control the bot in real-time.
"""

import json
import threading
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "lords-mobile-bot-secret"
socketio = SocketIO(app, cors_allowed_origins="*")

# Global engine reference (set from main.py)
engine = None
gatherer = None
redeemer = None


def set_engine(e):
    global engine, gatherer, redeemer
    engine = e


def set_gatherer(g):
    global gatherer
    gatherer = g


def set_redeemer(r):
    global redeemer
    redeemer = r


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/status")
def status():
    if engine:
        return jsonify(engine.status)
    return jsonify({"error": "Engine not initialized"})


@app.route("/api/config")
def get_config():
    cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
    with open(cfg) as f:
        return jsonify(json.load(f))


@app.route("/api/config", methods=["POST"])
def update_config():
    cfg = Path(__file__).parent.parent.parent / "config" / "settings.json"
    with open(cfg, "w") as f:
        json.dump(request.json, f, indent=2)
    return jsonify({"status": "ok"})


@app.route("/api/redeem", methods=["POST"])
def redeem():
    code = request.json.get("code", "LM2026")
    if redeemer:
        success = redeemer.redeem(code)
        return jsonify({"code": code, "success": success})
    return jsonify({"error": "Redeemer not initialized"})


@app.route("/api/gather", methods=["POST"])
def gather():
    targets = request.json.get("targets", [(522, 356)])
    if gatherer:
        threading.Thread(
            target=gatherer.run_cycle,
            args=(targets,),
            daemon=True
        ).start()
        return jsonify({"status": "started", "targets": targets})
    return jsonify({"error": "Gatherer not initialized"})


@socketio.on("connect")
def on_connect():
    emit("status", engine.status if engine else {})


@socketio.on("ping")
def on_ping():
    emit("status", engine.status if engine else {})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
