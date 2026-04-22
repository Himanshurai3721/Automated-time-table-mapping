/**
 * app.js - NeuralMap: Advanced AI Scheduler Logic
 * Swiss Engineering Design Pattern Implementation
 */

const API = '/api';

// ── STATE ────────────────────────────────────────────────────
let currentUser = null;
let currentRole = null; 
let authMode    = 'login';
let cache = { programs: [], teachers: [], subjects: [], classrooms: [], timeslots: [], schedule: [] };

// ── VIEW ROUTING ──────────────────────────────────────────────
function showView(viewId) {
    const el = document.getElementById('view-' + viewId);
    if (!el) return;
    document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
    el.classList.add('active');
}

function showAdminPage(pageId) {
    document.querySelectorAll('.admin-page').forEach(p => p.classList.remove('active'));
    const target = document.getElementById('admin-page-' + pageId);
    if(target) target.classList.add('active');
    
    // Update Sidebar Navigation
    document.querySelectorAll('.sidebar-item').forEach(a => a.classList.remove('active'));
    const activeNav = document.getElementById('nav-' + pageId);
    if(activeNav) activeNav.classList.add('active');

    // Update Title with Exact Prev UI Terms
    const titleMap = {
        'dashboard': 'Dashboard',
        'programs': 'Programs',
        'teachers': 'Faculty',
        'subjects': 'Subjects',
        'classrooms': 'Classrooms',
        'timeslots': 'Time Slots',
        'generate': 'AI Generator',
        'timetable': 'Master Table',
        'students': 'Students'
    };
    const titleEl = document.getElementById('admin-page-title');
    if(titleEl) titleEl.textContent = titleMap[pageId] || 'Admin';

    // Load page data
    if(pageId === 'dashboard') loadStats();
    if(pageId === 'programs')  loadPrograms();
    if(pageId === 'teachers')  loadTeachers();
    if(pageId === 'subjects')  loadSubjects();
    if(pageId === 'classrooms') loadClassrooms();
    if(pageId === 'timeslots') loadTimeslots();
    if(pageId === 'students')  loadStudents();
    if(pageId === 'generate')  loadProgramsDropdown();
    if(pageId === 'timetable') { loadProgramsDropdown(); loadTimetable(); }
}

// ── DASHBOARD & STATS ─────────────────────────────────────────
async function loadStats() {
    try {
        const stats = await api('GET', '/stats');
        const container = document.getElementById('admin-stats-container');
        if(!container) return;
        
        container.innerHTML = [
            { l: 'Programs', v: stats.programs, d: 'Active Program Architecture Slots' },
            { l: 'Faculty', v: stats.teachers, d: 'Faculty Processing Units' },
            { l: 'Subjects', v: stats.subjects, d: 'Complex Subject Mapping Load' },
            { l: 'Classrooms', v: stats.classrooms, d: 'Hardware Node Room Limits' }
        ].map(x => `
            <div class="card-stat p-8 shadow-sm border border-gray-100 group hover:border-[var(--swiss-navy)] transition-all">
                <p class="text-[11px] font-black uppercase text-gray-400 mb-1 tracking-[0.2em] group-hover:text-[var(--swiss-red)]">${x.l}</p>
                <p class="text-7xl font-black tracking-tighter text-[var(--swiss-navy)] mb-4">${x.v}</p>
                <div class="w-8 h-1 bg-[var(--swiss-navy)] mb-4 transition-all group-hover:w-full"></div>
                <p class="text-[9px] font-bold text-gray-400 uppercase tracking-widest leading-relaxed">${x.d}</p>
            </div>
        `).join('');

        // Dynamic System Metrics
        const load = Math.floor(Math.random() * (75 - 45) + 45);
        const loadBar = document.getElementById('sidebar-load-bar');
        const loadPerc = document.getElementById('sidebar-load-perc');
        const loadText = document.getElementById('sidebar-load-text');
        if(loadBar) loadBar.style.width = load + '%';
        if(loadPerc) loadPerc.textContent = load + '%';
        if(loadText) loadText.textContent = `SYSTEM_LOAD: ${load}%`;

        const convVal = document.getElementById('convergence-val');
        if(convVal) convVal.textContent = '100%';

    } catch(e) { toast(e.message, 'error'); }
}

// ── AI ENGINE ────────────────────────────────────────────────
async function generateTimetable() {
    const btn = document.getElementById('generate-btn');
    const pCard = document.getElementById('progress-card');
    const pBar = document.getElementById('progress-bar');
    const pPct = document.getElementById('progress-percent');
    const resB = document.getElementById('result-banner');

    btn.disabled = true; pCard.classList.remove('hidden'); resB.classList.add('hidden');
    let p = 0;
    const interval = setInterval(() => { 
        p = Math.min(p + 5, 98); 
        pBar.style.width = p + '%'; 
        pPct.textContent = p + '%'; 
    }, 150);

    try {
        const res = await api('POST', '/generate', {
            program_id: document.getElementById('ga-program-id').value || null,
            population_size: parseInt(document.getElementById('ga-population').value),
            generations: parseInt(document.getElementById('ga-generations').value)
        });
        clearInterval(interval); pBar.style.width = '100%'; pPct.textContent = '100%';
        
        resB.classList.remove('hidden');
        resB.className = `p-12 border-t-8 ${res.conflicts === 0 ? 'bg-gray-50 border-[var(--swiss-navy)]' : 'bg-red-50 border-[var(--swiss-red)]'}`;
        
        let diagHtml = '';
        if(res.conflict_details && res.conflict_details.length > 0) {
            diagHtml = `<div class="mt-8 pt-8 border-t border-gray-200"><p class="text-[10px] font-black uppercase mb-4 text-[var(--swiss-red)]">Conflict_Log</p><ul class="text-[10px] font-bold space-y-2 uppercase opacity-70">` + 
                       res.conflict_details.map(d => `<li class="flex items-center gap-2"><span class="w-1.5 h-1.5 bg-[var(--swiss-red)]"></span>${d}</li>`).join('') + `</ul></div>`;
        }

        resB.innerHTML = `
            <div class="flex justify-between items-start mb-8">
                <div>
                    <h3 class="text-4xl font-black uppercase tracking-tighter mb-2">${res.conflicts === 0 ? 'Optimal Schedule' : 'Conflicts Found'}</h3>
                    <p class="text-[10px] font-black uppercase tracking-widest text-gray-400">Fitness Score: ${res.fitness}</p>
                </div>
                <div class="text-right">
                    <p class="text-5xl font-black tracking-tighter ${res.conflicts > 0 ? 'text-[var(--swiss-red)]' : ''}">${res.conflicts}</p>
                    <p class="text-[10px] font-black uppercase text-gray-400">Total Conflicts</p>
                </div>
            </div>
            ${diagHtml}
            <div class="mt-10 flex gap-4">
                <button onclick="showAdminPage('timetable')" class="btn-primary text-[10px]">View Timetable</button>
                <button onclick="exportPDF()" class="btn-secondary text-[10px]">Export PDF</button>
            </div>
        `;
        toast('SCHEDULE_GENERATION_COMPLETE', 'success');
        loadStats(); // Auto-update dashboard metrics
        loadTimetable(); // Pre-load timetable data
    } catch(e) { clearInterval(interval); pCard.classList.add('hidden'); toast(e.message, 'error'); }
    finally { btn.disabled = false; }
}

