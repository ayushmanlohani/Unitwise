/**
 * Login.js — Authentication page for the Unitwise app.
 *
 * Provides both Sign Up and Log In flows via Supabase Auth.
 * Uses Supabase v2 methods (signUp, signInWithPassword).
 */

import { useState } from 'react';
import { supabase } from '../config/supabaseClient';

// ---------------------------------------------------------------------------
// Styles — modern, dark-themed auth card (no Tailwind, pure inline CSS)
// ---------------------------------------------------------------------------

const styles = {
  /* ---------- Full-page wrapper ---------- */
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
    fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
    padding: '1rem',
  },

  /* ---------- Card container ---------- */
  card: {
    width: '100%',
    maxWidth: '420px',
    background: 'rgba(255, 255, 255, 0.06)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '20px',
    padding: '2.5rem 2rem',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
    color: '#f0f0f0',
  },

  /* ---------- Title / subtitle ---------- */
  title: {
    margin: '0 0 0.25rem',
    fontSize: '1.75rem',
    fontWeight: 700,
    textAlign: 'center',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    margin: '0 0 2rem',
    fontSize: '0.9rem',
    textAlign: 'center',
    color: 'rgba(255, 255, 255, 0.55)',
  },

  /* ---------- Form inputs ---------- */
  label: {
    display: 'block',
    marginBottom: '0.4rem',
    fontSize: '0.85rem',
    fontWeight: 500,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  input: {
    width: '100%',
    padding: '0.75rem 1rem',
    marginBottom: '1.25rem',
    fontSize: '0.95rem',
    color: '#fff',
    background: 'rgba(255, 255, 255, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '10px',
    outline: 'none',
    transition: 'border-color 0.2s, box-shadow 0.2s',
    boxSizing: 'border-box',
  },

  /* ---------- Buttons ---------- */
  btnPrimary: {
    width: '100%',
    padding: '0.8rem',
    fontSize: '0.95rem',
    fontWeight: 600,
    color: '#fff',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'opacity 0.2s, transform 0.15s',
    marginBottom: '0.75rem',
  },
  btnSecondary: {
    width: '100%',
    padding: '0.8rem',
    fontSize: '0.95rem',
    fontWeight: 600,
    color: '#c4b5fd',
    background: 'transparent',
    border: '1px solid rgba(196, 181, 253, 0.35)',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'background 0.2s, transform 0.15s',
  },

  /* ---------- Feedback messages ---------- */
  error: {
    marginBottom: '1rem',
    padding: '0.65rem 1rem',
    fontSize: '0.85rem',
    color: '#fca5a5',
    background: 'rgba(239, 68, 68, 0.12)',
    border: '1px solid rgba(239, 68, 68, 0.25)',
    borderRadius: '8px',
    textAlign: 'center',
  },
  success: {
    marginBottom: '1rem',
    padding: '0.65rem 1rem',
    fontSize: '0.85rem',
    color: '#86efac',
    background: 'rgba(34, 197, 94, 0.12)',
    border: '1px solid rgba(34, 197, 94, 0.25)',
    borderRadius: '8px',
    textAlign: 'center',
  },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Login() {
  // ---- State ----
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // ---- Sign Up ----
  async function handleSignUp(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    const { error: signUpError } = await supabase.auth.signUp({
      email,
      password,
    });

    if (signUpError) {
      setError(signUpError.message);
    } else {
      setMessage('Account created! You can now log in.');
    }

    setLoading(false);
  }

  // ---- Log In (Supabase v2: signInWithPassword) ----
  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    const { error: loginError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (loginError) {
      setError(loginError.message);
    } else {
      setMessage('Logged in successfully!');
    }

    setLoading(false);
  }

  // ---- Render ----
  return (
    <div style={styles.page}>
      <div style={styles.card}>
        {/* Header */}
        <h1 style={styles.title}>Welcome to Unitwise</h1>
        <p style={styles.subtitle}>Sign in to access your academic assistant</p>

        {/* Feedback banners */}
        {error && <div style={styles.error}>{error}</div>}
        {message && <div style={styles.success}>{message}</div>}

        {/* Auth form */}
        <form onSubmit={handleLogin}>
          <label htmlFor="email" style={styles.label}>
            Email
          </label>
          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={styles.input}
          />

          <label htmlFor="password" style={styles.label}>
            Password
          </label>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            style={styles.input}
          />

          {/* Primary action — Log In */}
          <button
            id="login-btn"
            type="submit"
            disabled={loading}
            style={{
              ...styles.btnPrimary,
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? 'Please wait…' : 'Log In'}
          </button>

          {/* Secondary action — Sign Up */}
          <button
            id="signup-btn"
            type="button"
            disabled={loading}
            onClick={handleSignUp}
            style={{
              ...styles.btnSecondary,
              opacity: loading ? 0.6 : 1,
            }}
          >
            Create Account
          </button>
        </form>
      </div>
    </div>
  );
}
