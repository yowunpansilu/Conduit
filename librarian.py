import os
import shutil
import guessit
import tmdbsimple as tmdb
from config import Config

class Librarian:
    def __init__(self):
        self.download_dir = Config.DOWNLOAD_DIR or 'downloads'
        self.library_dir = Config.LIBRARY_DIR or 'library'
        
        # Configure TMDB
        if Config.TMDB_API_KEY:
            tmdb.API_KEY = Config.TMDB_API_KEY
        else:
            print("Librarian: Warning - TMDB_API_KEY not set. Metadata fetching will be skipped.")

    def scan_and_organize(self):
        """Scans the download directory and organizes video files."""
        print(f"Librarian: Scanning {self.download_dir}...")
        moved_count = 0
        
        for root, dirs, files in os.walk(self.download_dir):
            for file in files:
                if self._is_video_file(file):
                    success = self._process_file(os.path.join(root, file))
                    if success:
                        moved_count += 1
        
        return f"Scanned complete. Organized {moved_count} files."

    def _is_video_file(self, filename):
        video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv'}
        return os.path.splitext(filename)[1].lower() in video_exts

    def _process_file(self, file_path):
        from app import app
        from models import db, Media
        
        filename = os.path.basename(file_path)
        guess = guessit.guessit(filename)
        
        title = guess.get('title')
        if not title:
            print(f"Librarian: Could not guess title for {filename}. Skipping.")
            return False

        year = guess.get('year')
        media_type = guess.get('type', 'movie')
        
        # --- Metadata Fetching ---
        poster_path = None
        overview = None
        tmdb_id = None
        
        if Config.TMDB_API_KEY:
            try:
                search = tmdb.Search()
                if media_type == 'episode':
                    response = search.tv(query=title, year=year)
                else:
                    response = search.movie(query=title, year=year)
                    
                if search.results:
                    top_result = search.results[0]
                    tmdb_id = top_result['id']
                    overview = top_result['overview']
                    if top_result.get('poster_path'):
                        # Download Poster
                        poster_url = f"https://image.tmdb.org/t/p/w500{top_result['poster_path']}"
                        local_poster = f"poster_{tmdb_id}.jpg"
                        poster_save_path = os.path.join(Config.STATIC_DIR, 'posters', local_poster)
                        
                        import requests
                        with open(poster_save_path, 'wb') as f:
                            f.write(requests.get(poster_url).content)
                        poster_path = f"posters/{local_poster}"
                        print(f"Librarian: Downloaded poster for {title}")
            except Exception as e:
                print(f"Librarian: TMDB Error for {title}: {e}")

        # --- DB Entry ---
        with app.app_context():
            # Check if exists
            exists = Media.query.filter_by(file_path=filename).first()
            if not exists:
                media = Media(
                    title=title,
                    year=str(year) if year else None,
                    file_path=filename, # We keep it in downloads for now to simplify
                    media_type=media_type,
                    tmdb_id=tmdb_id,
                    overview=overview,
                    poster_path=poster_path
                )
                db.session.add(media)
                db.session.commit()
                print(f"Librarian: Saved {title} to Database.")
                return True
        return False

librarian = Librarian()
