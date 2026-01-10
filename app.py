import os
import socket
from flask import Flask, render_template, request, send_file, Response
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Ensure directories exist
os.makedirs(app.config['DOWNLOAD_DIR'], exist_ok=True)
os.makedirs(app.config['LIBRARY_DIR'], exist_ok=True)
os.makedirs(os.path.join(app.config['STATIC_DIR'], 'posters'), exist_ok=True)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.route('/')
def dashboard():
    return "<h1>Conduit Dashboard - Work in Progress</h1>"

@app.route('/stream/<path:filename>')
def stream(filename):
    return "Stream placeholder"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)
