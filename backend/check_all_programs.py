from app import app, db, Program
import traceback

with app.app_context():
    try:
        programs = Program.query.all()
        for p in programs:
            print(f"Program: {p.name} (ID: {p.id})")
            print(f"  Subjects:   {len(p.subjects)}")
            print(f"  Teachers:   {len(p.teachers)}")
            print(f"  Classrooms: {len(p.classrooms)}")
    except Exception as e:
        traceback.print_exc()
