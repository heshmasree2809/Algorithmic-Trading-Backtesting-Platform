import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, register } from '../services/api';
import { useAuthStore } from '../store/authStore';

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const setToken = useAuthStore((s) => s.setToken);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === 'register') {
        await register(email, password, fullName);
      }
      const { access_token } = await login(email, password);
      setToken(access_token);
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-terminal-bg">
      <div className="card w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="text-terminal-accent font-bold text-2xl tracking-tight">QuantX</div>
          <div className="text-xs text-terminal-muted uppercase tracking-wider">
            Algorithmic Trading Research Platform
          </div>
        </div>

        <div className="flex mb-4 border border-terminal-border rounded-md overflow-hidden text-sm">
          <button
            className={`flex-1 py-2 ${mode === 'login' ? 'bg-terminal-accent/10 text-terminal-accent' : 'text-terminal-muted'}`}
            onClick={() => setMode('login')}
          >
            Sign In
          </button>
          <button
            className={`flex-1 py-2 ${mode === 'register' ? 'bg-terminal-accent/10 text-terminal-accent' : 'text-terminal-muted'}`}
            onClick={() => setMode('register')}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {mode === 'register' && (
            <div>
              <label className="label">Full Name</label>
              <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
          )}
          <div>
            <label className="label">Email</label>
            <input
              type="email" required className="input" value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password" required minLength={8} className="input" value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-terminal-danger text-xs">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <p className="text-[10px] text-terminal-muted mt-6 text-center leading-snug">
          Research &amp; simulation only. QuantX never executes real trades and does not
          provide personalized investment advice.
        </p>
      </div>
    </div>
  );
}
