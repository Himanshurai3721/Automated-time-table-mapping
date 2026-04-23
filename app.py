"""
app.py - Consolidated Flask Backend for AI Timetable Generator
==================================================================
Unified file containing:
  - Database models (User, Student, Teacher, Program, Subject, Classroom, TimeSlot, TimetableEntry)
  - Genetic Algorithm classes (Gene, Chromosome, GeneticAlgorithm)
  - Flask routes and main app
"""

import os
import io
import re
import random
import copy
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_file, send_from_directory, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ════════════════════════════════════════════════════════════
db = SQLAlchemy()

# ════════════════════════════════════════════════════════════
# DATABASE MODELS
# ════════════════════════════════════════════════════════════
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


# ════════════════════════════════════════════════════════════
# GENETIC ALGORITHM ENGINE
# ════════════════════════════════════════════════════════════
class Gene:
    """Represents a single scheduled class: Subject + Teacher + Room + Slot."""
    def __init__(self, subject_id, teacher_id, classroom_id, timeslot_id):
        self.subject_id = subject_id
        self.teacher_id = teacher_id
        self.classroom_id = classroom_id
        self.timeslot_id = timeslot_id

# ─────────────────────────────────────────────
# CHROMOSOME (complete timetable)
# ─────────────────────────────────────────────
class Chromosome:
    def __init__(self, genes=None):
        self.genes = genes if genes else []
        self.fitness = 0
        self.conflicts = 0
        self.conflict_details = [] # New: Diagnostic log

    def calculate_fitness(self):
        score = 1000
        self.conflicts = 0
        self.conflict_details = []
        
        slot_teachers = {}
        slot_rooms = {}
        
        for gene in self.genes:
            tid = gene.timeslot_id
            if tid not in slot_teachers: slot_teachers[tid] = []
            slot_teachers[tid].append(gene)
            if tid not in slot_rooms: slot_rooms[tid] = []
            slot_rooms[tid].append(gene)
        
        # Hard Constraint: Teacher Clashes
        for tid, genes in slot_teachers.items():
            t_ids = [g.teacher_id for g in genes]
            if len(t_ids) != len(set(t_ids)):
                dupes = len(t_ids) - len(set(t_ids))
                self.conflicts += dupes
                score -= dupes * 100
                # Map the specific conflict
                seen = set()
                for g in genes:
                    if g.teacher_id in seen:
                        self.conflict_details.append({"type": "Teacher", "id": g.teacher_id, "slot": tid})
                    seen.add(g.teacher_id)
        
        # Hard Constraint: Room Clashes
        for tid, genes in slot_rooms.items():
            r_ids = [g.classroom_id for g in genes]
            if len(r_ids) != len(set(r_ids)):
                dupes = len(r_ids) - len(set(r_ids))
                self.conflicts += dupes
                score -= dupes * 100
                # Map the specific conflict
                seen = set()
                for g in genes:
                    if g.classroom_id in seen:
                        self.conflict_details.append({"type": "Room", "id": g.classroom_id, "slot": tid})
                    seen.add(g.classroom_id)
        
        # Soft Constraint: Same subject continuity
        subject_slots = {}
        for gene in self.genes:
            if gene.subject_id not in subject_slots: subject_slots[gene.subject_id] = []
            subject_slots[gene.subject_id].append(gene.timeslot_id)
        
        for sub_id, slots in subject_slots.items():
            slots_sorted = sorted(slots)
            for i in range(len(slots_sorted) - 1):
                if slots_sorted[i + 1] - slots_sorted[i] == 1:
                    score -= 10 # Penalty for back-to-back same subjects
        
        if self.genes:
            unique_slots = len(set(g.timeslot_id for g in self.genes))
            score += int((unique_slots / len(self.genes)) * 50)
        
        self.fitness = max(score, 0)
        return self.fitness

# ─────────────────────────────────────────────
# GENETIC ALGORITHM ENGINE
# ─────────────────────────────────────────────
class GeneticAlgorithm:
    def __init__(self, subjects, teachers, classrooms, timeslots, population_size=30, generations=100, mutation_rate=0.1, elite_size=5):
        self.subjects = subjects
        self.teachers = teachers
        self.classrooms = classrooms
        self.timeslots = timeslots
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.subject_teacher_map = self._build_subject_teacher_map()

    def _build_subject_teacher_map(self):
        mapping = {}
        # Get the program ID if we are filtering by one, otherwise we look at all
        # Note: The GA receives the subjects/teachers already filtered by the view if program_id was passed
        for subject in self.subjects:
            sid = subject["id"]
            capable_teachers = []
            
            for teacher in self.teachers:
                # Format of teacher["subject_ids"]: "pid1:s1,s2|pid2:s3,s4"
                raw = teacher.get("subject_ids", "") or ""
                assigned_global = []
                
                # Check for program-specific mappings
                parts = raw.split("|") if raw else []
                for part in parts:
                    if ":" in part:
                        pid_str, sids_str = part.split(":")
                        sids = [int(x) for x in sids_str.split(",") if x.strip().isdigit()]
                        assigned_global.extend(sids)

                if sid in assigned_global:
                    capable_teachers.append(teacher["id"])
            
            if not capable_teachers:
                # Fallback: if no one is explicitly assigned, everyone is capable 
                # (to prevent generation failure, though usually admin should map them)
                capable_teachers = [t["id"] for t in self.teachers]
            
            mapping[sid] = capable_teachers
        return mapping

    def _create_chromosome(self):
        genes = []
        classroom_ids = [c["id"] for c in self.classrooms]
        timeslot_ids = [t["id"] for t in self.timeslots]
        for subject in self.subjects:
            sid = subject["id"]
            hours = subject.get("hours_per_week", 3)
            capable_teachers = self.subject_teacher_map.get(sid, [t["id"] for t in self.teachers])
            for _ in range(hours):
                genes.append(Gene(sid, random.choice(capable_teachers), random.choice(classroom_ids), random.choice(timeslot_ids)))
        return Chromosome(genes)

    def _initialize_population(self):
        return [self._create_chromosome() for _ in range(self.population_size)]

    def _tournament_selection(self, population, tournament_size=5):
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda c: c.fitness)

    def _crossover(self, parent1, parent2):
        if len(parent1.genes) < 2 or len(parent2.genes) < 2: return copy.deepcopy(parent1)
        min_len = min(len(parent1.genes), len(parent2.genes))
        point = random.randint(1, min_len - 1)
        return Chromosome(copy.deepcopy(parent1.genes[:point]) + copy.deepcopy(parent2.genes[point:min_len]))

    def _mutate(self, chromosome):
        classroom_ids = [c["id"] for c in self.classrooms]
        timeslot_ids = [t["id"] for t in self.timeslots]
        for gene in chromosome.genes:
            if random.random() < self.mutation_rate:
                mutation_type = random.choice(["teacher", "classroom", "timeslot"])
                if mutation_type == "teacher":
                    capable = self.subject_teacher_map.get(gene.subject_id, [t["id"] for t in self.teachers])
                    gene.teacher_id = random.choice(capable)
                elif mutation_type == "classroom": gene.classroom_id = random.choice(classroom_ids)
                elif mutation_type == "timeslot": gene.timeslot_id = random.choice(timeslot_ids)
        return chromosome

    def run(self, progress_callback=None):
        population = self._initialize_population()
        best_chromosome = None
        best_fitness = -1
        for generation in range(self.generations):
            for chrom in population: chrom.calculate_fitness()
            population.sort(key=lambda c: c.fitness, reverse=True)
            if population[0].fitness > best_fitness:
                best_fitness = population[0].fitness
                best_chromosome = copy.deepcopy(population[0])
            if best_fitness >= 990: break
            new_population = copy.deepcopy(population[:self.elite_size])
            while len(new_population) < self.population_size:
                parent1 = self._tournament_selection(population)
                parent2 = self._tournament_selection(population)
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                new_population.append(child)
            population = new_population
            if progress_callback and generation % 10 == 0: progress_callback(generation, best_fitness)
        return best_chromosome, best_fitness

