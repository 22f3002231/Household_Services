from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Service, ServiceRequest, User, Review, ProfessionalProfile, professional_services
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from datetime import datetime

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != 'customer':
        flash('Access denied. This page is for customers only.', 'danger')
        return redirect(url_for('main.index'))
    
    search_query = request.args.get('search', '')
    if search_query:
        services = Service.query.filter(Service.name.ilike(f'%{search_query}%')).all()
    else:
        services = Service.query.all()
    return render_template('customer/dashboard.html', services=services, search_query=search_query)





@customer_bp.route('/service/<int:service_id>')
@login_required
def service_details(service_id):
    
    if current_user.user_type != 'customer':
        flash('Access denied. This page is for customers only.', 'danger')
        return redirect(url_for('main.index'))
    
    service = Service.query.get_or_404(service_id)
    professionals = User.query.filter_by(user_type='professional', is_approved=True).all()
    
    service_professionals = []
    
    for professional in professionals:
        if service in professional.professional_profile.services:
            reviews = Review.query.filter_by(professional_id=professional.id).all()
            if reviews:
                total_rating = sum([review.rating for review in reviews])
                avg_rating = total_rating / len(reviews)
                professional.avg_review = round(avg_rating, 1)
            else:
                professional.avg_review = None
            
            service_professionals.append(professional)

    return render_template('customer/service_details.html', service=service, professionals=service_professionals)





@customer_bp.route('/book_service/<int:service_id>/<int:professional_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id, professional_id):
    if current_user.user_type != 'customer':
        flash('Access denied. This page is for customers only.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        date_of_service_str = request.form['date_of_service']
        try:
            date_of_service = datetime.strptime(date_of_service_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('customer.book_service', service_id=service_id, professional_id=professional_id))

        new_request = ServiceRequest(
            customer_id=current_user.id,
            professional_id=professional_id,
            service_id=service_id,
            date_of_service=date_of_service,
            pincode=request.form['pincode'],
            city=request.form['city']
        )
        
        db.session.add(new_request)
        db.session.commit()
        flash('Service request created successfully!', 'success')
        return redirect(url_for('customer.dashboard'))
    
    service = Service.query.get_or_404(service_id)
    professional = User.query.get_or_404(professional_id)
    return render_template('customer/book_service.html', service=service, professional=professional)






@customer_bp.route('/my_requests')
@login_required
def my_requests():
    if current_user.user_type != 'customer':
        flash('Access denied. This page is for customers only.', 'danger')
        return redirect(url_for('main.index'))
    
    requests = ServiceRequest.query.filter_by(customer_id=current_user.id).options(
        joinedload(ServiceRequest.service),
        joinedload(ServiceRequest.professional)
    ).order_by(ServiceRequest.date_of_request.desc()).all()
    
    db.session.expire_all()
    db.session.refresh(current_user)
    
    return render_template('customer/my_requests.html', requests=requests)





@customer_bp.route('/edit_request/<int:request_id>', methods=['GET', 'POST'])
@login_required
def edit_request(request_id):
    if current_user.user_type != 'customer':
        flash('Access denied. This page is for customers only.', 'danger')
        return redirect(url_for('main.index'))
    
    service_request = ServiceRequest.query.get_or_404(request_id)
    if service_request.customer_id != current_user.id:
        flash('You are not authorized to edit this request.', 'danger')
        return redirect(url_for('customer.my_requests'))
    
    if request.method == 'POST':
        try:
            service_request.date_of_service = datetime.strptime(request.form['date_of_service'], '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('customer.edit_request', request_id=request_id))
        
        service_request.remarks = request.form.get('remarks') or None

        db.session.commit()
        flash('Service request updated successfully!', 'success')
        return redirect(url_for('customer.my_requests'))
    
    return render_template('customer/edit_request.html', service_request=service_request)








@customer_bp.route('/delete_request/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):

    request = ServiceRequest.query.get_or_404(request_id)

    if request.customer_id != current_user.id:
        flash('You are not authorized to delete this request.', 'danger')
        return redirect(url_for('customer.my_requests'))
    

    if request.status != 'pending':
        flash('You can only delete pending service requests.', 'danger')
        return redirect(url_for('customer.my_requests'))
    
    try:
        db.session.delete(request)
        db.session.commit()
        
        flash('Service request deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the request.', 'danger')
    
    return redirect(url_for('customer.my_requests'))








@customer_bp.route('/close_request/<int:request_id>', methods=['POST'])
@login_required
def close_request(request_id):
    if current_user.user_type != 'customer':
        flash('Access denied. This page is for customers only.', 'danger')
        return redirect(url_for('main.index'))
    
    service_request = ServiceRequest.query.get_or_404(request_id)
    if service_request.customer_id != current_user.id:
        flash('You are not authorized to close this request.', 'danger')
        return redirect(url_for('customer.my_requests'))
    
    service_request.completion_status = True
    service_request.status = 'completed'
    db.session.commit()
    flash('Service request closed successfully!', 'success')
    return redirect(url_for('customer.my_requests'))






@customer_bp.route('/review/<int:request_id>', methods=['GET', 'POST'])
@login_required
def review(request_id):
    if current_user.user_type != 'customer':
        flash('Access denied. This page is for customers only.', 'danger')
        return redirect(url_for('main.index'))
    
    service_request = ServiceRequest.query.get_or_404(request_id)
    if service_request.customer_id != current_user.id:
        flash('You are not authorized to review this service.', 'danger')
        return redirect(url_for('customer.my_requests'))
    
    existing_review = Review.query.filter_by(service_request_id=request_id).first()
    if existing_review:
        flash('You have already reviewed this service request.', 'warning')
        return redirect(url_for('customer.my_requests'))
    
    if request.method == 'POST':
        new_review = Review(
            reviewer_id=current_user.id,
            professional_id=service_request.professional_id,
            service_request_id=service_request.id,
            rating=request.form['rating'],
            comment=request.form['comment']
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('customer.my_requests'))
    
    return render_template('customer/review.html', service_request=service_request)