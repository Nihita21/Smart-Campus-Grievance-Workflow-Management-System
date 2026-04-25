from ..extensions import mongo
from bson import ObjectId
from datetime import datetime


class Category:
    """ER Diagram: CATEGORY entity - CategoryID, CategoryName, DefaultDeptID, SLA_Days"""

    @staticmethod
    def all():
        return list(mongo.db.categories.find())

    @staticmethod
    def get_by_id(cat_id):
        try:
            return mongo.db.categories.find_one({'_id': ObjectId(cat_id)})
        except Exception:
            return None

    @staticmethod
    def create(name, default_dept_id=None, sla_days=3):
        mongo.db.categories.insert_one({
            'category_name': name,
            'default_dept_id': ObjectId(default_dept_id) if default_dept_id else None,
            'sla_days': sla_days,
        })

    @staticmethod
    def seed_defaults():
        """Insert default categories if none exist"""
        if mongo.db.categories.count_documents({}) == 0:
            defaults = [
                {'category_name': 'Hostel', 'default_dept_id': None, 'sla_days': 3},
                {'category_name': 'Internet / Network', 'default_dept_id': None, 'sla_days': 2},
                {'category_name': 'Classroom Facilities', 'default_dept_id': None, 'sla_days': 3},
                {'category_name': 'Academic / Exam', 'default_dept_id': None, 'sla_days': 5},
                {'category_name': 'Library', 'default_dept_id': None, 'sla_days': 3},
                {'category_name': 'Other', 'default_dept_id': None, 'sla_days': 3},
            ]
            mongo.db.categories.insert_many(defaults)


class Department:
    """ER Diagram: DEPARTMENT entity - DeptID, DeptName, ContactEmail, DeptHeadUserID"""

    @staticmethod
    def all():
        return list(mongo.db.departments.find())

    @staticmethod
    def get_by_id(dept_id):
        try:
            return mongo.db.departments.find_one({'_id': ObjectId(dept_id)})
        except Exception:
            return None

    @staticmethod
    def create(name, contact_email, dept_head_user_id=None):
        mongo.db.departments.insert_one({
            'dept_name': name,
            'contact_email': contact_email,
            'dept_head_user_id': ObjectId(dept_head_user_id) if dept_head_user_id else None,
        })

    @staticmethod
    def seed_defaults():
        if mongo.db.departments.count_documents({}) == 0:
            defaults = [
                {'dept_name': 'Hostel Administration', 'contact_email': 'hostel@college.edu', 'dept_head_user_id': None},
                {'dept_name': 'IT / Network', 'contact_email': 'it@college.edu', 'dept_head_user_id': None},
                {'dept_name': 'Academic Affairs', 'contact_email': 'academic@college.edu', 'dept_head_user_id': None},
                {'dept_name': 'Infrastructure', 'contact_email': 'infra@college.edu', 'dept_head_user_id': None},
            ]
            mongo.db.departments.insert_many(defaults)


class Notification:
    """ER Diagram: NOTIFICATION entity - Process 5.0"""

    @staticmethod
    def create(user_id, grievance_id, message):
        mongo.db.notifications.insert_one({
            'user_id': ObjectId(user_id),
            'grievance_id': ObjectId(grievance_id),
            'message': message,
            'is_read': False,
            'created_at': datetime.utcnow(),
        })

    @staticmethod
    def get_for_user(user_id):
        return list(mongo.db.notifications.find(
            {'user_id': ObjectId(user_id)}
        ).sort('created_at', -1).limit(20))

    @staticmethod
    def mark_read(notification_id):
        mongo.db.notifications.update_one(
            {'_id': ObjectId(notification_id)},
            {'$set': {'is_read': True}}
        )

    @staticmethod
    def unread_count(user_id):
        return mongo.db.notifications.count_documents(
            {'user_id': ObjectId(user_id), 'is_read': False}
        )


class Feedback:
    """ER Diagram: FEEDBACK entity - UC-09: Submit Feedback"""

    @staticmethod
    def submit(grievance_id, user_id, rating, comments):
        mongo.db.feedback.update_one(
            {'grievance_id': ObjectId(grievance_id), 'user_id': ObjectId(user_id)},
            {'$set': {
                'grievance_id': ObjectId(grievance_id),
                'user_id': ObjectId(user_id),
                'rating': int(rating),
                'comments': comments,
                'submitted_at': datetime.utcnow(),
            }},
            upsert=True
        )

    @staticmethod
    def get_for_grievance(grievance_id):
        return mongo.db.feedback.find_one({'grievance_id': ObjectId(grievance_id)})
