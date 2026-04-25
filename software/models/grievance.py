from ..extensions import mongo
from bson import ObjectId
from datetime import datetime
import uuid


class Grievance:
    """
    Matches ER Diagram: GRIEVANCE entity
    Fields: GrievanceID, Title, Description, Status, Priority,
            SubmissionDate, ResolutionDate, AttachmentPath,
            SubmittedByUserID, AssignedToUserID, CategoryID
    Statuses: pending | assigned | in_progress | resolved | closed | escalated
    """

    STATUSES = ['pending', 'assigned', 'in_progress', 'resolved', 'closed', 'escalated']

    @staticmethod
    def generate_grievance_id():
        """Process 2.3: Create unique Grievance ID like GRV-2026-001"""
        year = datetime.utcnow().year
        count = mongo.db.grievances.count_documents({}) + 1
        return f"GRV-{year}-{count:04d}"

    @staticmethod
    def submit(title, description, category_id, submitted_by, priority='medium', attachment_path=''):
        """FR-02: Grievance Submission"""
        grievance_id = Grievance.generate_grievance_id()
        doc = {
            'grievance_id': grievance_id,
            'title': title,
            'description': description,
            'status': 'pending',
            'priority': priority,
            'submission_date': datetime.utcnow(),
            'resolution_date': None,
            'attachment_path': attachment_path,
            'submitted_by': ObjectId(submitted_by),
            'assigned_to': None,
            'category_id': ObjectId(category_id) if category_id else None,
            'dept_id': None,
            'resolution_notes': '',
            'is_escalated': False,
        }
        result = mongo.db.grievances.insert_one(doc)
        return grievance_id, str(result.inserted_id)

    @staticmethod
    def get_by_user(user_id):
        """FR-03: Student tracks their grievances"""
        return list(mongo.db.grievances.find(
            {'submitted_by': ObjectId(user_id)}
        ).sort('submission_date', -1))

    @staticmethod
    def get_all(filters=None):
        """FR-04: Admin views all grievances with optional filters"""
        query = filters or {}
        return list(mongo.db.grievances.find(query).sort('submission_date', -1))

    @staticmethod
    def get_by_id(grievance_mongo_id):
        try:
            return mongo.db.grievances.find_one({'_id': ObjectId(grievance_mongo_id)})
        except Exception:
            return None

    @staticmethod
    def get_by_grievance_id(grievance_id):
        return mongo.db.grievances.find_one({'grievance_id': grievance_id})

    @staticmethod
    def assign(grievance_mongo_id, staff_id, dept_id):
        """Process 3.0: Admin assigns grievance to staff"""
        mongo.db.grievances.update_one(
            {'_id': ObjectId(grievance_mongo_id)},
            {'$set': {
                'assigned_to': ObjectId(staff_id),
                'dept_id': ObjectId(dept_id) if dept_id else None,
                'status': 'assigned'
            }}
        )

    @staticmethod
    def update_status(grievance_mongo_id, status, resolution_notes=''):
        from bson import ObjectId
        from datetime import datetime
        from ..extensions import mongo

        status = status.lower()

        update = {
            'status': status,
            'updated_at': datetime.utcnow()
        }

        if status == 'resolved':
            update['resolution_date'] = datetime.utcnow()
            update['resolution_notes'] = resolution_notes

        mongo.db.grievances.update_one(
            {'_id': ObjectId(grievance_mongo_id)},
            {'$set': update}
        )

    @staticmethod
    def escalate_overdue(sla_days=3):
        """FR-05: Auto-escalate grievances older than SLA_DAYS"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=sla_days)
        overdue = mongo.db.grievances.find({
            'status': {'$in': ['pending', 'assigned']},
            'submission_date': {'$lt': cutoff},
            'is_escalated': False
        })
        escalated = []
        for g in overdue:
            mongo.db.grievances.update_one(
                {'_id': g['_id']},
                {'$set': {'status': 'escalated', 'is_escalated': True}}
            )
            # Log to ESCALATION_LOG (ER Diagram entity)
            mongo.db.escalation_log.insert_one({
                'grievance_id': g['_id'],
                'escalation_level': 1,
                'escalation_date': datetime.utcnow(),
                'escalated_to_user_id': None,  # department head
            })
            escalated.append(g)
        return escalated

    @staticmethod
    def get_dashboard_stats():
        """Process 6.0: Admin dashboard statistics"""
        total = mongo.db.grievances.count_documents({})
        pending = mongo.db.grievances.count_documents({'status': 'pending'})
        resolved = mongo.db.grievances.count_documents({'status': 'resolved'})
        escalated = mongo.db.grievances.count_documents({'status': 'escalated'})
        assigned = mongo.db.grievances.count_documents({'status': 'assigned'})
        in_progress = mongo.db.grievances.count_documents({'status': 'in_progress'})

        # Category-wise breakdown
        pipeline = [
            {'$group': {'_id': '$category_id', 'count': {'$sum': 1}}}
        ]
        category_stats = list(mongo.db.grievances.aggregate(pipeline))

        return {
            'total': total,
            'pending': pending,
            'resolved': resolved,
            'escalated': escalated,
            'assigned': assigned,
            'in_progress': in_progress,
            'category_stats': category_stats,
        }

    @staticmethod
    def get_assigned_to_staff(staff_id):
        return list(mongo.db.grievances.find(
            {'assigned_to': ObjectId(staff_id)}
        ).sort('submission_date', -1))
