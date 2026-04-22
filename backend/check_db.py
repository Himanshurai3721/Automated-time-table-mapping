from app import app, db, Subject

with app.app_context():
    try:
        subjects = Subject.query.all()
        print(f"Found {len(subjects)} subjects.")
        for s in subjects:
            print(s.to_dict())
    except Exception as e:
        print(f"Error: {e}")
