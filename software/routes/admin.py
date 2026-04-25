from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..models.grievance import Grievance
from ..models.user import User
from ..models.models import Category, Department, Notification
from bson import ObjectId

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'department_head']:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """FR-04: Admin dashboard with stats - Process 6.0"""
    stats = Grievance.get_dashboard_stats()
    grievances = Grievance.get_all()
    # Attach category names
    for g in grievances:
        if g.get('category_id'):
            cat = Category.get_by_id(str(g['category_id']))
            g['category_name'] = cat['name'] if cat else 'N/A'
        else:
            g['category_name'] = 'N/A'
    return render_template('admin/dashboard.html', stats=stats, grievances=grievances)


@admin_bp.route('/grievances')
@login_required
@admin_required
def all_grievances():
    """FR-04: Filter by category, status, date"""
    status = request.args.get('status', '')
    category_id = request.args.get('category_id', '')
    filters = {}
    if status:
        filters['status'] = status
    if category_id:
        try:
            filters['category_id'] = ObjectId(category_id)
        except Exception:
            pass

    grievances = Grievance.get_all(filters)
    categories = Category.all()
    staff_list = User.all_staff()

    for g in grievances:
        if g.get('category_id'):
            cat = Category.get_by_id(str(g['category_id']))
            g['category_name'] = cat['name'] if cat else 'N/A'
        else:
            g['category_name'] = 'N/A'

    return render_template('admin/grievances.html',
                           grievances=grievances,
                           categories=categories,
                           staff_list=staff_list,
                           selected_status=status,
                           selected_category=category_id)


@admin_bp.route('/grievance/<grievance_id>')
@login_required
@admin_required
def view_grievance(grievance_id):
    g = Grievance.get_by_id(grievance_id)
    if not g:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('admin.all_grievances'))
    staff_list = User.all_staff()
    departments = Department.all()
    categories = Category.all()
    cat = Category.get_by_id(str(g['category_id'])) if g.get('category_id') else None
    return render_template('admin/view_grievance.html',
                           g=g, staff_list=staff_list,
                           departments=departments,
                           category=cat)


@admin_bp.route('/assign/<grievance_id>', methods=['POST'])
@login_required
@admin_required
def assign_grievance(grievance_id):
    """Process 3.0: Assign grievance to staff"""
    staff_id = request.form.get('staff_id', '')
    dept_id = request.form.get('dept_id', '')

    if not staff_id:
        flash('Please select a staff member.', 'danger')
        return redirect(url_for('admin.view_grievance', grievance_id=grievance_id))

    g = Grievance.get_by_id(grievance_id)
    Grievance.assign(grievance_id, staff_id, dept_id if dept_id else None)

    # Notify assigned staff
    Notification.create(
        staff_id, grievance_id,
        f"Grievance {g.get('grievance_id', grievance_id)} has been assigned to you."
    )
    # Notify student
    if g:
        Notification.create(
            str(g['submitted_by']), grievance_id,
            f"Your grievance {g.get('grievance_id')} has been assigned to a staff member."
        )

    flash('Grievance assigned successfully.', 'success')
    return redirect(url_for('admin.view_grievance', grievance_id=grievance_id))


@admin_bp.route('/escalate_check')
@login_required
@admin_required
def escalate_check():
    """FR-05: Manually trigger escalation check"""
    from flask import current_app
    escalated = Grievance.escalate_overdue(current_app.config['SLA_DAYS'])
    flash(f'{len(escalated)} grievance(s) escalated.', 'info')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """UC-10: Generate Reports"""
    stats = Grievance.get_dashboard_stats()
    all_g = Grievance.get_all()
    categories = Category.all()
    cat_map = {str(c['_id']): c['name'] for c in categories}

    category_data = {}
    for g in all_g:
        cat_id = str(g.get('category_id', 'unknown'))
        cat_name = cat_map.get(cat_id, 'Uncategorized')
        category_data[cat_name] = category_data.get(cat_name, 0) + 1

    return render_template('admin/reports.html', stats=stats, category_data=category_data)


@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    """UC-11: Manage Users and Categories"""
    users = User.all_users()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/categories')
@login_required
@admin_required
def manage_categories():
    categories = Category.all()
    departments = Department.all()
    return render_template('admin/categories.html', categories=categories, departments=departments)


@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    name = request.form.get('name', '').strip()
    sla_days = int(request.form.get('sla_days', 3))
    if name:
        Category.create(name, sla_days=sla_days)
        flash(f'Category "{name}" added.', 'success')
    return redirect(url_for('admin.manage_categories'))
