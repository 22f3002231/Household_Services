from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated and current_user.user_type == "customer":
        return redirect(url_for('customer.dashboard'))
    if current_user.is_authenticated and current_user.user_type == "professional":
        return redirect(url_for('professional.dashboard'))
    if current_user.is_authenticated and current_user.user_type == "admin":
        return redirect(url_for('admin.dashboard'))
    return render_template('index.html')
