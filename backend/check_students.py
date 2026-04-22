from app import app, db, Student

with app.app_context():
    try:
        students = Student.query.all()
        print(f"Found {len(students)} students.")
        for s in students:
            print(s.to_dict())
    except Exception as e:
        print(f"Error: {e}")
