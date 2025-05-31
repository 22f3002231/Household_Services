from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models import ServiceRequest, User, Review, ProfessionalProfile, Service
from werkzeug.utils import secure_filename
import os
from sqlalchemy import func
from sqlalchemy.orm import joinedload



professional_bp = Blueprint('professional', 
                            __name__, 
                            url_prefix='/professional')



@professional_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != 'professional':
        flash('Access denied. This page is for professionals only.', 'danger')
        return redirect(url_for('main.index'))
    
    pending_requests = ServiceRequest.query.filter_by(professional_id=current_user.id, status='pending').count()
    accepted_requests = ServiceRequest.query.filter_by(professional_id=current_user.id, status='accepted').count()
    completed_requests = ServiceRequest.query.filter_by(professional_id=current_user.id, status='completed').count()
   
    
    average_rating = db.session.query(func.avg(Review.rating)).filter_by(
        professional_id=current_user.id
    ).scalar() or 0
    
    return render_template('professional/dashboard.html', 
                           pending_requests=pending_requests,
                           accepted_requests=accepted_requests,
                           completed_requests=completed_requests,
                           average_rating=average_rating)




@professional_bp.route('/service_requests/<status>')
@login_required
def service_requests(status):
    if current_user.user_type != 'professional':
        flash('Access denied. This page is for professionals only.', 'danger')
        return redirect(url_for('main.index'))
    
    valid_statuses = ['pending', 'accepted', 'completed']
    if status not in valid_statuses:
        flash('Invalid status.', 'danger')
        return redirect(url_for('professional.dashboard'))
    
    requests = ServiceRequest.query.filter_by(professional_id=current_user.id, status=status).options(
        db.joinedload(ServiceRequest.customer),
        db.joinedload(ServiceRequest.service)
    ).all()
    return render_template('professional/service_requests.html', requests=requests, status=status)






@professional_bp.route('/reviews')
@login_required
def reviews():
    if current_user.user_type != 'professional':
        flash('Access denied. This page is for professionals only.', 'danger')
        return redirect(url_for('main.index'))
    
    reviews = Review.query.filter_by(professional_id=current_user.id).options(
        joinedload(Review.reviewer)
    ).order_by(Review.created_at.desc()).all()
    return render_template('professional/reviews.html', reviews=reviews)






@professional_bp.route('/profile')
@login_required
def profile():
    if current_user.user_type != 'professional':
        flash('Access denied. This page is for professionals only.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('professional/profile.html', professional=current_user)






@professional_bp.route('/accept_request/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    if current_user.user_type != 'professional':
        flash('Access denied. This action is for professionals only.', 'danger')
        return redirect(url_for('main.index'))
    
    service_request = ServiceRequest.query.get_or_404(request_id)
    if service_request.professional_id != current_user.id:
        flash('You are not authorized to accept this request.', 'danger')
        return redirect(url_for('professional.dashboard'))
    
    service_request.status = 'accepted'
    db.session.commit()
    flash('Service request accepted successfully!', 'success')
    return redirect(url_for('professional.dashboard'))






@professional_bp.route('/reject_request/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    if current_user.user_type != 'professional':
        flash('Access denied. This action is for professionals only.', 'danger')
        return redirect(url_for('main.index'))
    
    service_request = ServiceRequest.query.get_or_404(request_id)
    if service_request.professional_id != current_user.id:
        flash('You are not authorized to reject this request.', 'danger')
        return redirect(url_for('professional.dashboard'))
    
    service_request.status = 'rejected'
    db.session.commit()
    flash('Service request rejected successfully!', 'success')
    return redirect(url_for('professional.dashboard'))





@professional_bp.route('/complete_request/<int:request_id>', methods=['POST'])
@login_required
def complete_request(request_id):
    if current_user.user_type != 'professional':
        flash('Access denied. This action is for professionals only.', 'danger')
        return redirect(url_for('main.index'))
    
    service_request = ServiceRequest.query.get_or_404(request_id)
    if service_request.professional_id != current_user.id:
        flash('You are not authorized to complete this request.', 'danger')
        return redirect(url_for('professional.dashboard'))
    
    service_request.status = 'completed'
    service_request.completion_status = True
    db.session.commit()
    flash('Service request completed successfully!', 'success')
    return redirect(url_for('professional.dashboard'))





@professional_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if current_user.user_type != 'professional':
        flash('Access denied. This page is for professionals only.', 'danger')
        return redirect(url_for('main.index'))

    services = Service.query.all()

    if request.method == 'POST':
        phone = request.form['phone']
        address = request.form['address']
        profession = request.form['profession']
        experience = request.form['experience']
        portfolio = request.form['portfolio']
        service_pincode = request.form['servicePincode']
        selected_services = request.form.getlist('services')

        identity_proof = request.files['identityProof']
        address_proof = request.files['addressProof']
        professional_cert = request.files.get('professionalCert')
        professional_photo = request.files['professionalPhoto']

        identity_proof_filename = secure_filename(identity_proof.filename)
        address_proof_filename = secure_filename(address_proof.filename)
        professional_cert_filename = secure_filename(professional_cert.filename) if professional_cert else None
        professional_photo_filename = secure_filename(professional_photo.filename)

        identity_proof.save(os.path.join(current_app.config['UPLOAD_FOLDER'], identity_proof_filename))
        address_proof.save(os.path.join(current_app.config['UPLOAD_FOLDER'], address_proof_filename))
        if professional_cert:
            professional_cert.save(os.path.join(current_app.config['UPLOAD_FOLDER'], professional_cert_filename))
        professional_photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], professional_photo_filename))

        profile = ProfessionalProfile(
            user_id=current_user.id,
            phone=phone,
            address=address,
            profession=profession,
            experience=experience,
            portfolio=portfolio,
            service_pincode=service_pincode,
            identity_proof=identity_proof_filename,
            address_proof=address_proof_filename,
            professional_cert=professional_cert_filename,
            professional_photo=professional_photo_filename
        )

        for service_id in selected_services:
            service = Service.query.get(service_id)
            if service:
                profile.services.append(service)

        db.session.add(profile)
        db.session.commit()

        flash('Professional profile setup completed successfully. Please wait for admin approval.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('professional/setup.html', services=services)