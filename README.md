# Automated Time Table Mapping
### Advanced 4th-Year Major Project: AI-Powered Evolutionary Optimization

**NeuralMap** is a high-performance, automated scheduling system designed to solve the NP-Hard problem of academic timetable generation. Using a **Genetic Algorithm (GA)**, the system explores a massive search space to find conflict-free mappings between Faculty, Subjects, Classrooms, and Temporal Slots.

---

## 🚀 Key Features

### 1. AI Optimization Engine
*   **Genetic Algorithm Core**: Implements evolutionary computing (Selection, Crossover, Mutation) to generate near-perfect schedules.
*   **Hard Constraint Enforcement**: Guarantees zero teacher clashes and zero classroom overlaps.
*   **Heuristic Fitness Scoring**: Mathematical evaluation of schedule quality based on resource distribution and continuity.
*   **Conflict Diagnostic Engine**: A real-time failure-mapping tool that pinpoint clashes for administrative manual override.

### 2. Multi-Role Portal System
*   **Admin Console**: Full architectural control over academic programs, faculty mapping, and AI engine parameters.
*   **Faculty Terminal**: Personalized workload view with classroom mapping.
*   **Student Gateway**: Secure access to program-specific academic pathways.

### 3. Professional Deliverables
*   **Grid-Based PDF Export**: High-quality, printable timetable reports with user metadata and legend mappings.
*   **Excel Synchronization**: Logic-to-data export for external registry management.
*   **Live Analytics**: Real-time system load and resource utilization tracking.

---

## 🛠️ Technical Stack

*   **Backend**: Python / Flask (Scalable Micro-service architecture)
*   **Database**: SQLite with SQLAlchemy ORM
*   **AI Logic**: Pure Python Implementation of Genetic Algorithms
*   **Frontend**: Tailwind CSS / Vanilla JS (Enterprise SaaS Aesthetic)
*   **Visualization**: Chart.js for resource utilization analytics
*   **Reports**: ReportLab (PDF Generation) & OpenPyXL (Excel Mapping)

---

## 📊 Evolutionary Strategy (The "AI Logic")

The system treats a full timetable as a **Chromosome**.
1.  **Selection**: Uses Tournament Selection to pick the strongest schedules.
2.  **Crossover**: Single-point crossover to merge the "best traits" of two schedules.
3.  **Mutation**: Randomly shifts teachers or rooms to prevent the AI from getting stuck in local optima.
4.  **Fitness Function**:
    *   `+1000` starting score.
    *   `-100` per Hard Constraint violation (clashes).
    *   `-10` per Soft Constraint violation (pedagogical preferences).

---

## ⚙️ Installation & Deployment

1. **Clone the Registry**:
   ```bash
   git clone [repository-url]
   ```
2. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize Core**:
   ```bash
   cd backend
   python app.py
   ```
5. **Access Endpoint**: 
   Open `http://localhost:5000` in your browser.

---

## 🔑 Access Credentials (Demo)
*   **Administrator**: `admin` / `admin123`
*   **Student/Faculty**: Use "Load Demo Data" in Admin Panel to populate active nodes (Default Password: `password123`).

---

**Developed by [Your Name]**  
*Submitted as a Major Project for 4th Year Engineering Curriculum.*
