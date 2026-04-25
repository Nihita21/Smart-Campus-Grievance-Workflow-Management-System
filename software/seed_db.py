"""
seed_db.py - Seeds the database with default data and demo users
Run: python -m software.seed_db
"""

from .app import create_app
from .extensions import mongo
from .models.user import User
from datetime import datetime

def seed_categories():
    categories = [
    "Academics",
    "Hostel",
    "Transport",
    "Library",
    "IT Services",
    "Attendance",
    "Examination",
    "Facilities"
    ]
    for cat in categories:
        if not mongo.db.categories.find_one({"name": cat}):
            mongo.db.categories.insert_one({
                "name": cat,
                "created_at": datetime.utcnow()
            })
            print(f"✔ Added category: {cat}")
        else:
            print(f"• Category exists: {cat}")

def seed_departments():
    departments = [
        "Computer Science",
        "Mechanical",
        "Electrical",
        "Civil",
        "Administration"
    ]


    for dept in departments:
        if not mongo.db.departments.find_one({"name": dept}):
            mongo.db.departments.insert_one({
                "name": dept,
                "created_at": datetime.utcnow()
            })
            print(f"✔ Added department: {dept}")
        else:
            print(f"• Department exists: {dept}")

def users():
    users = [
        {
    "name": "System Admin",
    "email": "admin@college.edu",
    "phone": "9999999999",
    "password": "Admin@123",
    "role": "admin"
    },
    {
    "name": "Demo Student",
    "email": "student@college.edu",
    "phone": "9876543210",
    "password": "Student@123",
    "role": "student"
    },
    {
    "name": "Staff Member",
    "email": "staff@college.edu",
    "phone": "9123456789",
    "password": "Staff@123",
    "role": "staff"
    }
    ]
    for user in users:
        if not User.find_by_email(user["email"]):
            User.create(**user)
            print(f"✔ Created user: {user['email']}")
        else:
            print(f"• User exists: {user['email']}")

def seed():
    app = create_app()


    with app.app_context():
        print("\n--- Seeding Database ---\n")

        seed_categories()
        seed_departments()
        users()

        print("\n✅ Database seeded successfully!\n")


if __name__ == "__main__":
    seed()