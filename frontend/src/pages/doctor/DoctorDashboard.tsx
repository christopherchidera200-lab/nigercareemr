import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import api from '../../utils/api';
import Sidebar from '../../components/shared/Sidebar';
import StatCard from '../../components/shared/StatCard';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import { useAuth } from '../../hooks/useAuth';
import toast from 'react-hot-toast';
import { Appointment, Patient, MedicalRecord } from '../../types';

const NAV = [
  { label: 'Dashboard',     to: '/doctor',                icon: '📊' },
  { label: 'My Schedule',   to: '/doctor/appointments',   icon: '📅' },
  { label: 'Patients',      to: '/doctor/patients',       icon: '👥' },
  { label: 'Medical Records',to: '/doctor/records',       icon: '📋' },
  { label: 'Notifications', to: '/doctor/notifications',  icon: '🔔' },
];

function DoctorOverview() {
  const { user }  = useAuth();
  const [appts, setAppts]   = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/appointments')
      .then(r => setAppts(r.data.appointments ?? []))
      .catch(() => toast.error('Failed to load appointments'))
      .finally(() => setLoading(false));
  }, []);

  const today   = new Date().toISOString().split('T')[0];
  const todayAppts  = appts.filter(a => a.appointment_date?.startsWith(today));
  const pending     = appts.filter(a => a.status === 'PENDING');
  const confirmed   = appts.filter(a => a.status === 'CONFIRMED');

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Good morning, {user?.name?.split(' ')[0]} 👋</h1>
        <p className="text-gray-500 text-sm mt-1">
          {new Date().toLocaleDateString('en-NG', { dateStyle: 'full' })}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Today's Appointments" value={todayAppts.length}  icon="📅" color="blue" />
        <StatCard title="Pending"              value={pending.length}     icon="⏳" color="amber" />
        <StatCard title="Confirmed"            value={confirmed.length}   icon="✅" color="green" />
      </div>

      <div className="card">
        <h2 className="text-base font-semibold text-gray-700 mb-4">Today's Schedule</h2>
        {todayAppts.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-6">No appointments scheduled for today</p>
        ) : (
          <div className="space-y-3">
            {todayAppts.map(a => (
              <div key={a.appointment_id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100">
                <div>
                  <p className="text-sm font-medium text-gray-800">{a.reason}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{a.patient_id} · {a.type}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">{a.duration_minutes}min</span>
                  <span className={
                    a.status === 'CONFIRMED' ? 'badge-success' :
                    a.status === 'PENDING'   ? 'badge-warning' :
                    a.status === 'CANCELLED' ? 'badge-danger'  : 'badge-neutral'
                  }>{a.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AppointmentsPanel() {
  const [appts, setAppts] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/appointments')
      .then(r => setAppts(r.data.appointments ?? []))
      .catch(() => toast.error('Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  async function updateStatus(appt: Appointment, status: string) {
    try {
      await api.put(`/appointments/${appt.appointment_id}`, { status });
      setAppts(prev => prev.map(a =>
        a.appointment_id === appt.appointment_id ? { ...a, status: status as Appointment['status'] } : a
      ));
      toast.success(`Appointment ${status.toLowerCase()}`);
    } catch { toast.error('Update failed'); }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">My Appointments</h1>
      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {['Date & Time','Patient','Reason','Type','Status','Actions'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {appts.length === 0 && (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">No appointments</td></tr>
            )}
            {appts.map(a => (
              <tr key={a.appointment_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                  {new Date(a.appointment_date).toLocaleString('en-NG', { dateStyle:'short', timeStyle:'short' })}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{a.patient_id.slice(0, 8)}…</td>
                <td className="px-4 py-3 text-gray-700 max-w-xs truncate">{a.reason}</td>
                <td className="px-4 py-3"><span className="badge-info">{a.type}</span></td>
                <td className="px-4 py-3">
                  <span className={
                    a.status === 'CONFIRMED' ? 'badge-success' :
                    a.status === 'PENDING'   ? 'badge-warning' :
                    a.status === 'CANCELLED' ? 'badge-danger'  :
                    a.status === 'COMPLETED' ? 'badge-neutral' : 'badge-info'
                  }>{a.status}</span>
                </td>
                <td className="px-4 py-3">
                  {a.status === 'PENDING' && (
                    <div className="flex gap-2">
                      <button onClick={() => updateStatus(a, 'CONFIRMED')}
                        className="text-xs text-green-600 hover:text-green-700 font-medium">Confirm</button>
                      <button onClick={() => updateStatus(a, 'CANCELLED')}
                        className="text-xs text-red-500 hover:text-red-600 font-medium">Cancel</button>
                    </div>
                  )}
                  {a.status === 'CONFIRMED' && (
                    <button onClick={() => updateStatus(a, 'COMPLETED')}
                      className="text-xs text-blue-600 hover:text-blue-700 font-medium">Complete</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RecordsPanel() {
  const [patientId, setPatientId] = useState('');
  const [records, setRecords]     = useState<MedicalRecord[]>([]);
  const [loading, setLoading]     = useState(false);
  const [showForm, setShowForm]   = useState(false);
  const { user } = useAuth();
  const [form, setForm] = useState({
    patient_id: '', record_type: 'DIAGNOSIS', title: '', content: '',
  });

  async function loadRecords() {
    if (!patientId.trim()) return;
    setLoading(true);
    try {
      const r = await api.get(`/records?patient_id=${patientId}`);
      setRecords(r.data.records ?? []);
    } catch { toast.error('Failed to load records'); }
    finally { setLoading(false); }
  }

  async function addRecord(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post('/records', form);
      toast.success('Record created');
      setShowForm(false);
      loadRecords();
    } catch { toast.error('Failed to create record'); }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Medical Records</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? 'Cancel' : '+ New Record'}
        </button>
      </div>

      <div className="flex gap-3">
        <input value={patientId} onChange={e => setPatientId(e.target.value)}
          placeholder="Enter Patient ID…" className="input-field max-w-sm" />
        <button onClick={loadRecords} className="btn-secondary">Search</button>
      </div>

      {showForm && (
        <div className="card">
          <h3 className="font-semibold mb-4">Create Medical Record</h3>
          <form onSubmit={addRecord} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patient ID</label>
                <input className="input-field" required value={form.patient_id}
                  onChange={e => setForm(f => ({...f, patient_id: e.target.value}))} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Record Type</label>
                <select className="input-field" value={form.record_type}
                  onChange={e => setForm(f => ({...f, record_type: e.target.value}))}>
                  {['DIAGNOSIS','LAB_RESULT','PRESCRIPTION','NOTE','IMAGING','PROCEDURE'].map(t => (
                    <option key={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input className="input-field" required value={form.title}
                onChange={e => setForm(f => ({...f, title: e.target.value}))} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Content / Notes</label>
              <textarea className="input-field h-28 resize-none" required value={form.content}
                onChange={e => setForm(f => ({...f, content: e.target.value}))} />
            </div>
            <button type="submit" className="btn-primary">Save Record</button>
          </form>
        </div>
      )}

      {loading && <LoadingSpinner />}

      {!loading && records.length > 0 && (
        <div className="space-y-3">
          {records.map(r => (
            <div key={r.record_id} className="card">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="badge-info">{r.record_type}</span>
                    {r.is_confidential && <span className="badge-danger">Confidential</span>}
                  </div>
                  <h3 className="font-semibold text-gray-800">{r.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{r.content}</p>
                </div>
                <p className="text-xs text-gray-400 whitespace-nowrap ml-4">
                  {new Date(r.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DoctorDashboard() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar navItems={NAV} portalName="Doctor Portal" />
      <main className="flex-1 p-6 overflow-auto">
        <Routes>
          <Route index                   element={<DoctorOverview />} />
          <Route path="appointments"     element={<AppointmentsPanel />} />
          <Route path="records"          element={<RecordsPanel />} />
          <Route path="*"                element={<DoctorOverview />} />
        </Routes>
      </main>
    </div>
  );
}