def chromosome_to_schedule(chromosome, subject_lookup, teacher_lookup, classroom_lookup, timeslot_lookup):
    schedule = []
    for gene in chromosome.genes:
        s = subject_lookup.get(gene.subject_id, {})
        t = teacher_lookup.get(gene.teacher_id, {})
        c = classroom_lookup.get(gene.classroom_id, {})
        ts = timeslot_lookup.get(gene.timeslot_id, {})
        schedule.append({
            "subject": s.get("name"), "subject_id": gene.subject_id, "subject_code": s.get("code"),
            "teacher": t.get("name"), "teacher_id": gene.teacher_id,
            "classroom": c.get("name"), "classroom_id": gene.classroom_id,
            "day": ts.get("day"), "start_time": ts.get("start_time"), "end_time": ts.get("end_time"), "timeslot_id": gene.timeslot_id
        })
    day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    schedule.sort(key=lambda x: (day_order.get(x["day"], 99), x["start_time"]))
    return schedule


# ════════════════════════════════════════════════════════════
# FLASK APP & ROUTES
# ════════════════════════════════════════════════════════════
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "frontend"))

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path="/",
)
app.secret_key = "timetable-ai-secret-key-2024"
CORS(app, supports_credentials=True)

app.config["SQLALCHEMY_DATABASE_URI"]        = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"]        = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"]        = True

db.init_app(app)

with app.app_context():
    db.create_all()
    # Create default admin account if none exists
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", email="admin@school.edu",
                     full_name="System Administrator", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

# ════════════════════════════════════════════════════════════
# CONSTANTS & HELPERS
# ════════════════════════════════════════════════════════════
MAX_ATTEMPTS = 5
LOCKOUT_MINS = 15
MIN_PWD_LEN  = 8

def _sanitize(value, max_len=200):
    if not isinstance(value, str): return ""
    return value.strip()[:max_len]

def _validate_email(email):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))

def _validate_phone(phone):
    digits = re.sub(r'[\s\-\+]', '', phone)
    return digits.isdigit() and 7 <= len(digits) <= 15

def _handle_failed_login(account):
    account.failed_attempts = (account.failed_attempts or 0) + 1
    if account.failed_attempts >= MAX_ATTEMPTS:
        account.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINS)
    db.session.commit()

def _handle_success_login(account):
    account.failed_attempts = 0
    account.locked_until    = None
    account.last_login      = datetime.utcnow()
    db.session.commit()

