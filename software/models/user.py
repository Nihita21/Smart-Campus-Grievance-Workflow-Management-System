from flask_login import UserMixin
from ..extensions import mongo, login_manager
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin):
    """
    Matches ER Diagram: USER entity
    Fields: UserID, Name, Email, Phone, PasswordHash, Role, ProfilePicture, CreatedAt, DeptID
    Roles: student | admin | staff | department_head
    """

    def __init__(self, user_doc):
        self._id = str(user_doc['_id'])
        self.name = user_doc.get('name', '')
        self.email = user_doc.get('email', '')
        self.phone = user_doc.get('phone', '')
        self.role = user_doc.get('role', 'student')
        self.dept_id = user_doc.get('dept_id')
        self.profile_picture = user_doc.get('profile_picture', '')
        self.created_at = user_doc.get('created_at', datetime.utcnow())
        self.is_locked = user_doc.get('is_locked', False)
        self.failed_attempts = user_doc.get('failed_attempts', 0)
        self.lock_until = user_doc.get('lock_until')

    def get_id(self):
        return self._id

    @staticmethod
    def create(name, email, phone, password, role='student', dept_id=None):
        """Register a new user (FR-01)"""
        user_doc = {
            'name': name,
            'email': email,
            'phone': phone,
            'password_hash': generate_password_hash(password),
            'role': role,
            'dept_id': dept_id,
            'profile_picture': '',
            'created_at': datetime.utcnow(),
            'is_locked': False,
            'failed_attempts': 0,
            'lock_until': None,
        }
        result = mongo.db.users.insert_one(user_doc)
        return str(result.inserted_id)

    @staticmethod
    def find_by_email(email):
        return mongo.db.users.find_one({'email': email})

    @staticmethod
    def find_by_id(user_id):
        try:
            return mongo.db.users.find_one({'_id': ObjectId(user_id)})
        except Exception:
            return None

    @staticmethod
    def verify_password(user_doc, password):
        return check_password_hash(user_doc['password_hash'], password)

    @staticmethod
    def increment_failed_attempts(email):
        """Security requirement: lock after 5 failed attempts (NFR 4.3)"""
        from datetime import timedelta
        user = mongo.db.users.find_one({'email': email})
        if not user:
            return
        attempts = user.get('failed_attempts', 0) + 1
        update = {'failed_attempts': attempts}
        if attempts >= 5:
            update['is_locked'] = True
            update['lock_until'] = datetime.utcnow() + timedelta(minutes=15)
        mongo.db.users.update_one({'email': email}, {'$set': update})

    @staticmethod
    def reset_failed_attempts(email):
        mongo.db.users.update_one(
            {'email': email},
            {'$set': {'failed_attempts': 0, 'is_locked': False, 'lock_until': None}}
        )

    @staticmethod
    def all_staff():
        return list(mongo.db.users.find({'role': 'staff'}))

    @staticmethod
    def all_users():
        return list(mongo.db.users.find())


@login_manager.user_loader
def load_user(user_id):
    doc = User.find_by_id(user_id)
    return User(doc) if doc else None
