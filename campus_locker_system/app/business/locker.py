from app import db

class Locker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(50), nullable=False)  # e.g., 'small', 'medium', 'large'
    # Possible statuses: 'free', 'occupied', 'out_of_service', 'disputed_contents', 'awaiting_collection'
    status = db.Column(db.String(50), nullable=False, default='free')
    parcels = db.relationship('Parcel', backref='locker', lazy=True)

    def __repr__(self):
        return f'<Locker {self.id} ({self.size}) - {self.status}>' 