def _lockout_response(account):
    remaining = int((account.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
    return jsonify({
        "error": f"Account locked. Try again in {remaining} minute(s).",
        "locked": True
    }), 429

def get_current_user():
    if session.get("user_id"):    return db.session.get(User, session["user_id"])
    if session.get("student_id"): return db.session.get(Student, session["student_id"])
    if session.get("teacher_id"): return db.session.get(Teacher, session["teacher_id"])
    return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return jsonify({"error": "Authentication required", "redirect": "/"}), 401
        return f(*args, **kwargs)
    return decorated

# ════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ════════════════════════════════════════════════════════════

@app.route("/api/auth/register", methods=["POST"])
def unified_register():
    data     = request.get_json() or {}
    role     = _sanitize(data.get("role", "")).lower()
    email    = _sanitize(data.get("email", "")).lower()
    password = data.get("password", "")

    if role not in ("student", "teacher"):
        return jsonify({"error": "Invalid role. Must be 'student' or 'teacher'"}), 400
    if not email or not _validate_email(email):
        return jsonify({"error": "Valid email address is required"}), 400
    if not password or len(password) < MIN_PWD_LEN:
        return jsonify({"error": f"Password must be at least {MIN_PWD_LEN} characters"}), 400

    if role == "student":
        full_name = _sanitize(data.get("full_name", ""))
        roll_no   = _sanitize(data.get("roll_no", "")).upper()
        prog_id   = data.get("program_id")
        if not full_name or not roll_no:
            return jsonify({"error": "Full name and roll number are required"}), 400
        
        student = Student.query.filter((db.func.lower(Student.email) == email) | 
                                       (db.func.lower(Student.roll_no) == roll_no.lower())).first()
        if student:
            if student.password_hash: return jsonify({"error": "Account already exists"}), 409
            student.full_name = full_name; student.email = email; student.roll_no = roll_no
            if prog_id: student.program_id = int(prog_id)
        else:
            student = Student(full_name=full_name, email=email, roll_no=roll_no, 
                              program_id=int(prog_id) if prog_id else None)
        
        student.set_password(password)
        db.session.add(student); db.session.commit()
        session.clear(); session["student_id"] = student.id; session.permanent = True
        return jsonify({"message": "Student registered successfully", "user": student.to_dict()}), 201

    if role == "teacher":
        phone_no = _sanitize(data.get("phone_no", ""))
        if not phone_no: return jsonify({"error": "Phone number is required"}), 400
        teacher = Teacher.query.filter(db.func.lower(Teacher.email) == email).first()
        if not teacher: return jsonify({"error": "No faculty record found with this email. Contact Admin."}), 404
        
        # Verify phone number match
        import re
        def _clean(p): return re.sub(r'[\s\-\+]', '', p or "")
        if _clean(teacher.phone_no) != _clean(phone_no):
            return jsonify({"error": "Phone number does not match our records. Contact Admin."}), 401

        if teacher.password_hash: return jsonify({"error": "Account already active. Please sign in."}), 409
        
        teacher.set_password(password); db.session.commit()
        session.clear(); session["teacher_id"] = teacher.id; session.permanent = True
        return jsonify({"message": "Faculty account activated successfully!", "user": teacher.to_dict()}), 201

@app.route("/api/auth/login", methods=["POST"])
def unified_login():
    data     = request.get_json() or {}
    role     = _sanitize(data.get("role", "")).lower()
    password = data.get("password", "")
    username = _sanitize(data.get("username", ""))
    email    = _sanitize(data.get("email", "")).lower()

    if not role: return jsonify({"error": "Role is required"}), 400
    if not password: return jsonify({"error": "Password is required"}), 400

    if role == "admin":
        user = User.query.filter((db.func.lower(User.username) == username.lower()) | 
                                 (db.func.lower(User.email) == username.lower()) | 
                                 (db.func.lower(User.email) == email.lower())).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid admin credentials"}), 401
        session.clear(); session["user_id"] = user.id; session.permanent = True
        return jsonify({"message": "Admin login successful", "role": "admin", "user": user.to_dict()})

    if role == "student":
        if not email: return jsonify({"error": "Email is required"}), 400
        student = Student.query.filter(db.func.lower(Student.email) == email).first()
        if not student: return jsonify({"error": "No student account found"}), 401
        if student.is_locked(): return _lockout_response(student)
        if not student.check_password(password):
            _handle_failed_login(student)
            return jsonify({"error": "Invalid password"}), 401
        _handle_success_login(student)
        session.clear(); session["student_id"] = student.id; session.permanent = True
        return jsonify({"message": "Student login successful", "role": "student", "user": student.to_dict()})

    if role == "teacher":
        if not email: return jsonify({"error": "Email is required"}), 400
        teacher = Teacher.query.filter(db.func.lower(Teacher.email) == email).first()
        if not teacher: return jsonify({"error": "No faculty account found"}), 401
        if not teacher.password_hash: return jsonify({"error": "Account not activated"}), 401
        if teacher.is_locked(): return _lockout_response(teacher)
        if not teacher.check_password(password):
            _handle_failed_login(teacher)
            return jsonify({"error": "Invalid password"}), 401
        _handle_success_login(teacher)
        session.clear(); session["teacher_id"] = teacher.id; session.permanent = True
        return jsonify({"message": "Faculty login successful", "role": "teacher", "user": teacher.to_dict()})

    return jsonify({"error": "Invalid role"}), 400

@app.route("/api/auth/logout", methods=["POST"])
def unified_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route("/api/auth/whoami", methods=["GET"])
def whoami():
    u = get_current_user()
    if not u: return jsonify({"error": "Not authenticated"}), 401
    role = "admin" if isinstance(u, User) else ("student" if isinstance(u, Student) else "teacher")
    return jsonify({"role": role, "user": u.to_dict()})

@app.route("/api/students", methods=["GET"])
@login_required
def get_students():
    return jsonify([s.to_dict() for s in Student.query.all()])

@app.route("/api/students", methods=["POST"])
@login_required
def add_student():
    data = request.get_json()
    if not data or not data.get("full_name") or not data.get("email") or not data.get("roll_no"):
        return jsonify({"error": "Full name, email, and roll number are required"}), 400
    
    email = data["email"].strip().lower()
    roll_no = data["roll_no"].strip().upper()
    
    if Student.query.filter((db.func.lower(Student.email) == email) | 
                            (db.func.lower(Student.roll_no) == roll_no.lower())).first():
        return jsonify({"error": "Student with this email or roll number already exists"}), 409

    s = Student(
        full_name=data["full_name"].strip(),
        email=email,
        roll_no=roll_no,
        program_id=data.get("program_id")
    )
    s.set_password(data.get("password", "password123"))
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201

@app.route("/api/students/<int:sid>", methods=["PUT"])
@login_required
def update_student(sid):
    s = Student.query.get_or_404(sid)
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided"}), 400
    
    if "full_name" in data: s.full_name = data["full_name"].strip()
    if "email" in data: s.email = data["email"].strip().lower()
    if "roll_no" in data: s.roll_no = data["roll_no"].strip().upper()
    if "program_id" in data: s.program_id = data["program_id"]
    
    db.session.commit()
    return jsonify(s.to_dict())

@app.route("/api/students/<int:sid>", methods=["DELETE"])
@login_required
def delete_student(sid):
    s = Student.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Student deleted"})

# ════════════════════════════════════════════════════════════
# TEACHERS  (protected)
# ════════════════════════════════════════════════════════════

@app.route("/api/teachers/<int:tid>/programs", methods=["PUT"])
@login_required
def set_teacher_programs(tid):
    t = Teacher.query.get_or_404(tid)
    ids = request.get_json().get("program_ids", [])
    
    # Update junction table entries
    programs = Program.query.filter(Program.id.in_(ids)).all()
    
    # We need to update each program's teachers list
    all_programs = Program.query.all()
    for p in all_programs:
        if p.id in ids:
            if t not in p.teachers: p.teachers.append(t)
        else:
            if t in p.teachers: p.teachers.remove(t)
            
    db.session.commit()
    return jsonify({"message": f"Programs updated for {t.name}"})

@app.route("/api/teachers/<int:tid>/programs", methods=["GET"])
@login_required
def get_teacher_programs(tid):
    t = Teacher.query.get_or_404(tid)
    # Find all programs where this teacher is assigned
    programs = Program.query.filter(Program.teachers.any(id=tid)).all()
    return jsonify([p.id for p in programs])

@app.route("/api/teachers/<int:tid>/programs/<int:pid>/subjects", methods=["PUT"])
@login_required
def set_teacher_program_subjects(tid, pid):
    t = Teacher.query.get_or_404(tid)
    p = Program.query.get_or_404(pid)
    data = request.get_json()
    ids = data.get("subject_ids", [])
    
    # Use the subject_ids field on teacher as a JSON mapping or comma separated list for now
    # Format: "p1:s1,s2|p2:s3,s4"
    current_raw = t.subject_ids or ""
    parts = current_raw.split("|") if current_raw else []
    new_parts = []
    found = False
    for part in parts:
        if part.startswith(f"{pid}:"):
            if ids: new_parts.append(f"{pid}:{','.join(map(str, ids))}")
            found = True
        else:
            new_parts.append(part)
    if not found and ids:
        new_parts.append(f"{pid}:{','.join(map(str, ids))}")
    
    t.subject_ids = "|".join(new_parts)
    db.session.commit()
    return jsonify({"message": "Subjects mapped successfully"})

@app.route("/api/teachers/<int:tid>/programs/<int:pid>/subjects", methods=["GET"])
@login_required
def get_teacher_program_subjects(tid, pid):
    t = Teacher.query.get_or_404(tid)
    current_raw = t.subject_ids or ""
    parts = current_raw.split("|") if current_raw else []
    for part in parts:
        if part.startswith(f"{pid}:"):
            ids_raw = part.split(":")[1]
            return jsonify([int(x) for x in ids_raw.split(",") if x])
    return jsonify([])

@app.route("/api/teachers/<int:tid>/password", methods=["PUT"])
@login_required
def change_teacher_password(tid):
    data = request.get_json()
    new_pwd = data.get("password")
    if not new_pwd or len(new_pwd) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    t = Teacher.query.get_or_404(tid)
    t.set_password(new_pwd)
    db.session.commit()
    return jsonify({"message": f"Password updated for {t.name}"})

@app.route("/api/students/<int:sid>/password", methods=["PUT"])
@login_required
def change_student_password(sid):
    data = request.get_json()
    new_pwd = data.get("password")
    if not new_pwd or len(new_pwd) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    s = Student.query.get_or_404(sid)
    s.set_password(new_pwd)
    db.session.commit()
    return jsonify({"message": f"Password updated for {s.full_name}"})

@app.route("/api/teachers", methods=["GET"])
@login_required
def get_teachers():
    return jsonify([t.to_dict() for t in Teacher.query.all()])

@app.route("/api/teachers", methods=["POST"])
@login_required
def add_teacher():
    data = request.get_json()
    if not data or not data.get("name"): return jsonify({"error": "Name is required"}), 400
    t = Teacher(name=data["name"].strip(), email=data.get("email","").strip(),
                phone_no=data.get("phone_no","1234567890").strip(), department=data.get("department","").strip())
    t.set_password("password123")
    db.session.add(t); db.session.commit()
    return jsonify(t.to_dict()), 201

@app.route("/api/teachers/<int:tid>", methods=["PUT"])
@login_required
def update_teacher(tid):
    t = Teacher.query.get_or_404(tid)
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided"}), 400
    
    if "name" in data: t.name = data["name"].strip()
    if "email" in data: t.email = data["email"].strip()
    if "department" in data: t.department = data["department"].strip()
    if "phone_no" in data: t.phone_no = data["phone_no"].strip()
    
    db.session.commit()
    return jsonify(t.to_dict())

@app.route("/api/teachers/<int:tid>/activate", methods=["POST"])
@login_required
def activate_teacher(tid):
    t = Teacher.query.get_or_404(tid)
    t.phone_no = t.phone_no or "1234567890"
    t.set_password("password123")
    db.session.commit()
    return jsonify({"message": f"Account for {t.name} activated with password123"})

@app.route("/api/teachers/<int:tid>", methods=["DELETE"])
@login_required
def delete_teacher(tid):
    t = Teacher.query.get_or_404(tid); db.session.delete(t); db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route("/api/subjects", methods=["GET"])
@login_required
def get_subjects():
    try:
        return jsonify([s.to_dict() for s in Subject.query.all()])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/subjects", methods=["POST"])
@login_required
def add_subject():
    data = request.get_json()
    if not data or not data.get("name"): return jsonify({"error": "Name is required"}), 400
    s = Subject(name=data["name"].strip(), code=data.get("code","").strip(),
                hours_per_week=int(data.get("hours_per_week", 3)))
    db.session.add(s)
    
    # Handle multiple program associations
    prog_ids = data.get("program_ids", [])
    if data.get("program_id"): prog_ids.append(data.get("program_id"))
    
    if prog_ids:
        programs = Program.query.filter(Program.id.in_(prog_ids)).all()
        s.programs = programs
        
    db.session.commit()
    return jsonify(s.to_dict()), 201

@app.route("/api/subjects/<int:sid>", methods=["PUT"])
@login_required
def update_subject(sid):
    s = Subject.query.get_or_404(sid)
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided"}), 400
    
    if "name" in data: s.name = data["name"].strip()
    if "code" in data: s.code = data["code"].strip()
    if "hours_per_week" in data: s.hours_per_week = int(data["hours_per_week"])
    
    if "program_ids" in data:
        ids = data["program_ids"]
        programs = Program.query.filter(Program.id.in_(ids)).all()
        s.programs = programs
    elif "program_id" in data: # Fallback for old single program_id
        new_pid = data["program_id"]
        s.programs = []
        if new_pid:
            p = db.session.get(Program, int(new_pid))
            if p: s.programs.append(p)
    
    db.session.commit()
    return jsonify(s.to_dict())

@app.route("/api/subjects/<int:sid>", methods=["DELETE"])
@login_required
def delete_subject(sid):
    s = Subject.query.get_or_404(sid); db.session.delete(s); db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route("/api/classrooms", methods=["GET"])
@login_required
def get_classrooms():
    return jsonify([c.to_dict() for c in Classroom.query.all()])

@app.route("/api/classrooms", methods=["POST"])
@login_required
def add_classroom():
    data = request.get_json()
    if not data or not data.get("name"): return jsonify({"error": "Name is required"}), 400
    c = Classroom(name=data["name"].strip(), capacity=int(data.get("capacity",30)))
    db.session.add(c); db.session.commit()
    return jsonify(c.to_dict()), 201

@app.route("/api/classrooms/<int:cid>", methods=["DELETE"])
@login_required
def delete_classroom(cid):
    c = Classroom.query.get_or_404(cid); db.session.delete(c); db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route("/api/programs", methods=["GET"])
@login_required
def get_programs():
    return jsonify([p.to_dict() for p in Program.query.all()])

@app.route("/api/student/programs", methods=["GET"])
def get_programs_public():
    return jsonify([{"id":p.id, "name":p.name, "level":p.level} for p in Program.query.all()])

@app.route("/api/programs", methods=["POST"])
@login_required
def add_program():
    data = request.get_json()
    if not data or not data.get("name"): return jsonify({"error": "Name is required"}), 400
    p = Program(name=data["name"].strip(), level=data.get("level","Undergraduate"))
    db.session.add(p); db.session.commit()
    return jsonify(p.to_dict()), 201

@app.route("/api/programs/<int:pid>", methods=["DELETE"])
@login_required
def delete_program(pid):
    p = Program.query.get_or_404(pid); db.session.delete(p); db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route("/api/timeslots", methods=["GET"])
@login_required
def get_timeslots():
    return jsonify([s.to_dict() for s in TimeSlot.query.all()])

@app.route("/api/timeslots", methods=["POST"])
@login_required
def add_timeslot():
    data = request.get_json()
    s = TimeSlot(day=data["day"], start_time=data["start_time"], end_time=data["end_time"])
    db.session.add(s); db.session.commit()
    return jsonify(s.to_dict()), 201

@app.route("/api/timeslots/<int:tid>", methods=["PUT"])
@login_required
def update_timeslot(tid):
    s = TimeSlot.query.get_or_404(tid)
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided"}), 400
    
    if "day" in data: s.day = data["day"]
    if "start_time" in data: s.start_time = data["start_time"]
    if "end_time" in data: s.end_time = data["end_time"]
    
    db.session.commit()
    return jsonify(s.to_dict())

@app.route("/api/timeslots/<int:tid>", methods=["DELETE"])
@login_required
def delete_timeslot(tid):
    s = TimeSlot.query.get_or_404(tid); db.session.delete(s); db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route("/api/programs/<int:pid>", methods=["GET"])
@login_required
def get_program(pid):
    p = Program.query.get_or_404(pid)
    d = p.to_dict()
    d["subjects"]   = [s.to_dict() for s in p.subjects]
    d["teachers"]   = [t.to_dict() for t in p.teachers]
    d["classrooms"] = [c.to_dict() for c in p.classrooms]
    return jsonify(d)

@app.route("/api/programs/<int:pid>/subjects", methods=["PUT"])
@login_required
def set_program_subjects(pid):
    p    = Program.query.get_or_404(pid)
    ids  = request.get_json().get("subject_ids", [])
    subs = Subject.query.filter(Subject.id.in_(ids)).all()
    p.subjects = subs
    db.session.commit()
    return jsonify({"message": "Subjects updated"})

@app.route("/api/programs/<int:pid>/teachers", methods=["PUT"])
@login_required
def set_program_teachers(pid):
    p    = Program.query.get_or_404(pid)
    ids  = request.get_json().get("teacher_ids", [])
    teachers = Teacher.query.filter(Teacher.id.in_(ids)).all()
    p.teachers = teachers
    db.session.commit()
    return jsonify({"message": "Faculty updated"})

@app.route("/api/programs/<int:pid>/classrooms", methods=["PUT"])
@login_required
def set_program_classrooms(pid):
    p    = Program.query.get_or_404(pid)
    ids  = request.get_json().get("classroom_ids", [])
    rooms = Classroom.query.filter(Classroom.id.in_(ids)).all()
    p.classrooms = rooms
    db.session.commit()
    return jsonify({"message": "Classrooms updated"})

@app.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    try:
        return jsonify({
            "programs": Program.query.count(), 
            "teachers": Teacher.query.count(),
            "students": Student.query.count(),
            "subjects": Subject.query.count(), 
            "classrooms": Classroom.query.count(),
            "timeslots": TimeSlot.query.count(), 
            "timetable_entries": TimetableEntry.query.count()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate", methods=["POST"])
@login_required
def generate_timetable():
    data = request.get_json() or {}
    program_id = data.get('program_id')
    print(f"DEBUG: Generate request for program_id={program_id}")
    
    if program_id:
        program = db.session.get(Program, int(program_id))
        if not program: return jsonify({"error": "Program not found"}), 404
        subjects = [s.to_dict() for s in program.subjects]
        teachers = [t.to_dict() for t in program.teachers]
        classrooms = [c.to_dict() for c in program.classrooms]
        
        # Robustness: Fallback to all if program-specific list is empty
        if not teachers:
            teachers = [t.to_dict() for t in Teacher.query.all()]
        if not classrooms:
            classrooms = [c.to_dict() for c in Classroom.query.all()]
    else:
        subjects = [s.to_dict() for s in Subject.query.all()]
        teachers = [t.to_dict() for t in Teacher.query.all()]
        classrooms = [c.to_dict() for c in Classroom.query.all()]
    
    timeslots = [ts.to_dict() for ts in TimeSlot.query.all()]
    
    print(f"DEBUG: Found {len(subjects)} subjects, {len(teachers)} teachers, {len(classrooms)} classrooms, {len(timeslots)} timeslots")
    
    if not timeslots:
        return jsonify({"error": "No Time Slots defined. Please add time slots first."}), 400
    if not subjects:
        return jsonify({"error": "No Subjects found for this program. Please assign subjects to this program in the 'Subjects' section."}), 400
    if not teachers:
        return jsonify({"error": "No Faculty found for this program. Please assign faculty or add them to the system."}), 400
    if not classrooms:
        return jsonify({"error": "No Classrooms found for this program. Please assign classrooms or add them to the system."}), 400

    ga = GeneticAlgorithm(subjects, teachers, classrooms, timeslots, 
                          population_size=int(data.get('population_size', 30)),
                          generations=int(data.get('generations', 100)))
    
    best_chrom, fitness = ga.run()
    
    # Process conflicts into human readable format for diagnostics
    conflict_details = []
    for c in best_chrom.conflict_details:
        slot = db.session.get(TimeSlot, c['slot'])
        if c['type'] == 'Teacher':
            t = db.session.get(Teacher, c['id'])
            msg = f"Teacher Clash: {t.name} is double booked on {slot.day} {slot.start_time}"
        else:
            r = db.session.get(Classroom, c['id'])
            msg = f"Room Clash: {r.name} is double booked on {slot.day} {slot.start_time}"
        conflict_details.append(msg)

    schedule = chromosome_to_schedule(best_chrom, {s['id']:s for s in subjects}, 
                                      {t['id']:t for t in teachers}, 
                                      {c['id']:c for c in classrooms}, 
                                      {ts['id']:ts for ts in timeslots})
    
    if program_id:
        TimetableEntry.query.filter_by(program_id=program_id).delete()
    else:
        TimetableEntry.query.delete()

    for e in schedule:
        subject = db.session.get(Subject, e['subject_id'])
        if program_id:
            # If generating for a specific program, only save for that program
            db.session.add(TimetableEntry(
                program_id=program_id,
                subject_id=e['subject_id'], 
                teacher_id=e['teacher_id'], 
                classroom_id=e['classroom_id'], 
                timeslot_id=e['timeslot_id']
            ))
        else:
            # If generating master, save for ALL programs associated with this subject
            if subject and subject.programs:
                for prog in subject.programs:
                    db.session.add(TimetableEntry(
                        program_id=prog.id,
                        subject_id=e['subject_id'], 
                        teacher_id=e['teacher_id'], 
                        classroom_id=e['classroom_id'], 
                        timeslot_id=e['timeslot_id']
                    ))
            else:
                # Fallback if subject has no programs
                first_prog = Program.query.first()
                if first_prog:
                    db.session.add(TimetableEntry(
                        program_id=first_prog.id,
                        subject_id=e['subject_id'], 
                        teacher_id=e['teacher_id'], 
                        classroom_id=e['classroom_id'], 
                        timeslot_id=e['timeslot_id']
                    ))
        
    db.session.commit()
    return jsonify({
        "success": True, 
        "fitness": fitness, 
        "conflicts": best_chrom.conflicts,
        "conflict_details": conflict_details, # New diagnostic field
        "total_classes": len(schedule)
    })

@app.route("/api/timetable", methods=["GET"])
@login_required
def get_timetable():
    program_id = request.args.get('program_id')
    query = TimetableEntry.query
    if program_id and program_id.isdigit(): query = query.filter_by(program_id=int(program_id))
    entries = query.all()
    return jsonify({"schedule": [e.to_dict() for e in entries]})

@app.route("/api/export/excel", methods=["GET"])
@login_required
def export_excel():
    import openpyxl
    from openpyxl.styles import Font, Alignment
    program_id = request.args.get('program_id')
    query = TimetableEntry.query
    if program_id and program_id.isdigit(): query = query.filter_by(program_id=int(program_id))
    entries = query.all()
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Timetable"
    headers = ["Program", "Day", "Start Time", "End Time", "Subject", "Teacher", "Classroom"]
    ws.append(headers)
    for cell in ws[1]: cell.font = Font(bold=True); cell.alignment = Alignment(horizontal="center")
    for e in entries:
        d = e.to_dict()
        ws.append([d.get('program') or '—', d.get('day', ''), d.get('start_time', ''), d.get('end_time', ''), d.get('subject', ''), d.get('teacher', ''), d.get('classroom', '')])
    out = io.BytesIO(); wb.save(out); out.seek(0)
    return send_file(out, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="timetable.xlsx")

@app.route("/api/export/pdf", methods=["GET"])
@login_required
def export_pdf():
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    program_id = request.args.get('program_id')
    user = get_current_user()
    if program_id and program_id.isdigit():
        entries = TimetableEntry.query.filter_by(program_id=int(program_id)).all()
        title_text = f"Program Timetable: {entries[0].program.name}" if entries else "Program Timetable"
    elif isinstance(user, Student):
        entries = TimetableEntry.query.filter_by(program_id=user.program_id).all() if user.program_id else []
        title_text = "Student Personal Timetable"
    elif isinstance(user, Teacher):
        entries = TimetableEntry.query.filter_by(teacher_id=user.id).all()
        title_text = "Faculty Teaching Schedule"
    else:
        entries = TimetableEntry.query.all()
        title_text = "Master Timetable"
    out = io.BytesIO(); doc = SimpleDocTemplate(out, pagesize=landscape(A4), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []; styles = getSampleStyleSheet()
    if not isinstance(user, User):
        elements.append(Paragraph(f"<b>Name:</b> {user.full_name if hasattr(user, 'full_name') else user.name}", styles['Normal']))
        if hasattr(user, 'roll_no'):
            elements.append(Paragraph(f"<b>Roll No:</b> {user.roll_no}", styles['Normal']))
            elements.append(Paragraph(f"<b>Program:</b> {user.program.name if user.program else 'N/A'}", styles['Normal']))
        else: elements.append(Paragraph(f"<b>Department:</b> {user.department or 'N/A'}", styles['Normal']))
        elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<font size=14><b>{title_text}</b></font>", styles['Normal']))
    elements.append(Spacer(1, 15))
    schedule = [e.to_dict() for e in entries]
    days_set = set(e['day'] for e in schedule if e['day'])
    periods_set = set((e['start_time'], e['end_time']) for e in schedule if e['start_time'] and e['end_time'])
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days = [d for d in day_order if d in days_set]
    sorted_periods = sorted(list(periods_set))
    grid = { d: [ [] for _ in range(len(sorted_periods)) ] for d in days }
    p_map = { p: i for i, p in enumerate(sorted_periods) }
    for e in schedule:
        d, p_idx = e['day'], p_map.get((e['start_time'], e['end_time']))
        if d in grid and p_idx is not None: grid[d][p_idx].append(e)
    if not entries: elements.append(Paragraph("No schedule data found.", styles['Normal']))
    else:
        data = [["Day"] + [f"{p[0]}-{p[1]}" for p in sorted_periods]]
        for d in days:
            row = [d]
            for i in range(len(sorted_periods)):
                cell = ""
                for e in grid[d][i]:
                    sub = e.get('subject_code') or e.get('subject'); info = e.get('classroom')
                    ext = e.get('teacher') if not isinstance(user, Teacher) else e.get('program')
                    cell += f"{sub}\n{ext}\n{info}\n\n"
                row.append(cell.strip())
            data.append(row)
        t = Table(data, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 7), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('BACKGROUND', (0, 1), (0, -1), colors.HexColor("#f1f5f9"))]))
        elements.append(t); elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<b>{'Subject'}</b>", styles['Normal']))
        elements.append(Spacer(1, 5))
        subject_ids = set(e['subject_id'] for e in schedule if e.get('subject_id'))
        subjects_data = []
        for sid in subject_ids:
            s = db.session.get(Subject, sid)
            if s: subjects_data.append([s.code or s.name[:5], s.name])
        if subjects_data:
            st = Table(subjects_data, hAlign='LEFT', colWidths=[60, 400]); st.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 7), ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#2563eb")), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
            elements.append(st); elements.append(Spacer(1, 15))
        if not isinstance(user, Teacher):
            elements.append(Paragraph("<b>Teacher</b>", styles['Normal']))
            elements.append(Spacer(1, 5))
            teacher_ids = set(e['teacher_id'] for e in schedule)
            teachers_data = []
            for tid in teacher_ids:
                t = db.session.get(Teacher, tid)
                if t: teachers_data.append([t.get_short_name(), t.name])
            if teachers_data:
                tt = Table(teachers_data, hAlign='LEFT', colWidths=[60, 400]); tt.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 7), ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#2563eb")), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
                elements.append(tt)
    doc.build(elements); out.seek(0)
    return send_file(out, mimetype="application/pdf")