// ── AUTH HANDLING ─────────────────────────────────────────────
async function openAuth(role) {
    currentRole = role;
    authMode = 'login';
    showView('auth');
    
    const icon = document.getElementById('auth-icon');
    const title = document.getElementById('auth-title');
    const tabs = document.getElementById('auth-tabs');
    const fUser = document.getElementById('field-username');
    const fEmail = document.getElementById('field-email');
    const fSign = document.getElementById('signup-fields');
    
    if(!icon || !title) return;

    tabs.classList.add('hidden');
    fUser.classList.add('hidden');
    fEmail.classList.remove('hidden');
    fSign.classList.add('hidden');

    if(role === 'admin') {
        icon.textContent = 'security';
        title.textContent = 'Admin Login';
        fUser.classList.remove('hidden');
        fEmail.classList.add('hidden');
    } else if(role === 'teacher') {
        icon.textContent = 'person';
        title.textContent = 'Faculty Login';
    } else if(role === 'student') {
        icon.textContent = 'school';
        title.textContent = 'Student Login';
        tabs.classList.remove('hidden');
        loadProgramsDropdown();
    }
    setAuthMode('login');
}

function setAuthMode(mode) {
    authMode = mode;
    const isSignup = (mode === 'signup' && currentRole === 'student');
    const signupEl = document.getElementById('signup-fields');
    const btn = document.getElementById('auth-btn');
    const title = document.getElementById('auth-title');
    
    if(signupEl) signupEl.classList.toggle('hidden', !isSignup);

    if(title) {
        if(isSignup) title.textContent = 'Sign Up';
        else title.textContent = currentRole === 'admin' ? 'Admin Login' : (currentRole === 'teacher' ? 'Faculty Login' : 'Student Login');
    }

    if(btn) btn.textContent = isSignup ? 'Create Account' : 'Login';
    
    ['tab-login', 'tab-signup'].forEach(id => {
        const el = document.getElementById(id);
        if(!el) return;
        const active = id.includes(mode);
        el.className = `py-4 text-[10px] font-black uppercase tracking-widest transition-all ${active ? 'bg-primary text-white' : 'bg-transparent text-primary'}`;
    });
}

async function handleAuth(e) {
    e.preventDefault();
    const btn = document.getElementById('auth-btn');
    const err = document.getElementById('auth-error');
    if(!btn || !err) return;

    err.classList.add('hidden');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner border-white/20 border-t-white mr-3"></span> Processing...';

    const payload = { role: currentRole };
    payload.username = document.getElementById('auth-username').value.trim();
    payload.email = document.getElementById('auth-email').value.trim();
    payload.password = document.getElementById('auth-password').value;

    let endpoint = '/auth/login';
    if(currentRole === 'student' && authMode === 'signup') {
        endpoint = '/auth/register';
        payload.full_name = document.getElementById('auth-fullname').value.trim();
        payload.roll_no = document.getElementById('auth-rollno').value.trim();
        payload.program_id = document.getElementById('auth-program').value;
    }

    try {
        const res = await api('POST', endpoint, payload);
        toast('SECURITY_CLEARANCE_PASS', 'success');
        if(currentRole === 'admin') { showView('admin'); showAdminPage('dashboard'); }
        else { showView('portal'); loadPortal(); }
    } catch(e) {
        err.classList.remove('hidden');
        document.getElementById('auth-error-msg').textContent = e.message.toUpperCase();
    } finally {
        btn.disabled = false;
        btn.textContent = authMode === 'signup' ? 'INITIATE_INITIALIZATION' : 'REQUEST_ACCESS';
    }
}

// ── PORTAL VIEW (STUDENT/TEACHER) ─────────────────────────────
async function loadPortal() {
    const container = document.getElementById('portal-timetable-container');
    try {
        const me = await api('GET', '/auth/whoami');
        currentUser = me.user;
        currentRole = me.role;
        
        document.getElementById('portal-user-name').textContent = (currentUser.full_name || currentUser.name).toUpperCase();
        document.getElementById('portal-user-meta').textContent = currentRole === 'student' 
            ? `SERIAL: ${currentUser.roll_no} // ARCH: ${currentUser.program || 'UNMAPPED'}`
            : `NODE: FACULTY // CORE: ${currentUser.department || 'GENERAL'}`;
        
        document.getElementById('portal-display-title').innerHTML = currentRole === 'student' ? 'Class<br/>Timetable' : 'Teaching<br/>Schedule';

        const data = await api('GET', `/${currentRole}/timetable`);
        renderGrid(container, data);
        renderLegends(data);
    } catch(e) {
        if(container) container.innerHTML = `<div class="p-20 text-[var(--swiss-red)] font-black uppercase text-center tracking-widest">CRITICAL_ERROR: ${e.message}</div>`;
    }
}

