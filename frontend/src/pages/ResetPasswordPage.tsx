import { useState, FormEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import api from '../utils/api';
import toast from 'react-hot-toast';

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const prefilled = (location.state as { email?: string })?.email || '';

  const [form, setForm] = useState({
    email:       prefilled,
    code:        '',
    newPassword: '',
    confirm:     '',
  });
  const [loading, setLoading] = useState(false);
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (form.newPassword !== form.confirm) {
      toast.error('Passwords do not match'); return;
    }
    if (form.newPassword.length < 12) {
      toast.error('Password must be at least 12 characters'); return;
    }
    setLoading(true);
    try {
      await api.post('/auth/confirm-password', {
        email:       form.email.trim().toLowerCase(),
        code:        form.code.trim(),
        newPassword: form.newPassword,
      });
      toast.success('Password reset successful! You can now log in.');
      navigate('/login');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })
        ?.response?.data?.error ?? 'Password reset failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <span className="text-3xl">🔒</span>
          </div>
          <h1 className="text-3xl font-bold text-white">Reset Password</h1>
          <p className="text-blue-200 mt-1">Enter the code from your email and a new password</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={form.email} onChange={set('email')}
                placeholder="your@email.com" className="input-field" required />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reset Code (from email)
              </label>
              <input
                type="text"
                value={form.code}
                onChange={(e) => setForm(f => ({ ...f, code: e.target.value.replace(/\D/g,'').slice(0,6) }))}
                placeholder="6-digit code"
                className="input-field text-center text-2xl font-bold tracking-widest"
                maxLength={6}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
              <input type="password" value={form.newPassword} onChange={set('newPassword')}
                placeholder="Min 12 chars, upper, lower, number, symbol"
                className="input-field" required />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
              <input type="password" value={form.confirm} onChange={set('confirm')}
                placeholder="Repeat new password" className="input-field" required />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3 text-base mt-2">
              {loading ? 'Resetting…' : 'Reset Password'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Remember your password?{' '}
            <Link to="/login" className="text-brand-600 font-medium hover:text-brand-700">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
