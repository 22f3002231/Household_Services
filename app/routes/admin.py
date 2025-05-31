from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.models import *
from app.utils import admin_required
import os






admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/professionals')
@login_required
@admin_required
def dashboard():
    search_query = request.args.get('search', '')
    
    all_professionals = User.query.filter_by(user_type='professional').all()
    
    filtered_professionals = []
    for professional in all_professionals:
        if search_query.lower() in professional.name.lower() or search_query.lower() in professional.email.lower():
            filtered_professionals.append(professional)
    
    pending_professionals = []
    approved_professionals = []
    
    for professional in filtered_professionals:
        if professional.is_approved:
            approved_professionals.append(professional)
        else:
            pending_professionals.append(professional)
    
    for professional in approved_professionals:
        all_ratings = Review.query.filter_by(professional_id=professional.id).all()
        total_ratings = len(all_ratings)
        if total_ratings > 0:
            sum_ratings = sum([review.rating for review in all_ratings])
            professional.avg_rating = round(sum_ratings / total_ratings, 1)
        else:
            professional.avg_rating = None
    
    return render_template('admin/dashboard.html', 
                           pending_professionals=pending_professionals, 
                           approved_professionals=approved_professionals,
                           search_query=search_query)





@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.filter_by(user_type='customer').all()
    return render_template('admin/users.html', users=users)







@admin_bp.route('/services')
@login_required
@admin_required
def services():
    services = Service.query.all()
    return render_template('admin/services.html', services=services)







@admin_bp.route('/add_service', methods=['GET', 'POST'])
@login_required
@admin_required
def add_service():
    if request.method == 'POST':
        name = request.form['name']
        base_price = float(request.form['base_price'])
        description = request.form['description']
        
        new_service = Service(name=name, base_price=base_price, description=description)
        db.session.add(new_service)
        db.session.commit()
        
        flash('New service added successfully.', 'success')
        return redirect(url_for('admin.services'))
    
    return render_template('admin/add_service.html')








@admin_bp.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    if request.method == 'POST':
        service.name = request.form['name']
        service.base_price = float(request.form['base_price'])
        service.description = request.form['description']
        db.session.commit()
        flash('Service updated successfully.', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/edit_service.html', service=service)







@admin_bp.route('/delete_service/<int:service_id>', methods=['POST'])
@login_required
@admin_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully.', 'success')
    return redirect(url_for('admin.services'))








@admin_bp.route('/block_user/<int:user_id>')
@login_required
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blocked = not user.is_blocked
    db.session.commit()
    flash(f"User {user.name} has been {'blocked' if user.is_blocked else 'unblocked'}.", 'success')
    return redirect(url_for('admin.users' if user.user_type == 'customer' else 'admin.dashboard'))











@admin_bp.route('/view_professional/<int:user_id>')
@login_required
@admin_required
def view_professional(user_id):
    user = User.query.get_or_404(user_id)
    if user.user_type != 'professional':
        abort(404)
    return render_template('admin/view_professional.html', professional=user)






@admin_bp.route('/approve_professional/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_professional(user_id):
    user = User.query.get_or_404(user_id)
    if user.user_type == 'professional':
        user.is_approved = True
        db.session.commit()
        flash(f"Professional {user.name} has been approved.", 'success')
    return redirect(url_for('admin.dashboard'))









@admin_bp.route('/reject_professional/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_professional(user_id):
    user = User.query.get_or_404(user_id)
    if user.user_type == 'professional':
        db.session.delete(user)
        db.session.commit()
        flash(f"Professional {user.name} has been rejected and removed from the system.", 'warning')
    return redirect(url_for('admin.dashboard'))