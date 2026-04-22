from app import app, db, Teacher, Subject, Classroom, TimeSlot, Program
import traceback

with app.app_context():
    try:
        print("--- Database Status ---")
        print(f"Programs:   {Program.query.count()}")
        print(f"Teachers:   {Teacher.query.count()}")
        print(f"Subjects:   {Subject.query.count()}")
        print(f"Classrooms: {Classroom.query.count()}")
        print(f"TimeSlots:  {TimeSlot.query.count()}")
        
        if Program.query.count() > 0:
            p = Program.query.first()
            print(f"\nChecking first program: {p.name}")
            print(f"  Subjects in program:  {len(p.subjects)}")
            print(f"  Teachers in program:  {len(p.teachers)}")
            print(f"  Classrooms in program:{len(p.classrooms)}")
            
    except Exception as e:
        print("EXCEPTION DETECTED:")
        traceback.print_exc()
