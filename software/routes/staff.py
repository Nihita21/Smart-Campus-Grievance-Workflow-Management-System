from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps

from ..models.grievance import Grievance
from ..models.models import Category, Notification

staff_bp = Blueprint('staff', __name__)


# 🔒 Role check
def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['staff', 'admin']:
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# 🔷 Dashboard
@staff_bp.route('/dashboard')
@login_required
@staff_required
def dashboard():
    grievances = Grievance.get_assigned_to_staff(current_user._id)

    # attach category names
    for g in grievances:
        cat = Category.get_by_id(str(g.get('category_id'))) if g.get('category_id') else None
        g['category_name'] = cat['name'] if cat else 'N/A'

    # 🔥 FIX: stats added
    stats = {
        'total': len(grievances),
        'pending': sum(1 for g in grievances if g['status'] == 'assigned'),
        'in_progress': sum(1 for g in grievances if g['status'] == 'in_progress'),
        'resolved': sum(1 for g in grievances if g['status'] == 'resolved'),
    }

    return render_template(
        'staff/dashboard.html',
        grievances=grievances,
        stats=stats
    )


# 🔷 View grievance
@staff_bp.route('/grievance/<grievance_id>')
@login_required
@staff_required
def view_grievance(grievance_id):
    g = Grievance.get_by_id(grievance_id)

    if not g:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('staff.dashboard'))

    # attach category
    cat = Category.get_by_id(str(g.get('category_id'))) if g.get('category_id') else None
    g['category_name'] = cat['name'] if cat else 'N/A'

    return render_template('staff/view_grievance.html', g=g)


# 🔷 Update / Resolve grievance
@staff_bp.route('/update/<grievance_id>', methods=['POST'])
@login_required
@staff_required
def update_status(grievance_id):
    status = request.form.get('status')
    resolution_notes = request.form.get('resolution_notes')

    if status not in Grievance.STATUSES:
        flash('Invalid status.', 'danger')
        return redirect(url_for('staff.view_grievance', grievance_id=grievance_id))

    g = Grievance.get_by_id(grievance_id)

    # 🔥 update DB
    Grievance.update_status(grievance_id, status, resolution_notes)

    # 🔔 notify student
    if g:
        msg = f"Your grievance is now {status.upper()}."
        Notification.create(str(g['submitted_by']), grievance_id, msg)

    flash('Status updated successfully.', 'success')
    return redirect(url_for('staff.dashboard'))