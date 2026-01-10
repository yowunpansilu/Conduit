import os
import socket
from flask import Flask, render_template, request, send_file, Response, redirect, url_for, session, flash
from config import Config
from models import db, Media, MediaFolder
import wifi_utils
# from crawler import crawler # Disabled for Librarian Mode
from librarian import librarian

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create tables
with app.app_context():
    # db.drop_all() # Commented out to prevent data loss on every restart
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
    all_media = Media.query.order_by(Media.id.desc()).all()
    
    # Deduplicate by TMDB ID or Title
    unique_library = {}
    for item in all_media:
        # Key: Prefer TMDB ID, fallback to Title+Year
        if item.tmdb_id:
            key = f"tmdb_{item.tmdb_id}"
        else:
            key = f"title_{item.title}_{item.year}"
            
        # Only add if not exists (keeps the newest one due to order_by desc)
        if key not in unique_library:
            unique_library[key] = item
            
    return render_template('dashboard.html', library=unique_library.values())
    
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

@app.route('/settings')
def settings():
    folders = MediaFolder.query.all()
    # Attempt Wi-Fi Scan
    networks = wifi_utils.scan_networks()
    return render_template('settings.html', 
                         folders=folders, 
                         networks=networks, 
                         download_dir=app.config['DOWNLOAD_DIR'])

@app.route('/settings/folder/add', methods=['POST'])
def add_folder():
    path = request.form.get('path')
    if path and os.path.exists(path):
        # Security: Prevent adding root or system dirs
        abs_path = os.path.abspath(path)
        if abs_path == '/' or abs_path.startswith('/etc') or abs_path.startswith('/var'):
             flash("Security Warning: Cannot add system directories.")
             return redirect(url_for('settings'))

        if not MediaFolder.query.filter_by(path=path).first():
            folder = MediaFolder(path=path)
            db.session.add(folder)
            db.session.commit()
            flash(f"Added watch folder: {path}")
        else:
            flash("Folder already exists.")
    else:
        flash("Invalid path or folder does not exist.")
    return redirect(url_for('settings'))

@app.route('/settings/folder/delete', methods=['POST'])
def delete_folder():
    folder_id = request.form.get('folder_id')
    folder = MediaFolder.query.get(folder_id)
    if folder:
        db.session.delete(folder)
        db.session.commit()
        flash("Folder removed.")
    return redirect(url_for('settings'))

@app.route('/settings/wifi/connect', methods=['POST'])
def connect_wifi():
    ssid = request.form.get('ssid')
    password = request.form.get('password')
    success, msg = wifi_utils.connect_network(ssid, password)
    flash(msg)
    return redirect(url_for('settings'))

@app.route('/api/scan', methods=['POST'])
def scan_library():
    # Upgrade scan to include MediaFolders
    folders = [app.config['DOWNLOAD_DIR']]
    watch_folders = MediaFolder.query.all()
    for wf in watch_folders:
        folders.append(wf.path)
        
    result = librarian.scan_and_organize(folders)
    flash(result)
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    crawler.logout()
    # Redirect to dashboard as login is disabled
    return redirect(url_for('dashboard'))

# --- File Browser API ---
@app.route('/api/browse', methods=['POST'])
def browse_filesystem():
    """Lists directories for the folder picker modal."""
    data = request.json or {}
    current_path = data.get('path')

    # Default to Home Directory if no path provided
    if not current_path:
        current_path = os.path.expanduser("~")
    
    # Security/Sanity Check
    if not os.path.isdir(current_path):
        current_path = os.path.expanduser("~")

    folders = []
    try:
        # List only directories
        with os.scandir(current_path) as it:
            for entry in it:
                if entry.is_dir() and not entry.name.startswith('.'):
                    folders.append(entry.name)
        folders.sort()
    except PermissionError:
        flash("Permission denied for this folder.")
        
    parent_path = os.path.dirname(current_path)
    
    return {
        'current_path': current_path,
        'parent_path': parent_path if parent_path != current_path else None,
        'folders': folders
    }

