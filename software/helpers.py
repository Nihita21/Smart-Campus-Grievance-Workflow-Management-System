import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'png', 'jpg', 'jpeg', 'docx'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def save_attachment(file):
    """Save uploaded file and return relative path"""
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(upload_folder, filename))
    return f"uploads/{filename}"


def format_datetime(dt):
    if dt is None:
        return 'N/A'
    return dt.strftime('%d %b %Y, %I:%M %p')


def status_badge(status):
    badges = {
        'pending': 'warning',
        'assigned': 'info',
        'in_progress': 'primary',
        'resolved': 'success',
        'closed': 'secondary',
        'escalated': 'danger',
    }
    return badges.get(status, 'light')
