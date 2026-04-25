from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..models.grievance import Grievance
from ..models.models import Category, Notification, Feedback
from ..helpers import allowed_file, save_attachment
import os

student_bp = Blueprint('student', __name__)


def student_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['student']:
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/dashboard')
@login_required
def dashboard():
    grievances = Grievance.get_by_user(current_user._id)
    notifications = Notification.get_for_user(current_user._id)
    unread = Notification.unread_count(current_user._id)
    stats = {
        'total': len(grievances),
        'pending': sum(1 for g in grievances if g['status'] == 'pending'),
        'resolved': sum(1 for g in grievances if g['status'] == 'resolved'),
        'escalated': sum(1 for g in grievances if g['status'] == 'escalated'),
    }
    return render_template('student/dashboard.html',
                           grievances=grievances, stats=stats,
                           notifications=notifications, unread=unread)


@student_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_grievance():
    """FR-02: Grievance Submission"""
    categories = Category.all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', '')
        priority = request.form.get('priority', 'medium')

        # FR-02 validation: description cannot be empty
        if not description:
            flash('Description cannot be empty.', 'danger')
            return render_template('student/submit.html', categories=categories)
        if not title:
            flash('Title is required.', 'danger')
            return render_template('student/submit.html', categories=categories)

        # Handle file attachment
        attachment_path = ''
        file = request.files.get('attachment')
        if file and file.filename:
            if allowed_file(file.filename):
                attachment_path = save_attachment(file)
            else:
                flash('Invalid file type. Allowed: pdf, png, jpg, jpeg, docx.', 'warning')

        grievance_id, _ = Grievance.submit(
            title=title,
            description=description,
            category_id=category_id if category_id else None,
            submitted_by=current_user._id,
            priority=priority,
            attachment_path=attachment_path
        )

        # Notify student
        g = Grievance.get_by_grievance_id(grievance_id)
        if g:
            Notification.create(
                current_user._id, str(g['_id']),
                f"Your grievance {grievance_id} has been submitted and is pending review."
            )

        flash(f'Grievance submitted successfully! Your ID: {grievance_id}', 'success')
        return redirect(url_for('student.my_grievances'))

    return render_template('student/submit.html', categories=categories)


@student_bp.route('/grievances')
@login_required
def my_grievances():
    """FR-03: Student tracks grievances"""
    grievances = Grievance.get_by_user(current_user._id)
    return render_template('student/grievances.html', grievances=grievances)


@student_bp.route('/grievance/<grievance_id>')
@login_required
def view_grievance(grievance_id):
    g = Grievance.get_by_id(grievance_id)
    if not g or str(g['submitted_by']) != current_user._id:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('student.my_grievances'))
    feedback = Feedback.get_for_grievance(grievance_id)
    return render_template('student/view_grievance.html', g=g, feedback=feedback)


@student_bp.route('/feedback/<grievance_id>', methods=['POST'])
@login_required
def submit_feedback(grievance_id):
    """UC-09: Submit Feedback"""
    g = Grievance.get_by_id(grievance_id)
    if not g or g['status'] != 'resolved':
        flash('Feedback can only be given for resolved grievances.', 'warning')
        return redirect(url_for('student.my_grievances'))
    rating = request.form.get('rating', 3)
    comments = request.form.get('comments', '')
    Feedback.submit(grievance_id, current_user._id, rating, comments)
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('student.view_grievance', grievance_id=grievance_id))


@student_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.get_for_user(current_user._id)
    for n in notifs:
        Notification.mark_read(str(n['_id']))
    return render_template('student/notifications.html', notifications=notifs)
