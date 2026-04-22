from app import app, db, Subject
import traceback

with app.app_context():
    try:
        print("Fetching all subjects...")
        subjects = Subject.query.all()
        print(f"Found {len(subjects)} subjects.")
        for s in subjects:
            print(f"Processing subject ID {s.id}: {s.name}")
            d = s.to_dict()
            print(f"  Success: {d}")
    except Exception as e:
        print("EXCEPTION DETECTED:")
        traceback.print_exc()
