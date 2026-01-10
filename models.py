from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(4))
    file_path = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.String(20)) # 'movie' or 'episode'
    
    # Metadata
    tmdb_id = db.Column(db.Integer)
    overview = db.Column(db.Text)
    poster_path = db.Column(db.String(200)) # Local path to poster image
    backdrop_path = db.Column(db.String(200))
    
    # TV Specific
    series_title = db.Column(db.String(100))
    season_number = db.Column(db.Integer)
    episode_number = db.Column(db.Integer)

    def __repr__(self):
        return f'<Media {self.title}>'

class MediaFolder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(500), nullable=False, unique=True)
    folder_type = db.Column(db.String(20), default='watch') # 'watch' or 'import'

    def __repr__(self):
        return f'<MediaFolder {self.path}>'
