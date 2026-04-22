"""
models.py - Database models for the Timetable AI System
Defines: User, Student, Teacher, Program, Subject, Classroom, TimeSlot, TimetableEntry
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


# ── Junction tables (many-to-many) ──────────────────────────
program_subjects = db.Table(
    "program_subjects",
    db.Column("program_id", db.Integer, db.ForeignKey("programs.id"), primary_key=True),
    db.Column("subject_id", db.Integer, db.ForeignKey("subjects.id"), primary_key=True),
)

program_teachers = db.Table(
    "program_teachers",
    db.Column("program_id", db.Integer, db.ForeignKey("programs.id"), primary_key=True),
    db.Column("teacher_id", db.Integer, db.ForeignKey("teachers.id"), primary_key=True),
)

program_classrooms = db.Table(
    "program_classrooms",
    db.Column("program_id",   db.Integer, db.ForeignKey("programs.id"),   primary_key=True),
    db.Column("classroom_id", db.Integer, db.ForeignKey("classrooms.id"), primary_key=True),
)


# ════════════════════════════════════════════════════════════
# USER  (Admin only)
# ════════════════════════════════════════════════════════════
class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  nullable=False, unique=True)
    email         = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name     = db.Column(db.String(120), nullable=True)
    role          = db.Column(db.String(20),  nullable=False, default="admin")
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256:600000")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id, "username": self.username,
            "email": self.email, "full_name": self.full_name, "role": self.role,
        }


# ════════════════════════════════════════════════════════════
# STUDENT  (self-registration: email + roll_no)
# ════════════════════════════════════════════════════════════
class Student(db.Model):
    __tablename__ = "students"

    id              = db.Column(db.Integer, primary_key=True)
    full_name       = db.Column(db.String(120), nullable=False)
    email           = db.Column(db.String(150), nullable=False, unique=True)
    roll_no         = db.Column(db.String(50),  nullable=False, unique=True)
    password_hash   = db.Column(db.String(256), nullable=False)
    program_id      = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=True)
    # Security fields
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until    = db.Column(db.DateTime, nullable=True)
    last_login      = db.Column(db.DateTime, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    program = db.relationship("Program", foreign_keys=[program_id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256:600000")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_locked(self):
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    def to_dict(self):
        return {
            "id":         self.id,
            "full_name":  self.full_name,
            "email":      self.email,
            "roll_no":    self.roll_no,
            "program_id": self.program_id,
            "program":    self.program.name if self.program else None,
            "role":       "student",
        }


# ════════════════════════════════════════════════════════════
# TEACHER  (self-registration: email + phone_no)
# ════════════════════════════════════════════════════════════
class Teacher(db.Model):
    __tablename__ = "teachers"

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), nullable=False, unique=True)
    email           = db.Column(db.String(150), nullable=True, unique=True)
    phone_no        = db.Column(db.String(20),  nullable=True)   # used for self-registration
    subject_ids     = db.Column(db.String(255), nullable=True, default="")
    password_hash   = db.Column(db.String(256), nullable=True)
    short_name      = db.Column(db.String(20),  nullable=True)
    department      = db.Column(db.String(100), nullable=True)
    # Security fields
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until    = db.Column(db.DateTime, nullable=True)
    last_login      = db.Column(db.DateTime, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256:600000")

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_locked(self):
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    def get_short_name(self):
        if self.short_name:
            return self.short_name
        name = self.name
        for title in ["Dr.", "Prof.", "Mr.", "Ms.", "Mrs.", "Dr"]:
            name = name.replace(title, "").strip()
        words = [w for w in name.split() if w]
        if len(words) >= 2:
            return "".join(w[0].upper() for w in words[:3])
        if len(words) == 1:
            return words[0][:3].upper()
        return "TCH"

    def to_dict(self):
        return {
            "id":           self.id,
            "name":         self.name,
            "email":        self.email,
            "phone_no":     self.phone_no,
            "subject_ids":  self.subject_ids,
            "short_name":   self.get_short_name(),
            "department":   self.department,
            "is_active":    bool(self.password_hash),
            "role":         "teacher",
            "assigned_programs": [p.name for p in self.programs]
        }


# ════════════════════════════════════════════════════════════
# PROGRAM
# ════════════════════════════════════════════════════════════
class Program(db.Model):
    __tablename__ = "programs"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False, unique=True)
    code        = db.Column(db.String(30),  nullable=True)
    prog_type   = db.Column(db.String(30),  nullable=False, default="university")
    level       = db.Column(db.String(50),  nullable=True)
    description = db.Column(db.String(255), nullable=True)

    subjects   = db.relationship("Subject",   secondary=program_subjects,   lazy="select", backref="programs")
    teachers   = db.relationship("Teacher",   secondary=program_teachers,   lazy="select", backref="programs")
    classrooms = db.relationship("Classroom", secondary=program_classrooms, lazy="select")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "code": self.code,
            "prog_type": self.prog_type, "level": self.level,
            "description": self.description,
            "subject_count":   len(self.subjects),
            "teacher_count":   len(self.teachers),
            "classroom_count": len(self.classrooms),
        }

    def to_full_dict(self):
        return {
            **self.to_dict(),
            "subject_ids":   [s.id for s in self.subjects],
            "teacher_ids":   [t.id for t in self.teachers],
            "classroom_ids": [c.id for c in self.classrooms],
        }


# ════════════════════════════════════════════════════════════
# SUBJECT
# ════════════════════════════════════════════════════════════
class Subject(db.Model):
    __tablename__ = "subjects"

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False, unique=True)
    code           = db.Column(db.String(20),  nullable=True)
    hours_per_week = db.Column(db.Integer,     nullable=False, default=3)

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name,
            "code": self.code, 
            "hours_per_week": self.hours_per_week,
            "programs": [p.name for p in self.programs],
            "program_ids": [p.id for p in self.programs]
        }


# ════════════════════════════════════════════════════════════
# CLASSROOM
# ════════════════════════════════════════════════════════════
class Classroom(db.Model):
    __tablename__ = "classrooms"

    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=False, unique=True)
    capacity  = db.Column(db.Integer,    nullable=False, default=30)
    room_type = db.Column(db.String(50), nullable=True,  default="lecture")

    def to_dict(self):
        return {"id": self.id, "name": self.name,
                "capacity": self.capacity, "room_type": self.room_type}


# ════════════════════════════════════════════════════════════
# TIMESLOT
# ════════════════════════════════════════════════════════════
class TimeSlot(db.Model):
    __tablename__ = "timeslots"

    id         = db.Column(db.Integer, primary_key=True)
    day        = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time   = db.Column(db.String(10), nullable=False)

    def to_dict(self):
        return {"id": self.id, "day": self.day,
                "start_time": self.start_time, "end_time": self.end_time,
                "label": f"{self.day} {self.start_time}-{self.end_time}"}


# ════════════════════════════════════════════════════════════
# TIMETABLE ENTRY
# ════════════════════════════════════════════════════════════
class TimetableEntry(db.Model):
    __tablename__ = "timetable_entries"

    id           = db.Column(db.Integer, primary_key=True)
    program_id   = db.Column(db.Integer, db.ForeignKey("programs.id"),   nullable=True)
    subject_id   = db.Column(db.Integer, db.ForeignKey("subjects.id"),   nullable=False)
    teacher_id   = db.Column(db.Integer, db.ForeignKey("teachers.id"),   nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classrooms.id"), nullable=False)
    timeslot_id  = db.Column(db.Integer, db.ForeignKey("timeslots.id"),  nullable=False)
    generation   = db.Column(db.Integer, nullable=True, default=0)

    program   = db.relationship("Program",   foreign_keys=[program_id])
    subject   = db.relationship("Subject",   foreign_keys=[subject_id])
    teacher   = db.relationship("Teacher",   foreign_keys=[teacher_id])
    classroom = db.relationship("Classroom", foreign_keys=[classroom_id])
    timeslot  = db.relationship("TimeSlot",  foreign_keys=[timeslot_id])

    def to_dict(self):
        return {
            "id":           self.id,
            "program_id":   self.program_id,
            "program":      self.program.name   if self.program   else None,
            "subject":      self.subject.name   if self.subject   else None,
            "subject_id":   self.subject_id,
            "subject_code": self.subject.code   if self.subject   else None,
            "teacher":      self.teacher.name   if self.teacher   else None,
            "teacher_id":   self.teacher_id,
            "classroom":    self.classroom.name if self.classroom else None,
            "classroom_id": self.classroom_id,
            "day":          self.timeslot.day        if self.timeslot else None,
            "start_time":   self.timeslot.start_time if self.timeslot else None,
            "end_time":     self.timeslot.end_time   if self.timeslot else None,
            "timeslot_id":  self.timeslot_id,
            "generation":   self.generation,
        }