@app.route("/api/student/timetable", methods=["GET"])
def student_timetable():
    sid = session.get("student_id")
    if not sid: return jsonify({"error": "Not authenticated"}), 401
    s = db.session.get(Student, sid)
    entries = TimetableEntry.query.filter_by(program_id=s.program_id).all() if s.program_id else []
    return _build_grid_response(entries)

@app.route("/api/teacher/timetable", methods=["GET"])
def teacher_timetable():
    tid = session.get("teacher_id")
    if not tid: return jsonify({"error": "Not authenticated"}), 401
    entries = TimetableEntry.query.filter_by(teacher_id=tid).all()
    return _build_grid_response(entries)

def _build_grid_response(entries):
    schedule = [e.to_dict() for e in entries]
    days_set = set(); periods_set = set()
    for e in schedule:
        if e['day']: days_set.add(e['day'])
        if e['start_time'] and e['end_time']: periods_set.add((e['start_time'], e['end_time']))
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days = [d for d in day_order if d in days_set]
    sorted_periods = sorted(list(periods_set)); periods = [{"start": p[0], "end": p[1]} for p in sorted_periods]
    period_idx_map = { (p[0], p[1]): i for i, p in enumerate(sorted_periods) }
    grid = { day: [ [] for _ in range(len(periods)) ] for day in days }
    for e in schedule:
        d = e['day']; p_idx = period_idx_map.get((e['start_time'], e['end_time']))
        if d in grid and p_idx is not None: grid[d][p_idx].append(e)
    teacher_ids = set(e['teacher_id'] for e in schedule); subject_ids = set(e['subject_id'] for e in schedule if e.get('subject_id'))
    teachers = []
    for tid in teacher_ids:
        t = db.session.get(Teacher, tid)
        if t: teachers.append({"id": t.id, "short": t.get_short_name(), "full": t.name})
    subjects = []
    for sid in subject_ids:
        s = db.session.get(Subject, sid)
        if s: subjects.append({"id": s.id, "code": s.code or s.name[:5], "name": s.name})
    return jsonify({"schedule": schedule, "days": days, "periods": periods, "grid": grid, "teachers": teachers, "subjects": subjects})

