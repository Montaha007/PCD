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

function IconUser({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M12 12a4.2 4.2 0 1 0 0-8.4A4.2 4.2 0 0 0 12 12Z" stroke="currentColor" strokeWidth="1.8" />
      <path d="M4.6 20.4a7.4 7.4 0 0 1 14.8 0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconCalendar({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M7 3.8h10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M7 7h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8 11h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconGender({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M12 13.8a4.8 4.8 0 1 0 0-9.6 4.8 4.8 0 0 0 0 9.6Z" stroke="currentColor" strokeWidth="1.8" />
      <path d="M12 13.8v6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M9.5 17.2h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconGlobe({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z" stroke="currentColor" strokeWidth="1.8" />
      <path d="M3.5 12h17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M12 3c2.6 2.6 4.1 6.1 4.1 9s-1.5 6.4-4.1 9c-2.6-2.6-4.1-6.1-4.1-9S9.4 5.6 12 3Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
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

function IconChart({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M4 19h17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M7 19V11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M12 19V7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M17 19v-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

const API_BASE = 'http://localhost:8000';

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: '',
    age: '',
    gender: '',
    country: '',
    email: '',
    password: '',
    insomnia_duration_years: '',
    notifications_enabled: true,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        ...formData,
        age: parseInt(formData.age, 10),
        insomnia_duration_years: formData.insomnia_duration_years
          ? parseInt(formData.insomnia_duration_years, 10)
          : 0,
      };

      const res = await fetch(`${API_BASE}/accounts/api/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        navigate('/dashboard');
      } else {
        // Format Django REST Framework error messages
        const messages = Object.entries(data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('\n');
        setError(messages);
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

      <SpotlightCard className="custom-spotlight-card" spotlightColor="rgba(0, 229, 255, 0.2)">
        {/* Header */}
        <div className="accounts-header">
          <div className="accounts-logo-icon">
            <MoonIcon className="accounts-mark" />
          </div>
          <div className="accounts-eyebrow">Sleep &amp; Wellness</div>
          <h1>Create Your Account</h1>
          <p>Start your journey toward better sleep tonight</p>
        </div>

        {error && <div className="accounts-error">{error}</div>}

        <form onSubmit={handleSubmit} className="accounts-form">

          {/* Row: Full name + Age */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="full_name"><IconUser className="field-icon field-icon--rose" /> Full Name</label>
              <input
                id="full_name"
                type="text"
                name="full_name"
                required
                value={formData.full_name}
                onChange={handleChange}
                placeholder="John Doe"
              />
            </div>
            <div className="form-group">
              <label htmlFor="age"><IconCalendar className="field-icon field-icon--lavender" /> Age</label>
              <input
                id="age"
                type="number"
                name="age"
                required
                min="1"
                max="120"
                value={formData.age}
                onChange={handleChange}
                placeholder="25"
              />
            </div>
          </div>

          {/* Row: Gender + Country */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="gender"><IconGender className="field-icon field-icon--mint" /> Gender</label>
              <select
                id="gender"
                name="gender"
                required
                value={formData.gender}
                onChange={handleChange}
              >
                <option value="">Select gender</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="X">Prefer not to say</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="country"><IconGlobe className="field-icon field-icon--aqua" /> Country</label>
              <input
                id="country"
                type="text"
                name="country"
                required
                value={formData.country}
                onChange={handleChange}
                placeholder="Algeria"
              />
            </div>
          </div>

          {/* Email */}
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

          {/* Password */}
          <div className="form-group">
            <label htmlFor="password"><IconLock className="field-icon field-icon--lavender" /> Password</label>
            <input
              id="password"
              type="password"
              name="password"
              required
              minLength="8"
              value={formData.password}
              onChange={handleChange}
              placeholder="Minimum 8 characters"
            />
          </div>

          {/* Insomnia duration */}
          <div className="form-group">
            <label htmlFor="insomnia_duration_years">
              <IconChart className="field-icon field-icon--rose" />
              Insomnia Duration (years)
            </label>
            <input
              id="insomnia_duration_years"
              type="number"
              name="insomnia_duration_years"
              min="0"
              max="100"
              value={formData.insomnia_duration_years}
              onChange={handleChange}
              placeholder="0"
            />
          </div>

          {/* Notifications toggle */}
          <label className="toggle-field">
            <span className="toggle-label">Enable notifications</span>
            <span className="toggle-switch">
              <input
                type="checkbox"
                id="notifications_enabled"
                name="notifications_enabled"
                checked={formData.notifications_enabled}
                onChange={handleChange}
              />
              <span className="toggle-slider" aria-hidden="true" />
            </span>
          </label>

          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create Account →'}
          </button>
        </form>

        <p className="accounts-footer-text">
          Already have an account?{' '}
          <Link to="/login">Sign in</Link>
        </p>
      </SpotlightCard>
    </div>
  );
}