function renderGrid(container, data) {
    if(!container) return;
    if(!data.schedule || data.schedule.length === 0) {
        container.innerHTML = `<div class="p-60 text-center text-gray-200 font-black uppercase tracking-[0.5em] text-sm">NO_MATRIX_DATA_GENERATED</div>`;
        return;
    }
    const { days, periods, grid } = data;
    const tMap = {}; (data.teachers || []).forEach(t => tMap[t.id] = t.full);

    let html = `<div class="overflow-x-auto"><table class="tt-table"><thead><tr><th style="width:100px">TEMPORAL</th>`;
    periods.forEach((p, i) => html += `<th>SEQ_${(i+1).toString().padStart(2,'0')}<div class="text-[8px] opacity-50 mt-1 font-bold tracking-tight">${p.start} - ${p.end}</div></th>`);
    html += `</tr></thead><tbody>`;

    days.forEach(day => {
        html += `<tr><td class="tt-day-label">${day.slice(0,3)}</td>`;
        for(let i=0; i<periods.length; i++) {
            const entries = (grid[day] && grid[day][i]) ? grid[day][i] : [];
            if(entries.length === 0) html += `<td class="tt-empty"></td>`;
            else {
                html += `<td class="tt-cell">`;
                entries.forEach(e => {
                    const sub = currentRole === 'student' ? (tMap[e.teacher_id] || e.teacher) : (e.program || 'NODE');
                    html += `<div class="fade-up">
                        <span class="tt-code">${e.subject_code || e.subject}</span>
                        <span class="tt-teacher">${sub}</span>
                        <span class="tt-room">${e.classroom}</span>
                    </div>`;
                });
                html += `</td>`;
            }
        }
        html += `</tr>`;
    });
    container.innerHTML = html + `</tbody></table></div>`;
}

function renderLegends(data) {
    const tL = document.getElementById('portal-teacher-legend');
    const sL = document.getElementById('portal-subject-legend');
    if(!tL || !sL) return;

    if(currentRole === 'teacher') tL.parentElement.classList.add('hidden');
    else tL.parentElement.classList.remove('hidden');

    tL.innerHTML = (data.teachers || []).map(t => `
        <div class="topology-node flex items-center justify-between mb-1">
            <div class="flex items-center gap-4">
                <span class="w-10 h-10 bg-[var(--swiss-navy)] text-white flex items-center justify-center font-black text-[10px]">
                    <i class="fa-solid fa-user"></i>
                </span>
                <span class="font-black uppercase text-xs tracking-tight text-[var(--swiss-navy)]">${t.full.toUpperCase()}</span>
            </div>
            <i class="fa-solid fa-user-check text-gray-300 text-sm"></i>
        </div>
    `).join('') || '<div class="p-8 text-gray-200 font-black uppercase text-[10px]">EMPTY_REGISTRY</div>';

    sL.innerHTML = (data.subjects || []).map(s => `
        <div class="topology-node flex items-center justify-between mb-1">
            <div class="flex items-center gap-4">
                <span class="w-16 h-10 bg-white border-2 border-[var(--swiss-navy)] text-[var(--swiss-navy)] flex items-center justify-center font-black text-[10px] uppercase">${s.code}</span>
                <span class="font-black uppercase text-xs tracking-tight text-[var(--swiss-navy)]">${s.name.toUpperCase()}</span>
            </div>
            <i class="fa-solid fa-layer-group text-gray-300 text-sm"></i>
        </div>
    `).join('') || '<div class="p-8 text-gray-200 font-black uppercase text-[10px]">EMPTY_ARRAY</div>';
}

// ── REGISTRY HELPERS (CRUD) ───────────────────────────────────
async function loadPrograms() {
    const data = await api('GET', '/programs');
    const tb = document.getElementById('programs-tbody');
    if(!tb) return;
    tb.innerHTML = data.map(p => `
        <tr class="border-b border-gray-100 hover:bg-gray-50 transition-all">
            <td class="px-8 py-6">
                <div class="font-black text-[var(--swiss-navy)] text-sm uppercase tracking-tight">${p.name}</div>
                <div class="text-[9px] text-gray-400 font-bold uppercase tracking-widest mt-1">ID: 0x${p.id.toString(16).toUpperCase()} // LAYER: ${p.level}</div>
            </td>
            <td class="px-8 py-6"><span class="error-tag bg-gray-400">${p.level}</span></td>
            <td class="px-8 py-6 text-right">
                <button onclick="deleteItem('programs', ${p.id})" class="text-gray-300 hover:text-[var(--swiss-red)] transition-all">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </td>
        </tr>
    `).join('');
    loadProgramsDropdown();
}

async function loadTeachers() {
    const data = await api('GET', '/teachers');
    const tb = document.getElementById('teachers-tbody');
    if(!tb) return;
    tb.innerHTML = data.map(t => `
        <tr class="border-b border-gray-100 hover:bg-gray-50">
            <td class="px-8 py-6">
                <div class="font-black text-[var(--swiss-navy)] text-sm uppercase tracking-tight">${t.name}</div>
                <div class="text-[9px] text-gray-400 font-bold uppercase tracking-widest mt-1">
                    ${t.email} // CORE: ${t.assigned_programs && t.assigned_programs.length > 0 ? t.assigned_programs.join(', ') : (t.department || 'GENERAL')}
                </div>
            </td>
            <td class="px-8 py-6 text-center">
                <div class="inline-flex items-center gap-2 px-3 py-1 border border-gray-200 ${t.is_active ? 'bg-green-50 text-green-600' : 'bg-red-50 text-[var(--swiss-red)]'} text-[9px] font-black uppercase">
                    <span class="w-1.5 h-1.5 rounded-full ${t.is_active ? 'bg-green-500' : 'bg-[var(--swiss-red)] animate-pulse'}"></span>
                    ${t.is_active ? 'Online' : 'Disconnected'}
                </div>
            </td>
            <td class="px-8 py-6 text-right flex justify-end gap-2">
                <button onclick="openMappingModal(${t.id}, '${t.name}')" class="w-10 h-10 text-gray-300 hover:text-primary transition-all" title="Map Programs">
                    <span class="material-symbols-outlined">hub</span>
                </button>
                ${!t.is_active ? `<button onclick="activateTeacher(${t.id})" class="btn-primary py-1 px-3 text-[8px]">Activate</button>` : ''}
                <button onclick="openEditTeacherModal(${JSON.stringify(t).replace(/"/g, '&quot;')})" class="w-10 h-10 text-gray-300 hover:text-blue-500 transition-all" title="Edit Profile">
                    <span class="material-symbols-outlined">edit</span>
                </button>
                <button onclick="changePassword('teachers', ${t.id})" class="w-10 h-10 text-gray-300 hover:text-[var(--swiss-navy)]"><span class="material-symbols-outlined">key</span></button>
                <button onclick="deleteItem('teachers', ${t.id})" class="w-10 h-10 text-gray-300 hover:text-[var(--swiss-red)]"><span class="material-symbols-outlined">delete</span></button>
            </td>
        </tr>
    `).join('');
}

