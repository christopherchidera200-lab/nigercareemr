import { useState, FormEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import api from '../utils/api';
import toast from 'react-hot-toast';

export default function ConfirmPage() {
  const navigate  = useNavigate();
  const location  = useLocation();

  // Pre-fill email if passed from register page
  const prefilled = (location.state as { email?: string })?.email || '';

  const [email, setEmail]   = useState(prefilled);
  const [code, setCode]     = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!email || !code) { toast.error('Enter your email and the code'); return; }
    setLoading(true);
    try {
      await api.post('/auth/confirm', { email: email.trim().toLowerCase(), code: code.trim() });
      toast.success('Email confirmed! You can now log in.');
      navigate('/login');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })
        ?.response?.data?.error ?? 'Confirmation failed. Check your code.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function resendCode() {
    if (!email) { toast.error('Enter your email first'); return; }
    try {
      await api.post('/auth/resend-code', { email: email.trim().toLowerCase() });
      toast.success('New code sent! Check your inbox and spam folder.');
    } catch {
      toast.error('Failed to resend code');
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <span className="text-3xl">📧</span>
          </div>
          <h1 className="text-3xl font-bold text-white">Verify Your Email</h1>
          <p className="text-blue-200 mt-1">Enter the 6-digit code sent to your email</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-700">
              📬 Check your <strong>inbox and spam folder</strong> for an email from NigerCare EMR with your verification code.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Verification Code
              </label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="6-digit code e.g. 966156"
                className="input-field text-center text-2xl font-bold tracking-widest"
                maxLength={6}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 text-base"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Confirming…
                </span>
              ) : 'Confirm My Account'}
            </button>
          </form>

          <div className="mt-6 text-center space-y-3">
            <p className="text-sm text-gray-500">
              Didn't receive the code?{' '}
              <button
                onClick={resendCode}
                className="text-brand-600 font-medium hover:text-brand-700"
              >
                Resend code
              </button>
            </p>
            <p className="text-sm text-gray-500">
              Already confirmed?{' '}
              <Link to="/login" className="text-brand-600 font-medium hover:text-brand-700">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
