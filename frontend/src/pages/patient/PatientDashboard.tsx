import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import api from '../../utils/api';
import Sidebar from '../../components/shared/Sidebar';
import StatCard from '../../components/shared/StatCard';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import { useAuth } from '../../hooks/useAuth';
import toast from 'react-hot-toast';
import { Appointment, MedicalRecord, Notification } from '../../types';

const NAV = [
  { label: 'My Health',       to: '/patient',               icon: '🏥' },
  { label: 'Appointments',    to: '/patient/appointments',   icon: '📅' },
  { label: 'Medical Records', to: '/patient/records',        icon: '📋' },
  { label: 'Notifications',   to: '/patient/notifications',  icon: '🔔' },
  { label: 'Upload Documents',to: '/patient/uploads',        icon: '📎' },
];

function PatientOverview() {
  const { user } = useAuth();
  const [appts, setAppts]           = useState<Appointment[]>([]);
  const [notifications, setNotifs]  = useState<Notification[]>([]);
  const [loading, setLoading]       = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/appointments'),
      api.get('/notifications'),
    ]).then(([ar, nr]) => {
      setAppts(ar.data.appointments ?? []);
      setNotifs(nr.data.notifications ?? []);
    }).catch(() => toast.error('Failed to load data'))
      .finally(() => setLoading(false));
  }, []);

  const upcoming = appts.filter(a =>
    ['PENDING','CONFIRMED'].includes(a.status) &&
    new Date(a.appointment_date) >= new Date()
  );
  const unread = notifications.filter(n => !n.is_read);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Hello, {user?.name?.split(' ')[0]} 👋</h1>
        <p className="text-gray-500 text-sm mt-1">Here's your health summary</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Upcoming Appointments" value={upcoming.length}    icon="📅" color="blue" />
        <StatCard title="Unread Notifications"  value={unread.length}     icon="🔔" color="amber" />
        <StatCard title="Total Appointments"    value={appts.length}      icon="📊" color="green" />
      </div>

      {/* Upcoming */}
      <div className="card">
        <h2 className="font-semibold text-gray-700 mb-4">Upcoming Appointments</h2>
        {upcoming.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">No upcoming appointments</p>
        ) : (
          <div className="space-y-3">
            {upcoming.slice(0, 5).map(a => (
              <div key={a.appointment_id}
                className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-100">
                <div>
                  <p className="text-sm font-medium text-gray-800">{a.reason}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {new Date(a.appointment_date).toLocaleString('en-NG', { dateStyle:'medium', timeStyle:'short' })}
                    {' · '}{a.type}
                  </p>
                </div>
                <span className={a.status === 'CONFIRMED' ? 'badge-success' : 'badge-warning'}>
                  {a.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notifications */}
      {unread.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-4">Unread Notifications</h2>
          <div className="space-y-2">
            {unread.slice(0, 5).map(n => (
              <div key={n.notification_id}
                className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
                <span className="text-lg">🔔</span>
                <div>
                  <p className="text-sm font-medium text-gray-800">{n.title}</p>
                  <p className="text-xs text-gray-500">{n.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BookAppointment() {
  const [appts, setAppts]     = useState<Appointment[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading]   = useState(true);
  const { user } = useAuth();
  const [form, setForm] = useState({
    doctor_id: '', appointment_date: '', reason: '', type: 'IN_PERSON', notes: '',
  });

  useEffect(() => {
    api.get('/appointments')
      .then(r => setAppts(r.data.appointments ?? []))
      .catch(() => toast.error('Failed to load appointments'))
      .finally(() => setLoading(false));
  }, []);

  async function book(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post('/appointments', { ...form, patient_id: user?.sub });
      toast.success('Appointment booked! Awaiting confirmation.');
      setShowForm(false);
      const r = await api.get('/appointments');
      setAppts(r.data.appointments ?? []);
    } catch { toast.error('Failed to book appointment'); }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">My Appointments</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? 'Cancel' : '+ Book Appointment'}
        </button>
      </div>

      {showForm && (
        <div className="card">
          <h3 className="font-semibold mb-4">Book New Appointment</h3>
          <form onSubmit={book} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doctor ID</label>
                <input className="input-field" required placeholder="Enter doctor ID"
                  value={form.doctor_id}
                  onChange={e => setForm(f => ({...f, doctor_id: e.target.value}))} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date & Time</label>
                <input type="datetime-local" className="input-field" required
                  value={form.appointment_date}
                  onChange={e => setForm(f => ({...f, appointment_date: e.target.value}))} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Visit Type</label>
                <select className="input-field" value={form.type}
                  onChange={e => setForm(f => ({...f, type: e.target.value}))}>
                  <option value="IN_PERSON">In Person</option>
                  <option value="TELEMEDICINE">Telemedicine</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                <input className="input-field" required placeholder="Reason for visit"
                  value={form.reason}
                  onChange={e => setForm(f => ({...f, reason: e.target.value}))} />
              </div>
            </div>
            <button type="submit" className="btn-primary">Book Appointment</button>
          </form>
        </div>
      )}

      <div className="space-y-3">
        {appts.length === 0 && <p className="text-gray-400 text-sm text-center py-8">No appointments yet</p>}
        {appts.map(a => (
          <div key={a.appointment_id} className="card flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800">{a.reason}</p>
              <p className="text-sm text-gray-500 mt-0.5">
                {new Date(a.appointment_date).toLocaleString('en-NG', { dateStyle:'medium', timeStyle:'short' })}
                {' · '}{a.type} · {a.duration_minutes}min
              </p>
            </div>
            <span className={
              a.status === 'CONFIRMED' ? 'badge-success' :
              a.status === 'PENDING'   ? 'badge-warning' :
              a.status === 'CANCELLED' ? 'badge-danger'  :
              a.status === 'COMPLETED' ? 'badge-neutral' : 'badge-info'
            }>{a.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function PatientRecords() {
  const { user } = useAuth();
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.sub) return;
    api.get(`/records?patient_id=${user.sub}`)
      .then(r => setRecords(r.data.records ?? []))
      .catch(() => toast.error('Failed to load records'))
      .finally(() => setLoading(false));
  }, [user?.sub]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">My Medical Records</h1>
      {records.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-4xl mb-3">📋</p>
          <p className="text-gray-500">No medical records yet</p>
        </div>
      ) : (
        records.map(r => (
          <div key={r.record_id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge-info">{r.record_type}</span>
                </div>
                <h3 className="font-semibold text-gray-800">{r.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{r.content}</p>
                <p className="text-xs text-gray-400 mt-2">Dr. {r.doctor_name}</p>
              </div>
              <p className="text-xs text-gray-400 ml-4 whitespace-nowrap">
                {new Date(r.created_at).toLocaleDateString('en-NG')}
              </p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function PatientNotifications() {
  const [notifs, setNotifs] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/notifications')
      .then(r => setNotifs(r.data.notifications ?? []))
      .catch(() => toast.error('Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  async function markRead(id: string, createdAt: string) {
    try {
      await api.put(`/notifications/${id}/read`, {});
      setNotifs(prev => prev.map(n => n.notification_id === id ? {...n, is_read: true} : n));
    } catch { toast.error('Failed to mark read'); }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Notifications</h1>
      {notifs.length === 0 && <p className="text-gray-400 text-center py-8">No notifications</p>}
      {notifs.map(n => (
        <div key={n.notification_id}
          className={`card border-l-4 ${n.is_read ? 'border-gray-200 opacity-60' : 'border-brand-500'}`}>
          <div className="flex items-start justify-between">
            <div>
              <p className="font-medium text-gray-800">{n.title}</p>
              <p className="text-sm text-gray-600 mt-1">{n.message}</p>
              <p className="text-xs text-gray-400 mt-2">
                {new Date(n.created_at).toLocaleString('en-NG')}
              </p>
            </div>
            {!n.is_read && (
              <button onClick={() => markRead(n.notification_id, n.created_at)}
                className="text-xs text-brand-600 hover:text-brand-700 font-medium ml-4 whitespace-nowrap">
                Mark read
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function PatientDashboard() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar navItems={NAV} portalName="Patient Portal" />
      <main className="flex-1 p-6 overflow-auto">
        <Routes>
          <Route index                   element={<PatientOverview />} />
          <Route path="appointments"     element={<BookAppointment />} />
          <Route path="records"          element={<PatientRecords />} />
          <Route path="notifications"    element={<PatientNotifications />} />
          <Route path="*"                element={<PatientOverview />} />
        </Routes>
      </main>
    </div>
  );
}
