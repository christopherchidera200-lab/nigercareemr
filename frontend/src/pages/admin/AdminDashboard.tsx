import { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import Sidebar from '../../components/shared/Sidebar';
import StatCard from '../../components/shared/StatCard';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import toast from 'react-hot-toast';
import { DashboardStats, Patient, Doctor } from '../../types';

const NAV = [
  { label: 'Dashboard',   to: '/admin',          icon: '📊' },
  { label: 'Patients',    to: '/admin/patients',  icon: '👥' },
  { label: 'Doctors',     to: '/admin/doctors',   icon: '👨‍⚕️' },
  { label: 'Appointments',to: '/admin/appointments', icon: '📅' },
  { label: 'Audit Logs',  to: '/admin/audit',     icon: '🔍' },
  { label: 'Users',       to: '/admin/users',     icon: '⚙️' },
];

// ── Overview ──────────────────────────────────────────────────────────────────
function Overview() {
  const [stats, setStats]   = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/admin/stats')
      .then(r => setStats(r.data))
      .catch(() => toast.error('Failed to load stats'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Admin Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">
          NigerCare Medical Centre · {new Date().toLocaleDateString('en-NG', { dateStyle: 'full' })}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Active Patients"     value={stats?.active_patients ?? 0}    icon="🧑‍🤝‍🧑" color="blue"   subtitle="Registered & active" />
        <StatCard title="Total Doctors"       value={stats?.total_doctors ?? 0}      icon="👨‍⚕️"  color="green"  subtitle="On staff" />
        <StatCard title="Appointments Today"  value={stats?.appointments_today ?? 0} icon="📅"   color="amber"  subtitle="Scheduled for today" />
        <StatCard title="Pending Approvals"   value={stats?.pending_approvals ?? 0}  icon="⏳"   color="red"    subtitle="Awaiting confirmation" />
      </div>

      <div className="card">
        <h2 className="text-base font-semibold text-gray-700 mb-4">System Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          {[
            { label: 'API Gateway',      status: 'Operational', color: 'green' },
            { label: 'DynamoDB',         status: 'Operational', color: 'green' },
            { label: 'S3 Storage',       status: 'Operational', color: 'green' },
            { label: 'Cognito Auth',     status: 'Operational', color: 'green' },
            { label: 'CloudFront CDN',   status: 'Operational', color: 'green' },
            { label: 'Notifications',    status: 'Operational', color: 'green' },
          ].map(s => (
            <div key={s.label} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-medium text-gray-700">{s.label}</span>
              <span className={`badge-success`}>✓ {s.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Patients List ─────────────────────────────────────────────────────────────
function PatientsPanel() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');

  useEffect(() => {
    api.get('/patients')
      .then(r => setPatients(r.data.patients ?? []))
      .catch(() => toast.error('Failed to load patients'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = patients.filter(p =>
    `${p.firstName} ${p.lastName} ${p.email} ${p.phone}`
      .toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Patients ({patients.length})</h1>
      </div>
      <input value={search} onChange={e => setSearch(e.target.value)}
        placeholder="Search by name, email or phone…" className="input-field max-w-sm" />
      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['Name', 'DOB', 'Gender', 'Phone', 'Blood', 'Status'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.length === 0 && (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">No patients found</td></tr>
            )}
            {filtered.map(p => (
              <tr key={p.patient_id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-800">{p.firstName} {p.lastName}</td>
                <td className="px-4 py-3 text-gray-500">{p.dateOfBirth}</td>
                <td className="px-4 py-3 text-gray-500">{p.gender}</td>
                <td className="px-4 py-3 text-gray-500">{p.phone}</td>
                <td className="px-4 py-3">
                  {p.bloodGroup ? <span className="badge-info">{p.bloodGroup}</span> : '—'}
                </td>
                <td className="px-4 py-3">
                  <span className={p.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}>
                    {p.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Doctors List ──────────────────────────────────────────────────────────────
function DoctorsPanel() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name:'', specialty:'', email:'', phone:'', license_number:'' });
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/admin/doctors')
      .then(r => setDoctors(r.data.doctors ?? []))
      .catch(() => toast.error('Failed to load doctors'))
      .finally(() => setLoading(false));
  }, []);

  async function addDoctor(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post('/admin/doctors', form);
      toast.success('Doctor added');
      setShowForm(false);
      setForm({ name:'', specialty:'', email:'', phone:'', license_number:'' });
      const r = await api.get('/admin/doctors');
      setDoctors(r.data.doctors ?? []);
    } catch { toast.error('Failed to add doctor'); }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Doctors ({doctors.length})</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? 'Cancel' : '+ Add Doctor'}
        </button>
      </div>

      {showForm && (
        <div className="card">
          <h3 className="font-semibold mb-4">New Doctor Profile</h3>
          <form onSubmit={addDoctor} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              ['name','Full Name','Dr. Amara Obi'],
              ['specialty','Specialty','Cardiology'],
              ['email','Email','dr.obi@nigercaremedicals.com'],
              ['phone','Phone','+234 800 000 0000'],
              ['license_number','License #','MDCN-12345'],
            ].map(([k, label, ph]) => (
              <div key={k}>
                <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                <input className="input-field" placeholder={ph} required
                  value={(form as Record<string,string>)[k]}
                  onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))} />
              </div>
            ))}
            <div className="sm:col-span-2 flex gap-3">
              <button type="submit" className="btn-primary">Save Doctor</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['Name','Specialty','Email','Phone','License','Status'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {doctors.length === 0 && (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">No doctors found</td></tr>
            )}
            {doctors.map(d => (
              <tr key={d.doctor_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{d.name}</td>
                <td className="px-4 py-3 text-gray-500">{d.specialty}</td>
                <td className="px-4 py-3 text-gray-500">{d.email}</td>
                <td className="px-4 py-3 text-gray-500">{d.phone}</td>
                <td className="px-4 py-3 text-gray-500">{d.license_number}</td>
                <td className="px-4 py-3">
                  <span className={d.status === 'ACTIVE' ? 'badge-success' : 'badge-neutral'}>{d.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Audit Logs ────────────────────────────────────────────────────────────────
function AuditPanel() {
  const [logs, setLogs]     = useState<Record<string,string>[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/admin/audit')
      .then(r => setLogs(r.data.logs ?? []))
      .catch(() => toast.error('Failed to load audit logs'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Audit Logs</h1>
      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {['Timestamp','User','Action','Resource'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {logs.length === 0 && (
              <tr><td colSpan={4} className="text-center py-8 text-gray-400">No audit logs</td></tr>
            )}
            {logs.map((l, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                  {new Date(l.timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-gray-700">{l.user_id}</td>
                <td className="px-4 py-3"><span className="badge-info">{l.action}</span></td>
                <td className="px-4 py-3 text-gray-500 text-xs truncate max-w-xs">{l.resource}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Layout shell ──────────────────────────────────────────────────────────────
export default function AdminDashboard() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar navItems={NAV} portalName="Admin Portal" />
      <main className="flex-1 p-6 overflow-auto">
        <Routes>
          <Route index         element={<Overview />} />
          <Route path="patients"    element={<PatientsPanel />} />
          <Route path="doctors"     element={<DoctorsPanel />} />
          <Route path="audit"       element={<AuditPanel />} />
          <Route path="*"           element={<Overview />} />
        </Routes>
      </main>
    </div>
  );
}
