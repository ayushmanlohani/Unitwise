import { useState } from 'react';
import { supabase } from '../config/supabaseClient';

const styles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f4ed', // Parchment
    fontFamily: "system-ui, -apple-system, sans-serif",
    padding: '1rem',
  },
  card: {
    width: '100%',
    maxWidth: '400px',
    backgroundColor: '#faf9f5', // Ivory
    border: '1px solid #f0eee6', // Border Cream
    borderRadius: '16px',
    padding: '48px 40px',
    boxShadow: 'rgba(0,0,0,0.05) 0px 4px 24px', // Whisper shadow
  },
  title: {
    fontFamily: "'Georgia', serif",
    fontSize: '32px',
    fontWeight: 500,
    lineHeight: 1.10,
    color: '#141413',
    margin: '0 0 8px 0',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: '16px',
    lineHeight: 1.60,
    color: '#5e5d59', // Olive Gray
    textAlign: 'center',
    margin: '0 0 32px 0',
  },
  label: {
    display: 'block',
    fontSize: '14px',
    color: '#4d4c48',
    marginBottom: '6px',
  },
  input: {
    width: '100%',
    padding: '12px',
    marginBottom: '20px',
    fontSize: '16px',
    fontFamily: "system-ui, sans-serif",
    color: '#141413',
    backgroundColor: '#ffffff',
    border: '1px solid #e8e6dc', // Border Warm
    borderRadius: '8px',
    outline: 'none',
    boxSizing: 'border-box',
    transition: 'border-color 0.2s',
  },
  btnPrimary: {
    width: '100%',
    backgroundColor: '#141413', // Near Black for primary action here
    color: '#f5f4ed',
    padding: '12px 16px',
    borderRadius: '8px',
    border: 'none',
    fontSize: '16px',
    fontWeight: 500,
    cursor: 'pointer',
    marginTop: '8px',
    boxShadow: '0px 0px 0px 1px #30302e',
  },
  linkBtn: {
    background: 'none',
    border: 'none',
    color: '#3d3d3a', // Dark Warm
    fontSize: '14px',
    cursor: 'pointer',
    textDecoration: 'underline',
    marginTop: '24px',
    width: '100%',
    textAlign: 'center',
  },
  message: {
    padding: '12px',
    borderRadius: '8px',
    fontSize: '14px',
    marginBottom: '20px',
    textAlign: 'center',
  }
};

export default function Login() {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    if (isLoginMode) {
      const { error: loginError } = await supabase.auth.signInWithPassword({ email, password });
      if (loginError) setError(loginError.message);
      else setMessage('Entering your study space...');
    } else {
      const { error: signUpError } = await supabase.auth.signUp({ email, password });
      if (signUpError) setError(signUpError.message);
      else setMessage('Library card created! You can now sign in.');
    }
    setLoading(false);
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>{isLoginMode ? 'Welcome Back' : 'Join Unitwise'}</h1>
        <p style={styles.subtitle}>
          {isLoginMode ? 'Return to your academic materials.' : 'Create an account to begin studying.'}
        </p>

        {error && <div style={{ ...styles.message, backgroundColor: '#fbe9e9', color: '#b53333' }}>{error}</div>}
        {message && <div style={{ ...styles.message, backgroundColor: '#f0eee6', color: '#4d4c48' }}>{message}</div>}

        <form onSubmit={handleSubmit}>
          <label style={styles.label}>Email Address</label>
          <input
            type="email"
            style={styles.input}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onFocus={(e) => e.target.style.borderColor = '#3898ec'}
            onBlur={(e) => e.target.style.borderColor = '#e8e6dc'}
            required
          />

          <label style={styles.label}>Password</label>
          <input
            type="password"
            style={styles.input}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onFocus={(e) => e.target.style.borderColor = '#3898ec'}
            onBlur={(e) => e.target.style.borderColor = '#e8e6dc'}
            required
          />

          <button type="submit" style={{ ...styles.btnPrimary, opacity: loading ? 0.7 : 1 }} disabled={loading}>
            {loading ? 'Please wait...' : (isLoginMode ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <button type="button" style={styles.linkBtn} onClick={() => { setIsLoginMode(!isLoginMode); setError(''); setMessage(''); }}>
          {isLoginMode ? "Need an account? Sign up" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}