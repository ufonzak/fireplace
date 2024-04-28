
import os
import sys
import threading
from flask import Flask, send_from_directory, send_file, typing as flask
from .fireplace import Fireplace

app = Flask(__name__)
fireplace = Fireplace()


@app.get("/")
def index() -> flask.ResponseReturnValue:
    """Serve index file."""
    return send_file("index.html", mimetype="text/html")


@app.route("/static/<path:path>")
def serve_static(path: str) -> flask.ResponseReturnValue:
    """Serve static directory."""
    return send_from_directory("../static", path)


@app.post("/fire")
def fire() -> flask.ResponseReturnValue:
    fireplace.fire_now()
    return ("", 204)


@app.post("/stop")
def stop() -> flask.ResponseReturnValue:
    fireplace.disable()
    return ("", 204)


@app.get("/temperature")
def get_temperature() -> flask.ResponseReturnValue:
    current = fireplace.current
    temperature = current.temperature if current is not None else float('nan')
    return ({"temperature": temperature}, 200)


def start():
    thread = threading.Thread(target=fireplace.loop, daemon=True)
    thread.start()