# --- Security Utils ---
def is_safe_path(path):
    """Ensure path is within safe directories (Downloads or Watch Folders)."""
    # 1. Resolve absolute path
    abs_path = os.path.abspath(path)
    
    # 2. Collect allowed roots
    allowed_roots = [os.path.abspath(app.config['DOWNLOAD_DIR'])]
    with app.app_context():
        # We need to handle context if calling outside request, but here is fine
        try:
            for mf in MediaFolder.query.all():
                allowed_roots.append(os.path.abspath(mf.path))
        except:
            pass # DB might not be ready
            
    # 3. Check if path starts with any allowed root
    for root in allowed_roots:
        # commonpath check prevents traversal like /media/downloads/../../etc/passwd
        # by verifying the resolved path still shares the root prefix
        try:
            if os.path.commonpath([abs_path, root]) == root:
                return True
        except ValueError:
            continue # Paths on different drives (Windows)
            
    return False

# --- Helper: Resolve Path ---
def resolve_media_path(filename):
    """
    Attempts to resolve the filesystem path from the Flask route variable.
    Handles absolute paths, relative paths, and Flask's slash-stripping quirks.
    """
    candidates = []
    
    # 1. As-is (Absolute or Relative to CWD)
    candidates.append(filename)
    
    # 2. Relative to Download Directory
    candidates.append(os.path.join(app.config['DOWNLOAD_DIR'], filename))
    
    # 3. Re-constructed Absolute Path (if leading slash was stripped)
    # e.g. "Users/me/..." -> "/Users/me/..."
    candidates.append(os.path.abspath(os.path.join(os.path.sep, filename)))

    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
            
    return None

@app.route('/stream/<path:filename>')
def stream(filename):
    full_path = resolve_media_path(filename)
    
    if full_path and is_safe_path(full_path):
         return send_file(full_path)
    
    print(f"Stream Error: File not found or unsafe: {filename} -> {full_path}")
    return Response("Access Denied or File Not Found", status=403)

# --- VLC Transcoding Logic ---
@app.route('/stream/transcode/<path:filename>')
def stream_transcode(filename):
    """
    Uses local VLC to transcode non-browser-friendly files (MKV, AVI) to MP4 live.
    """
    full_path = resolve_media_path(filename)
        
    if not full_path or not is_safe_path(full_path):
        print(f"Transcode Error: File not found or unsafe: {filename} -> {full_path}")
        return Response("Access Denied", status=403)

    # 2. VLC Command
    # Detect Path based on OS
    import shutil
    vlc_cmd = shutil.which("cvlc") or shutil.which("vlc")
    
    # Fallback for macOS if not in PATH
    if not vlc_cmd and os.path.exists("/Applications/VLC.app/Contents/MacOS/VLC"):
        vlc_cmd = "/Applications/VLC.app/Contents/MacOS/VLC"
        
    if not vlc_cmd:
        print("Transcode Error: VLC not found on system.")
        return Response("VLC not found on server", status=500)
    
    cmd = [
        vlc_cmd,
        "-I", "dummy",          # No interface
        full_path,              # Input
        "--sout",               # Stream Output
        "#transcode{vcodec=h264,vb=1500,acodec=mp3,ab=128}:std{access=file,mux=mp4,dst=-}",
        "vlc://quit"            # Quit when done
    ]

    def generate():
        # Spawn VLC process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        try:
            # Stream stdout in chunks
            while True:
                data = process.stdout.read(4096)
                if not data:
                    break
                yield data
        finally:
            process.kill()

    return Response(generate(), mimetype='video/mp4')

# --- External Player Logic ---
@app.route('/open/vlc/<int:media_id>')
def open_in_vlc(media_id):
    """
    Generates an m3u playlist file to trigger external players (VLC).
    """
    media = Media.query.get_or_404(media_id)
    
    # Construct absolute URL for the stream
    stream_url = url_for('stream', filename=media.file_path, _external=True)
    
    # M3U Content
    m3u_content = f"#EXTM3U\n#EXTINF:-1,{media.title}\n{stream_url}"
    
    return Response(
        m3u_content,
        mimetype='audio/x-mpegurl',
        headers={'Content-Disposition': f'attachment;filename="{media.title}.m3u"'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)