function openEditTeacherModal(teacher) {
    document.getElementById('edit-teacher-id').value = teacher.id;
    document.getElementById('edit-teacher-name').value = teacher.name;
    document.getElementById('edit-teacher-email').value = teacher.email;
    document.getElementById('edit-teacher-dept').value = teacher.department || '';
    document.getElementById('edit-teacher-modal').classList.remove('hidden');
}

function closeEditTeacherModal() {
    document.getElementById('edit-teacher-modal').classList.add('hidden');
}

async function saveTeacherEdit(event) {
    event.preventDefault();
    const id = document.getElementById('edit-teacher-id').value;
    const btn = document.getElementById('save-teacher-edit-btn');
    
    const data = {
        name: document.getElementById('edit-teacher-name').value,
        email: document.getElementById('edit-teacher-email').value,
        department: document.getElementById('edit-teacher-dept').value
    };

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner border-white/20 border-t-white mr-2"></span> Updating...';

    try {
        await api('PUT', `/teachers/${id}`, data);
        toast('PROFILE_UPDATED', 'success');
        closeEditTeacherModal();
        loadTeachers();
    } catch(e) { toast(e.message, 'error'); }
    finally {
        btn.disabled = false;
        btn.textContent = 'Update Profile';
    }
}

let currentMappingTeacherId = null;

async function openMappingModal(tid, name) {
    currentMappingTeacherId = tid;
    const modal = document.getElementById('mapping-modal');
    const title = document.getElementById('mapping-modal-title');
    const container = document.getElementById('mapping-options');
    
    title.textContent = `Map ${name}`;
    container.innerHTML = '<div class="col-span-2 py-10 text-center"><div class="spinner"></div></div>';
    modal.classList.remove('hidden');

    try {
        const [allPrograms, assignedIds] = await Promise.all([
            api('GET', '/programs'),
            api('GET', `/teachers/${tid}/programs`)
        ]);

        container.innerHTML = allPrograms.map(p => `
            <div class="group flex items-center gap-4 p-4 border border-gray-100 hover:border-primary transition-all">
                <input type="checkbox" value="${p.id}" ${assignedIds.includes(p.id) ? 'checked' : ''} onchange="toggleTeacherProgram(${tid}, ${p.id}, this.checked)" class="w-5 h-5 border-2 border-[var(--swiss-navy)] text-primary focus:ring-0"/>
                <div class="flex-1">
                    <p class="text-[10px] font-black uppercase tracking-tight leading-none mb-1">${p.name}</p>
                    <p class="text-[8px] font-bold text-gray-400 uppercase tracking-widest">${p.level}</p>
                </div>
                ${assignedIds.includes(p.id) ? `
                    <button onclick="openSubjectMappingModal(${tid}, ${p.id}, '${p.name}')" class="px-3 py-1 bg-primary text-white text-[8px] font-black uppercase tracking-widest hover:bg-black transition-all">
                        Subjects
                    </button>
                ` : ''}
            </div>
        `).join('');

        document.getElementById('save-mapping-btn').onclick = () => { closeMappingModal(); loadTeachers(); };
    } catch(e) { toast(e.message, 'error'); }
}

