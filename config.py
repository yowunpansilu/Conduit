import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TG_API_ID = os.environ.get('TG_API_ID')
    TG_API_HASH = os.environ.get('TG_API_HASH')
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_please_change'
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR') or os.path.join(BASE_DIR, 'downloads')
    LIBRARY_DIR = os.environ.get('LIBRARY_DIR') or os.path.join(BASE_DIR, 'library')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