@app.route("/api/admin/activate-all-faculty", methods=["POST"])
@login_required
def activate_all_faculty():
    teachers = Teacher.query.all(); count = 0
    for t in teachers:
        if not t.password_hash or not t.phone_no: t.phone_no = "1234567890"; t.set_password("password123"); count += 1
    db.session.commit()
    return jsonify({"message": f"Activated {count} faculty accounts successfully!"})

@app.route("/api/seed", methods=["POST"])
@login_required
def seed_data():
    try:
        db.drop_all(); db.create_all()
        admin = User(username="admin", email="admin@school.edu", full_name="System Administrator", role="admin"); admin.set_password("admin123"); db.session.add(admin)
        programs = [Program(name="B.Tech CSE Core", code="BT-CSE", level="Undergraduate"), Program(name="B.Tech CSE (AI & ML)", code="BT-AI-ML", level="Undergraduate"), Program(name="B.Tech CSE (Data Science)", code="BT-DS", level="Undergraduate"), Program(name="B.Tech CSE (Cyber Security)", code="BT-CS", level="Undergraduate"), Program(name="B.Tech Information Technology", code="BT-IT", level="Undergraduate"), Program(name="B.Tech Electronics & Communication", code="BT-ECE", level="Undergraduate"), Program(name="B.Tech Mechanical Engineering", code="BT-ME", level="Undergraduate")]
        db.session.add_all(programs); db.session.flush()
        subjects = [Subject(name="Data Structures", code="CS101", hours_per_week=4), Subject(name="Algorithms", code="CS102", hours_per_week=4), Subject(name="Database Systems", code="DB205", hours_per_week=3), Subject(name="Operating Systems", code="CS301", hours_per_week=4), Subject(name="Computer Networks", code="CS302", hours_per_week=3), Subject(name="Software Engineering", code="CS305", hours_per_week=3), Subject(name="Artificial Intelligence", code="AI201", hours_per_week=3), Subject(name="Machine Learning", code="ML202", hours_per_week=3), Subject(name="Deep Learning", code="DL401", hours_per_week=3), Subject(name="Big Data Analytics", code="DS301", hours_per_week=3), Subject(name="Network Security", code="NS302", hours_per_week=3), Subject(name="Cryptography", code="CY401", hours_per_week=3), Subject(name="Python Programming", code="PY105", hours_per_week=4), Subject(name="Web Technologies", code="IT201", hours_per_week=3), Subject(name="Cloud Computing", code="CC301", hours_per_week=3), Subject(name="Digital Electronics", code="EC201", hours_per_week=4), Subject(name="Signals & Systems", code="EC202", hours_per_week=4), Subject(name="Microprocessors", code="EC301", hours_per_week=3), Subject(name="VLSI Design", code="EC401", hours_per_week=3), Subject(name="Engineering Mechanics", code="ME101", hours_per_week=4), Subject(name="Thermodynamics", code="ME201", hours_per_week=4), Subject(name="Fluid Mechanics", code="ME202", hours_per_week=3), Subject(name="Manufacturing Processes", code="ME301", hours_per_week=3)]
        db.session.add_all(subjects)
        teachers = [Teacher(name="Dr. Alan Turing", email="turing@school.edu", department="Computer Science", phone_no="1234567890"), Teacher(name="Dr. Ada Lovelace", email="ada@school.edu", department="Computer Science", phone_no="1234567890"), Teacher(name="Dr. Donald Knuth", email="knuth@school.edu", department="Computer Science", phone_no="1234567890"), Teacher(name="Dr. Geoffrey Hinton", email="hinton@school.edu", department="AI & DS", phone_no="1234567890"), Teacher(name="Dr. Andrew Ng", email="andrew@school.edu", department="AI & DS", phone_no="1234567890"), Teacher(name="Dr. Claude Shannon", email="shannon@school.edu", department="IT & Cyber", phone_no="1234567890"), Teacher(name="Dr. Whitfield Diffie", email="diffie@school.edu", department="IT & Cyber", phone_no="1234567890"), Teacher(name="Dr. Heinrich Hertz", email="hertz@school.edu", department="ECE", phone_no="1234567890"), Teacher(name="Dr. Guglielmo Marconi", email="marconi@school.edu", department="ECE", phone_no="1234567890"), Teacher(name="Dr. Nikola Tesla", email="tesla@school.edu", department="ECE", phone_no="1234567890"), Teacher(name="Dr. Isaac Newton", email="tesla_rival@school.edu", department="Mechanical", phone_no="1234567890"), Teacher(name="Dr. James Watt", email="watt@school.edu", department="Mechanical", phone_no="1234567890"), Teacher(name="Dr. Rudolf Diesel", email="diesel@school.edu", department="Mechanical", phone_no="1234567890")]
        for t in teachers: t.set_password("password123")
        db.session.add_all(teachers)
        rooms = [Classroom(name="CS Lab 1", capacity=40, room_type="lab"), Classroom(name="CS Lab 2", capacity=40, room_type="lab"), Classroom(name="AI/ML Center", capacity=30, room_type="lab"), Classroom(name="Data Science Lab", capacity=30, room_type="lab"), Classroom(name="Cyber Range", capacity=30, room_type="lab"), Classroom(name="ECE Lab A", capacity=40, room_type="lab"), Classroom(name="Mech Workshop", capacity=50, room_type="workshop"), Classroom(name="Lecture Hall 101", capacity=60, room_type="lecture"), Classroom(name="Lecture Hall 102", capacity=60, room_type="lecture"), Classroom(name="Lecture Hall 201", capacity=80, room_type="lecture"), Classroom(name="Lecture Hall 202", capacity=80, room_type="lecture"), Classroom(name="Seminar Hall A", capacity=120, room_type="lecture")]
        db.session.add_all(rooms); days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days:
            for start, end in [("08:30", "09:30"), ("09:30", "10:30"), ("10:45", "11:45"), ("11:45", "12:45"), ("01:30", "02:30"), ("02:30", "03:30"), ("03:45", "04:45")]: db.session.add(TimeSlot(day=day, start_time=start, end_time=end))
        db.session.flush(); p1, p2, p3, p4, p5, p6, p7 = programs
        p1.subjects = subjects[0:6] + [subjects[12], subjects[13]]; p2.subjects = subjects[0:4] + subjects[6:9] + [subjects[12]]; p3.subjects = subjects[0:3] + [subjects[7], subjects[9], subjects[12], subjects[13]]; p4.subjects = subjects[0:4] + [subjects[10], subjects[11], subjects[12]]; p5.subjects = subjects[0:3] + subjects[12:15] + [subjects[4], subjects[5]]; p6.subjects = subjects[15:19] + [subjects[0], subjects[12]]; p7.subjects = subjects[19:23] + [subjects[12]]
        p1.teachers = teachers[0:3] + [teachers[12]]; p2.teachers = teachers[0:2] + teachers[3:5]; p3.teachers = [teachers[0], teachers[2], teachers[3], teachers[4]]; p4.teachers = [teachers[1], teachers[2], teachers[5], teachers[6]]; p5.teachers = teachers[0:2] + teachers[5:7]; p6.teachers = teachers[7:10] + [teachers[0]]; p7.teachers = teachers[10:13] + [teachers[0]]
        for p in [p1, p2, p3, p4, p5]: p.classrooms = rooms[0:5] + rooms[7:12]
        p6.classrooms = [rooms[5]] + rooms[7:12]; p7.classrooms = [rooms[6]] + rooms[7:12]
        students_data = [{"name": "John Core", "email": "cse@demo.com", "roll": "CS001", "pid": p1.id}, {"name": "Alice AI", "email": "ai@demo.com", "roll": "AI001", "pid": p2.id}, {"name": "Bob Data", "email": "ds@demo.com", "roll": "DS001", "pid": p3.id}, {"name": "Charlie Cyber", "email": "cyber@demo.com", "roll": "CY001", "pid": p4.id}, {"name": "Diana IT", "email": "it@demo.com", "roll": "IT001", "pid": p5.id}, {"name": "Eve ECE", "email": "ece@demo.com", "roll": "EC001", "pid": p6.id}, {"name": "Frank Mech", "email": "mech@demo.com", "roll": "ME001", "pid": p7.id}]
        for s_info in students_data:
            s = Student(full_name=s_info["name"], email=s_info["email"], roll_no=s_info["roll"], program_id=s_info["pid"]); s.set_password("password123"); db.session.add(s)
        db.session.commit()
        return jsonify({"message": "Database reset and massive demo data loaded!"})
    except Exception as e: db.session.rollback(); return jsonify({"error": str(e)}), 500

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)): return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__": app.run(debug=False, port=5000, use_reloader=False)