async function toggleTeacherProgram(tid, pid, checked) {
    // Immediate sync for the junction table
    const checkboxes = document.querySelectorAll('#mapping-options input:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));
    try {
        await api('PUT', `/teachers/${tid}/programs`, { program_ids: ids });
        // Refresh mapping modal to show/hide "Subjects" button
        const name = document.getElementById('mapping-modal-title').textContent.replace('Map ', '');
        openMappingModal(tid, name);
    } catch(e) { toast(e.message, 'error'); }
}

let currentMapTid = null;
let currentMapPid = null;

async function openSubjectMappingModal(tid, pid, progName) {
    currentMapTid = tid;
    currentMapPid = pid;
    const modal = document.getElementById('subject-mapping-modal');
    const container = document.getElementById('subject-mapping-options');
    
    document.getElementById('subject-mapping-title').textContent = `Subjects for ${progName}`;
    container.innerHTML = '<div class="col-span-2 py-10 text-center"><div class="spinner"></div></div>';
    modal.classList.remove('hidden');

    try {
        // Fetch all subjects for this program and currently assigned subjects for this teacher in this program
        const [progData, assignedIds] = await Promise.all([
            api('GET', `/programs/${pid}`),
            api('GET', `/teachers/${tid}/programs/${pid}/subjects`)
        ]);

        if(!progData.subjects || progData.subjects.length === 0) {
            container.innerHTML = '<p class="col-span-2 text-center text-xs font-bold text-gray-400 py-10 uppercase tracking-widest">No subjects found for this program</p>';
            return;
        }

        container.innerHTML = progData.subjects.map(s => `
            <label class="group flex items-center gap-4 p-4 border border-gray-100 hover:border-primary cursor-pointer transition-all">
                <input type="checkbox" value="${s.id}" ${assignedIds.includes(s.id) ? 'checked' : ''} class="w-5 h-5 border-2 border-primary text-primary focus:ring-0"/>
                <div class="flex-1">
                    <p class="text-[10px] font-black uppercase tracking-tight leading-none mb-1">${s.name}</p>
                    <p class="text-[8px] font-bold text-gray-400 uppercase tracking-widest">CODE: ${s.code}</p>
                </div>
            </label>
        `).join('');

        document.getElementById('save-subject-mapping-btn').onclick = saveSubjectMapping;
    } catch(e) { toast(e.message, 'error'); }
}

function closeSubjectMappingModal() {
    document.getElementById('subject-mapping-modal').classList.add('hidden');
}

async function saveSubjectMapping() {
    const btn = document.getElementById('save-subject-mapping-btn');
    const checkboxes = document.querySelectorAll('#subject-mapping-options input:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner border-white/20 border-t-white mr-2"></span> Synchronizing...';

    try {
        await api('PUT', `/teachers/${currentMapTid}/programs/${currentMapPid}/subjects`, { subject_ids: ids });
        toast('MODULES_SYNCED', 'success');
        closeSubjectMappingModal();
    } catch(e) { toast(e.message, 'error'); }
    finally {
        btn.disabled = false;
        btn.textContent = 'Update Module Assignment';
    }
}

function closeMappingModal() {
    document.getElementById('mapping-modal').classList.add('hidden');
    currentMappingTeacherId = null;
}

async function saveMapping(tid) {
    const btn = document.getElementById('save-mapping-btn');
    const checkboxes = document.querySelectorAll('#mapping-options input:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner border-white/20 border-t-white mr-2"></span> Updating...';

    try {
        await api('PUT', `/teachers/${tid}/programs`, { program_ids: ids });
        toast('MAPPING_SYNCHRONIZED', 'success');
        closeMappingModal();
        loadTeachers();
    } catch(e) { toast(e.message, 'error'); }
    finally {
        btn.disabled = false;
        btn.textContent = 'Update Mapping Configuration';
    }
}

async function loadSubjects() {
    const data = await api('GET', '/subjects');
    const tb = document.getElementById('subjects-tbody');
    if(!tb) return;
    tb.innerHTML = data.map(s => `
        <tr class="border-b border-gray-100 hover:bg-gray-50">
            <td class="px-8 py-6">
                <div class="font-black text-[var(--swiss-navy)] text-sm uppercase tracking-tight">${s.name}</div>
                <div class="text-[9px] text-gray-400 font-bold uppercase tracking-widest mt-1">SUB CODE : ${s.code} // LOAD: ${s.hours_per_week} HRS/WK</div>
                <div class="mt-2 flex flex-wrap gap-1">
                    ${(s.programs || []).map(p => `<span class="bg-blue-50 text-blue-600 text-[8px] font-black px-2 py-0.5 uppercase border border-blue-100">${p}</span>`).join('')}
                </div>
            </td>
            <td class="px-8 py-6 text-right flex justify-end gap-2">
                <button onclick="openEditSubjectModal(${JSON.stringify(s).replace(/"/g, '&quot;')})" class="w-10 h-10 text-gray-300 hover:text-blue-500 transition-all" title="Edit Subject">
                    <span class="material-symbols-outlined">edit</span>
                </button>
                <button onclick="deleteItem('subjects', ${s.id})" class="text-gray-300 hover:text-[var(--swiss-red)]"><span class="material-symbols-outlined">delete</span></button>
            </td>
        </tr>
    `).join('');
}

async function openEditSubjectModal(subject) {
    const modal = document.getElementById('edit-subject-modal');
    const container = document.getElementById('edit-subject-programs-list');
    
    document.getElementById('edit-subject-id').value = subject.id;
    document.getElementById('edit-subject-name').value = subject.name;
    document.getElementById('edit-subject-code').value = subject.code;
    document.getElementById('edit-subject-hours').value = subject.hours_per_week;
    
    container.innerHTML = '<div class="spinner"></div>';
    try {
        const programs = await api('GET', '/programs');
        container.innerHTML = programs.map(p => {
            const isChecked = subject.program_ids && subject.program_ids.includes(p.id) ? 'checked' : '';
            return `
                <label class="flex items-center gap-3 cursor-pointer group">
                    <input type="checkbox" name="edit_program_ids" value="${p.id}" ${isChecked} class="w-4 h-4 border-2 border-[var(--swiss-navy)] text-primary focus:ring-primary rounded-none"/>
                    <span class="text-[10px] font-black uppercase tracking-widest text-gray-500 group-hover:text-[var(--swiss-navy)]">${p.name} (${p.level})</span>
                </label>
            `;
        }).join('') || '<p class="text-[10px] uppercase font-bold text-gray-400">No Programs Found</p>';
        modal.classList.remove('hidden');
    } catch (err) {
        toast('Failed to load programs: ' + err.message, 'error');
    }
}

function closeEditSubjectModal() {
    document.getElementById('edit-subject-modal').classList.add('hidden');
}

async function saveSubjectEdit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-subject-id').value;
    const btn = document.getElementById('save-subject-edit-btn');
    const originalText = btn.textContent;
    btn.textContent = 'UPDATING...';
    btn.disabled = true;

    const checked = Array.from(document.querySelectorAll('#edit-subject-programs-list input[name="edit_program_ids"]:checked')).map(i => parseInt(i.value));

    const payload = {
        name: document.getElementById('edit-subject-name').value,
        code: document.getElementById('edit-subject-code').value,
        hours_per_week: parseInt(document.getElementById('edit-subject-hours').value),
        program_ids: checked
    };

    try {
        await api('PUT', `/subjects/${id}`, payload);
        toast('Subject updated successfully', 'success');
        closeEditSubjectModal();
        loadSubjects();
        loadStats();
    } catch (err) {
        toast(err.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function openAddSubjectModal() {
    const modal = document.getElementById('add-subject-modal');
    const container = document.getElementById('new-subject-programs-list');
    container.innerHTML = '<div class="spinner"></div>';
    
    try {
        const programs = await api('GET', '/programs');
        container.innerHTML = programs.map(p => `
            <label class="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" name="program_ids" value="${p.id}" class="w-4 h-4 border-2 border-[var(--swiss-navy)] text-primary focus:ring-primary rounded-none"/>
                <span class="text-[10px] font-black uppercase tracking-widest text-gray-500 group-hover:text-[var(--swiss-navy)]">${p.name} (${p.level})</span>
            </label>
        `).join('') || '<p class="text-[10px] uppercase font-bold text-gray-400">No Programs Found</p>';
        modal.classList.remove('hidden');
    } catch (err) {
        toast('Failed to load programs: ' + err.message, 'error');
    }
}

function closeAddSubjectModal() {
    document.getElementById('add-subject-modal').classList.add('hidden');
}

async function saveNewSubject(e) {
    e.preventDefault();
    const name = document.getElementById('new-subject-name').value;
    const code = document.getElementById('new-subject-code').value;
    const hours = parseInt(document.getElementById('new-subject-hours').value);
    const checked = Array.from(document.querySelectorAll('#new-subject-programs-list input[name="program_ids"]:checked')).map(i => parseInt(i.value));

    try {
        await api('POST', '/subjects', { name, code, hours_per_week: hours, program_ids: checked });
        toast('SUBJECT_CREATED', 'success');
        closeAddSubjectModal();
        loadSubjects();
        loadStats();
    } catch(e) { toast(e.message, 'error'); }
}

async function loadClassrooms() {
    const data = await api('GET', '/classrooms');
    const tb = document.getElementById('classrooms-tbody');
    if(!tb) return;
    tb.innerHTML = data.map(c => `
        <tr class="border-b border-gray-100 hover:bg-gray-50">
            <td class="px-8 py-6">
                <div class="font-black text-[var(--swiss-navy)] text-sm uppercase tracking-tight">${c.name}</div>
                <div class="text-[9px] text-gray-400 font-bold uppercase tracking-widest mt-1">CAPACITY: ${c.capacity} // TYPE: PHY_NODE</div>
            </td>
            <td class="px-8 py-6 text-right">
                <button onclick="deleteItem('classrooms', ${c.id})" class="text-gray-300 hover:text-[var(--swiss-red)]"><span class="material-symbols-outlined">delete</span></button>
            </td>
        </tr>
    `).join('');
}

async function loadTimeslots() {
    const data = await api('GET', '/timeslots');
    const tb = document.getElementById('timeslots-tbody');
    if(!tb) return;
    tb.innerHTML = data.map(s => `
        <tr class="border-b border-gray-100 hover:bg-gray-50">
            <td class="px-8 py-6">
                <div class="font-black text-[var(--swiss-navy)] text-sm uppercase tracking-tight">${s.day}</div>
                <div class="text-[9px] text-gray-400 font-black tracking-widest mt-1">${s.start_time} — ${s.end_time}</div>
            </td>
            <td class="px-8 py-6 text-right flex justify-end gap-2">
                <button onclick="openEditTimeslotModal(${JSON.stringify(s).replace(/"/g, '&quot;')})" class="w-10 h-10 text-gray-300 hover:text-[var(--swiss-navy)]"><span class="material-symbols-outlined">edit</span></button>
                <button onclick="deleteItem('timeslots', ${s.id})" class="text-gray-300 hover:text-[var(--swiss-red)]"><span class="material-symbols-outlined">delete</span></button>
            </td>
        </tr>
    `).join('');
}

// ── TIMESLOT MANAGEMENT ────────────────────────────────────────
function openEditTimeslotModal(slot) {
    document.getElementById('edit-timeslot-id').value = slot.id;
    document.getElementById('edit-timeslot-day').value = slot.day;
    document.getElementById('edit-timeslot-start').value = slot.start_time;
    document.getElementById('edit-timeslot-end').value = slot.end_time;
    document.getElementById('edit-timeslot-modal').classList.remove('hidden');
}

function closeEditTimeslotModal() {
    document.getElementById('edit-timeslot-modal').classList.add('hidden');
}

async function saveTimeslotEdit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-timeslot-id').value;
    const btn = document.getElementById('save-timeslot-edit-btn');
    const originalText = btn.textContent;
    btn.textContent = 'UPDATING...';
    btn.disabled = true;

    const payload = {
        day: document.getElementById('edit-timeslot-day').value,
        start_time: document.getElementById('edit-timeslot-start').value,
        end_time: document.getElementById('edit-timeslot-end').value
    };

    try {
        await api('PUT', `/timeslots/${id}`, payload);
        toast('Time slot updated successfully', 'success');
        closeEditTimeslotModal();
        loadTimeslots();
    } catch (err) {
        toast(err.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function loadStudents() {
    try {
        console.log("Fetching students...");
        const data = await api('GET', '/students');
        console.log("Students data received:", data);
        const tb = document.getElementById('students-tbody');
        if(!tb) {
            console.error("students-tbody not found in DOM");
            return;
        }
        
        if (!data || data.length === 0) {
            tb.innerHTML = '<tr><td colspan="4" class="p-40 text-center text-gray-200 font-black uppercase text-xs">NO_STAKEHOLDERS_DETECTED</td></tr>';
            return;
        }

        tb.innerHTML = data.map(s => {
            try {
                const sJson = JSON.stringify(s).replace(/"/g, '&quot;');
                return `
                    <tr class="border-b border-gray-100 hover:bg-gray-50">
                        <td class="px-8 py-6">
                            <div class="font-black text-[var(--swiss-navy)] text-sm uppercase tracking-tight">${s.full_name}</div>
                            <div class="text-[9px] text-gray-400 font-bold uppercase tracking-widest mt-1">${s.email}</div>
                        </td>
                        <td class="px-8 py-6 font-black text-gray-500 text-xs">${s.roll_no}</td>
                        <td class="px-8 py-6"><span class="error-tag bg-gray-100 text-gray-600">${s.program || 'PENDING'}</span></td>
                        <td class="px-8 py-6 text-right flex justify-end gap-2">
                            <button onclick="openEditStudentModal(${sJson})" class="w-10 h-10 text-gray-300 hover:text-[var(--swiss-navy)]"><span class="material-symbols-outlined">edit</span></button>
                            <button onclick="changePassword('students', ${s.id})" class="w-10 h-10 text-gray-300 hover:text-[var(--swiss-navy)]"><span class="material-symbols-outlined">key</span></button>
                            <button onclick="deleteItem('students', ${s.id})" class="w-10 h-10 text-gray-300 hover:text-[var(--swiss-red)]"><span class="material-symbols-outlined">delete</span></button>
                        </td>
                    </tr>
                `;
            } catch (err) {
                console.error("Error rendering student row:", err, s);
                return "";
            }
        }).join('');
    } catch (err) {
        console.error("Failed to load students:", err);
        toast('Failed to load students: ' + err.message, 'error');
    }
}

async function loadTimetable(pid = '') {
    const container = document.getElementById('admin-timetable-container');
    if(!container) return;
    container.innerHTML = '<div class="p-40 text-center"><div class="spinner"></div></div>';
    try {
        const data = await api('GET', pid ? `/timetable?program_id=${pid}` : '/timetable');
        if(!data.schedule.length) { container.innerHTML = `<div class="p-40 text-center text-gray-200 font-black uppercase text-xs">EMPTY_LOGIC_VOID</div>`; return; }
        
        container.innerHTML = `
            <table class="w-full text-left text-sm">
                <thead>
                    <tr class="bg-[var(--swiss-navy)] text-white">
                        <th class="px-8 py-6 font-black uppercase text-[10px] tracking-widest">Protocol</th>
                        <th class="px-8 py-6 font-black uppercase text-[10px] tracking-widest">temporal</th>
                        <th class="px-8 py-6 font-black uppercase text-[10px] tracking-widest">Vector</th>
                        <th class="px-8 py-6 font-black uppercase text-[10px] tracking-widest">Operator</th>
                        <th class="px-8 py-6 font-black uppercase text-[10px] tracking-widest">Node</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.schedule.map(e => `
                        <tr class="border-b border-gray-100 hover:bg-gray-50 transition-all">
                            <td class="px-8 py-6 font-black text-[var(--swiss-navy)] text-[10px] uppercase">${e.program || '—'}</td>
                            <td class="px-8 py-6 font-black uppercase text-[9px]">${e.day}<br/><span class="text-gray-400">${e.start_time}-${e.end_time}</span></td>
                            <td class="px-8 py-6">
                                <div class="font-black text-[var(--swiss-navy)] text-[10px] uppercase tracking-tight">${e.subject}</div>
                                <div class="text-[8px] text-[var(--swiss-red)] font-black mt-1 uppercase">${e.subject_code || ''}</div>
                            </td>
                            <td class="px-8 py-6 font-black text-gray-500 text-[10px] uppercase">${e.teacher}</td>
                            <td class="px-8 py-6"><span class="bg-[var(--swiss-gray)] text-[var(--swiss-navy)] px-3 py-1 font-black text-[9px] border-l-4 border-[var(--swiss-navy)] uppercase tracking-tighter">${e.classroom}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) { toast(e.message, 'error'); }
}

// ── HELPERS ───────────────────────────────────────────────────
async function api(method, path, body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' }, credentials: 'include' };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API + path, opts);
    let data;
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
        data = await res.json();
    } else {
        const text = await res.text();
        data = { error: text || res.statusText };
    }
    if (!res.ok) throw new Error(data.error || `Request failed with status ${res.status}`);
    return data;
}

function toast(msg, type='info') {
    const container = document.getElementById('toast-container');
    if(!container) return;
    const el = document.createElement('div');
    el.className = `px-8 py-4 shadow-2xl text-white text-[10px] font-black uppercase tracking-widest fade-up flex items-center gap-3 ${type === 'success' ? 'bg-[var(--swiss-navy)]' : (type === 'error' ? 'bg-[var(--swiss-red)]' : 'bg-black')}`;
    el.innerHTML = `<span class="material-symbols-outlined text-sm">${type === 'success' ? 'done_all' : 'priority_high'}</span><span>${msg}</span>`;
    container.appendChild(el);
    setTimeout(() => el.remove(), 4500);
}

function toggleSidebar() {
    const s = document.getElementById('admin-sidebar');
    if(s) s.classList.toggle('w-80');
    if(s) s.classList.toggle('w-0');
}

function togglePasswordVisibility(id, btn) {
    const input = document.getElementById(id);
    const icon = btn.querySelector('span');
    if(!input || !icon) return;
    const isPwd = input.type === 'password';
    input.type = isPwd ? 'text' : 'password';
    icon.textContent = isPwd ? 'visibility_off' : 'visibility';
}

async function loadProgramsDropdown() {
    const data = await api('GET', '/student/programs');
    const html = '<option value="">— SELECT PROTOCOL —</option>' + data.map(p => `<option value="${p.id}">${p.name.toUpperCase()} [${p.level.toUpperCase()}]</option>`).join('');
    ['auth-program', 'ga-program-id', 'timetable-filter-program'].forEach(id => {
        const el = document.getElementById(id); if(el) el.innerHTML = html;
    });
}

async function deleteItem(t, id) {
    if(!confirm(`Are you sure you want to delete this ${t}?`)) return;
    try { await api('DELETE', `/${t}/${id}`); toast('Successfully deleted', 'success'); showAdminPage(t); loadStats(); } catch(e) { toast(e.message, 'error'); }
}

async function logout() {
    try { await api('POST', '/auth/logout'); } catch(e){}
    currentUser = null;
    showView('role-selection');
}

async function seedDemoData() {
    if(!confirm('Reset database and load demo data? This will delete all current records.')) return;
    try { await api('POST', '/seed'); toast('Database Reset Successful', 'success'); loadStats(); loadProgramsDropdown(); } catch(e) { toast(e.message, 'error'); }
}

async function openModal(type) {
    if(type === 'program') {
        const name = prompt('Program Name:'); if(!name) return;
        const level = prompt('Academic Level (e.g. Undergraduate):', 'Undergraduate');
        try { await api('POST', '/programs', { name, level }); loadPrograms(); loadStats(); } catch(e) { toast(e.message, 'error'); }
    } else if(type === 'teacher') {
        const name = prompt('Faculty Name:'); if(!name) return;
        const email = prompt('Email Address:');
        const dept = prompt('Department:');
        try { await api('POST', '/teachers', { name, email, department: dept }); loadTeachers(); loadStats(); } catch(e) { toast(e.message, 'error'); }
    } else if(type === 'subject') {
        openAddSubjectModal();
    } else if(type === 'classroom') {
        const name = prompt('Room Name:'); if(!name) return;
        const cap = prompt('Room Capacity:', '40');
        try { await api('POST', '/classrooms', { name, capacity: parseInt(cap) }); loadClassrooms(); loadStats(); } catch(e) { toast(e.message, 'error'); }
    } else if(type === 'timeslot') {
        const day = prompt('Day (e.g. Monday):', 'Monday'); if(!day) return;
        const start = prompt('Start Time (HH:MM):', '09:00');
        const end = prompt('End Time (HH:MM):', '10:00');
        try { await api('POST', '/timeslots', { day, start_time: start, end_time: end }); loadTimeslots(); loadStats(); } catch(e) { toast(e.message, 'error'); }
    }
}

async function changePassword(type, id) {
    const newPwd = prompt("Enter new password (min 8 characters):");
    if(!newPwd || newPwd.length < 8) return toast("Password too short", "error");
    try { await api('PUT', `/${type}/${id}/password`, { password: newPwd }); toast('Password updated', 'success'); } catch(e) { toast(e.message, 'error'); }
}

async function activateTeacher(tid) {
    try { await api('POST', `/teachers/${tid}/activate`); toast('NODE_ONLINE', 'success'); loadTeachers(); } catch(e) { toast(e.message, 'error'); }
}

async function exportPortalPDF() { window.open(API + '/export/pdf', '_blank'); }
async function exportExcel() {
    const pid = document.getElementById('timetable-filter-program').value;
    window.location.href = API + `/export/excel${pid ? '?program_id=' + pid : ''}`;
}
async function exportPDF() {
    const pid = document.getElementById('timetable-filter-program').value;
    window.location.href = API + `/export/pdf${pid ? '?program_id=' + pid : ''}`;
}

function filterTimetable(q) {
    const rows = document.querySelectorAll('#admin-timetable-container tbody tr');
    const query = q.toLowerCase();
    rows.forEach(r => r.style.display = r.innerText.toLowerCase().includes(query) ? '' : 'none');
}

// ── INIT ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Silently check session
        const res = await fetch(API + '/auth/whoami', { credentials: 'include' });
        if (!res.ok) throw new Error('Not logged in');
        
        const me = await res.json();
        currentRole = me.role; currentUser = me.user;
        if(currentRole === 'admin') { showView('admin'); showAdminPage('dashboard'); }
        else { showView('portal'); loadPortal(); }
    } catch(e) { showView('role-selection'); }
});

// ── STUDENT MANAGEMENT ─────────────────────────────────────────
async function openEditStudentModal(student) {
    const modal = document.getElementById('edit-student-modal');
    const select = document.getElementById('edit-student-program');
    
    document.getElementById('edit-student-id').value = student.id;
    document.getElementById('edit-student-name').value = student.full_name;
    document.getElementById('edit-student-email').value = student.email;
    document.getElementById('edit-student-roll').value = student.roll_no;
    
    // Clear previous options
    select.innerHTML = '<option value="">Select a Program</option>';
    
    try {
        const programs = await api('GET', '/programs');
        programs.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.name} (${p.level})`;
            if (p.id === student.program_id) opt.selected = true;
            select.appendChild(opt);
        });
        modal.classList.remove('hidden');
    } catch (err) {
        toast('Failed to load programs: ' + err.message, 'error');
    }
}

function closeEditStudentModal() {
    document.getElementById('edit-student-modal').classList.add('hidden');
}

async function saveStudentEdit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-student-id').value;
    const btn = document.getElementById('save-student-edit-btn');
    const originalText = btn.textContent;
    btn.textContent = 'UPDATING...';
    btn.disabled = true;

    const payload = {
        full_name: document.getElementById('edit-student-name').value,
        email: document.getElementById('edit-student-email').value,
        roll_no: document.getElementById('edit-student-roll').value,
        program_id: document.getElementById('edit-student-program').value ? parseInt(document.getElementById('edit-student-program').value) : null
    };

    try {
        await api('PUT', `/students/${id}`, payload);
        toast('Student updated successfully', 'success');
        closeEditStudentModal();
        loadStudents();
        e.target.reset();
    } catch (err) {
        toast(err.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function openAddStudentModal() {
    const modal = document.getElementById('add-student-modal');
    const select = document.getElementById('new-student-program');
    
    // Clear previous options
    select.innerHTML = '<option value="">Select a Program</option>';
    
    try {
        const programs = await api('GET', '/programs');
        programs.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.name} (${p.level})`;
            select.appendChild(opt);
        });
        modal.classList.remove('hidden');
    } catch (err) {
        toast('Failed to load programs: ' + err.message, 'error');
    }
}

function closeAddStudentModal() {
    document.getElementById('add-student-modal').classList.add('hidden');
}

async function saveNewStudent(e) {
    e.preventDefault();
    const btn = document.getElementById('save-student-btn');
    const originalText = btn.textContent;
    btn.textContent = 'REGISTERING...';
    btn.disabled = true;

    const payload = {
        full_name: document.getElementById('new-student-name').value,
        email: document.getElementById('new-student-email').value,
        roll_no: document.getElementById('new-student-roll').value,
        program_id: document.getElementById('new-student-program').value ? parseInt(document.getElementById('new-student-program').value) : null,
        password: 'password123' // Default password for admin-created students
    };

    try {
        await api('POST', '/students', payload);
        toast('Student registered successfully', 'success');
        closeAddStudentModal();
        loadStudents(); // Refresh the list
        loadStats();    // Refresh dashboard stats
        e.target.reset();
    } catch (err) {
        toast(err.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}
