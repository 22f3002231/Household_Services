from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

auth_bp = Blueprint('auth', 
                    __name__, 
                    url_prefix='/auth')







@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', 'warning')
            return redirect(url_for('auth.register'))

        new_user = User(name=name, email=email, password=generate_password_hash(password), user_type=user_type)
        if user_type == 'customer':
            new_user.is_approved = True
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        if user_type == 'professional':
            return redirect(url_for('professional.setup'))
        else:
            flash('Registration successful, Welcome', 'success')
            return redirect(url_for('customer.dashboard'))

    return render_template('auth/register.html')






@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if user.is_blocked:
                flash('Your account has been blocked. Please contact the administrator.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user)
            if user.user_type == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.user_type == 'customer':
                 return redirect(url_for('customer.dashboard'))
            elif user.user_type == 'professional' and not user.is_approved:
                flash('Your account is pending approval. Please wait for admin verification.', 'info')
                return redirect(url_for('auth.login'))
            else:
                return redirect(url_for('professional.dashboard'))
        else:
            flash('Invalid email or password','warning')

    return render_template('auth/login.html')






@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))