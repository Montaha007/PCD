import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Galaxy from '../../component/Galaxy';
import SpotlightCard from '../../component/SpotlightCard';
import './accounts.css';

function MoonIcon({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path
        d="M14.2 3.3a8.8 8.8 0 1 0 6.5 14.7A9.5 9.5 0 0 1 14.2 3.3Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconMail({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M5 7h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.8" />
      <path d="m4 9 8 6 8-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconLock({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8.8 11V8.9a3.2 3.2 0 0 1 6.4 0V11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

const API_BASE = 'http://localhost:8000';

export default function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/accounts/api/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        navigate('/dashboard');
      } else {
        setError(data.error || 'Invalid credentials. Please try again.');
      }
    } catch {
      setError('Network error. Make sure the Django server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="accounts-page">
      {/* Galaxy background */}
      <div className="accounts-galaxy" aria-hidden="true">
        <Galaxy
          starSpeed={0.5}
          density={0.8}
          hueShift={140}
          speed={0.1}
          glowIntensity={0.3}
          saturation={0}
          mouseRepulsion
          trackCursorGlobally
          repulsionStrength={2}
          twinkleIntensity={0.3}
          rotationSpeed={0.1}
          transparent
        />
      </div>

      <SpotlightCard className="custom-spotlight-card custom-spotlight-card--narrow" spotlightColor="rgba(0, 229, 255, 0.2)">
        {/* Header */}
        <div className="accounts-header">
          <div className="accounts-logo-icon">
            <MoonIcon className="accounts-mark" />
          </div>
          <div className="accounts-eyebrow">Sleep &amp; Wellness</div>
          <h1>Welcome Back</h1>
          <p>Sign in to continue your sleep journey</p>
        </div>

        {error && <div className="accounts-error">{error}</div>}

        <form onSubmit={handleSubmit} className="accounts-form">
          <div className="form-group">
            <label htmlFor="email"><IconMail className="field-icon field-icon--aqua" /> Email</label>
            <input
              id="email"
              type="email"
              name="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="you@example.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password"><IconLock className="field-icon field-icon--lavender" /> Password</label>
            <input
              id="password"
              type="password"
              name="password"
              required
              value={formData.password}
              onChange={handleChange}
              placeholder="Your password"
            />
          </div>

          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In →'}
          </button>
        </form>

        <div className="accounts-divider">or</div>

        <p className="accounts-footer-text">
          Don&apos;t have an account?{' '}
          <Link to="/register">Create one free</Link>
        </p>
      </SpotlightCard>
    </div>
  );
}
