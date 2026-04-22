"""
scheduler.py - Genetic Algorithm Engine for Timetable Generation
================================================================
This module implements a full Genetic Algorithm (GA) to generate
conflict-free, optimized timetables.
"""

import random
import copy

# ─────────────────────────────────────────────
# GENE (single class session)
# ─────────────────────────────────────────────
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
