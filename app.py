import os
import socket
from flask import Flask, render_template, request, send_file, Response, redirect, url_for, session, flash
from config import Config
from models import db, Media
# from crawler import crawler # Disabled for Librarian Mode
from librarian import librarian

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Ensure directories exist
os.makedirs(app.config['DOWNLOAD_DIR'], exist_ok=True)
os.makedirs(app.config['LIBRARY_DIR'], exist_ok=True)
os.makedirs(os.path.join(app.config['STATIC_DIR'], 'posters'), exist_ok=True)

# --- Network Logic ---
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

# --- Routes ---

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # Fetch all media ordered by ID desc (newest first)
    library = Media.query.order_by(Media.id.desc()).all()
    return render_template('dashboard.html', library=library)
    
@app.route('/play/<int:media_id>')
def play(media_id):
    media = Media.query.get_or_404(media_id)
    return render_template('player.html', media=media)

# @app.route('/login')
# def login():
#     if crawler.is_authorized():
#         return redirect(url_for('dashboard'))
#     # Trigger QR generation if not already running
#     crawler.start_qr_login()
#     return render_template('login_qr.html')

# API routes for QR (disabled)
# @app.route('/api/qr_code')
# def api_qr_code():
#     import qrcode
#     from io import BytesIO
    
#     url = crawler.get_qr_url()
#     if not url:
#         return Response("Loading...", status=202) # 202 Accepted (Processing)
        
#     img = qrcode.make(url)
#     img_io = BytesIO()
#     img.save(img_io, 'PNG')
#     img_io.seek(0)
#     return send_file(img_io, mimetype='image/png')

# @app.route('/api/check_auth')
# def check_auth():
#     if crawler.is_authorized():
#         return {'authenticated': True}
#     return {'authenticated': False}

@app.route('/api/scan', methods=['POST'])
def scan_library():
    result = librarian.scan_and_organize()
    flash(result)
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    crawler.logout()
    # Redirect to dashboard as login is disabled
    return redirect(url_for('dashboard'))

@app.route('/stream/<path:filename>')
def stream(filename):
    # Streaming from Downloads directly (Simplified for now)
    # Ideally should differentiate between library paths
    return send_file(os.path.join(app.config['DOWNLOAD_DIR'], filename))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)
