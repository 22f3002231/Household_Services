from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    professional_profile = db.relationship('ProfessionalProfile', backref='user', uselist=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class ProfessionalProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    profession = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    portfolio = db.Column(db.Text)
    service_pincode = db.Column(db.String(10), nullable=False)
    identity_proof = db.Column(db.String(200), nullable=False)
    address_proof = db.Column(db.String(200), nullable=False)
    professional_cert = db.Column(db.String(200))
    professional_photo = db.Column(db.String(200))
    services = db.relationship('Service', secondary='professional_services', backref='professionals')

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_of_request = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_of_service = db.Column(db.DateTime, nullable=False)
    date_of_completion = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    completion_status = db.Column(db.Boolean, default=False)
    remarks = db.Column(db.Text)
    pincode = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(100), nullable=False)

    service = db.relationship('Service', backref='service_requests')
    customer = db.relationship('User', foreign_keys=[customer_id], backref='customer_requests')
    professional = db.relationship('User', foreign_keys=[professional_id], backref='professional_requests')


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Consider adding a range validator
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_as_reviewer')
    professional = db.relationship('User', foreign_keys=[professional_id], backref='reviews_as_professional')
    service_request = db.relationship('ServiceRequest', backref='reviews')  # Updated to plural


professional_services = db.Table('professional_services',
    db.Column('professional_id', db.Integer, db.ForeignKey('professional_profile.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('service.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

