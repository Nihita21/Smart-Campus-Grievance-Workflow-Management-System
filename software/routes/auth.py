from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from ..models.user import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')

        # Validation
        if not all([name, email, phone, password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if User.find_by_email(email):
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        # Only allow student/staff self-registration
        if role not in ['student', 'staff']:
            role = 'student'

        User.create(name, email, phone, password, role)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user_doc = User.find_by_email(email)

        if not user_doc:
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html')

        # NFR 4.3: Check if account is locked
        if user_doc.get('is_locked'):
            lock_until = user_doc.get('lock_until')
            if lock_until and datetime.utcnow() < lock_until:
                flash('Account locked for 15 minutes due to too many failed attempts.', 'danger')
                return render_template('auth/login.html')
            else:
                User.reset_failed_attempts(email)
                user_doc = User.find_by_email(email)

        if not User.verify_password(user_doc, password):
            User.increment_failed_attempts(email)
            attempts = user_doc.get('failed_attempts', 0) + 1
            remaining = max(0, 5 - attempts)
            flash(f'Invalid email or password. {remaining} attempts remaining.', 'danger')
            return render_template('auth/login.html')

        # Success
        User.reset_failed_attempts(email)
        user_obj = User(user_doc)
        login_user(user_obj)

        # Role-based redirect
        role = user_doc.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'staff':
            return redirect(url_for('staff.dashboard'))
        elif role == 'department_head':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
