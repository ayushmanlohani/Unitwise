import { useState } from 'react';
import { supabase } from '../config/supabaseClient';

const styles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f4ed',
    fontFamily: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
    padding: '16px',
    boxSizing: 'border-box',
  },
  card: {
    width: '100%',
    maxWidth: '438px',
    backgroundColor: '#faf9f5',
    border: '1px solid #e8e6dc',
    borderRadius: '18px',
    padding: '32px 34px 26px',
    boxShadow: 'rgba(20, 20, 19, 0.05) 0px 8px 30px',
    boxSizing: 'border-box',
  },
  title: {
    fontFamily: "'Instrument Serif', Georgia, serif",
    fontSize: '34px',
    fontWeight: 500,
    lineHeight: 1.12,
    color: '#141413',
    margin: '0 0 6px 0',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: '14px',
    lineHeight: 1.45,
    color: '#5e5d59',
    textAlign: 'center',
    margin: '0 0 20px 0',
  },
  label: {
    display: 'block',
    fontSize: '13px',
    fontWeight: 500,
    color: '#4d4c48',
    marginBottom: '5px',
  },
  input: {
    width: '100%',
    padding: '10px 14px',
    marginBottom: '14px',
    fontSize: '14px',
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
    color: '#141413',
    backgroundColor: '#ffffff',
    border: '1px solid #e8e6dc',
    borderRadius: '9px',
    outline: 'none',
    boxSizing: 'border-box',
    transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
  },
  btnPrimary: {
    width: '100%',
    backgroundColor: '#141413',
    color: '#faf9f5',
    padding: '11px 16px',
    borderRadius: '9px',
    border: 'none',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
    marginTop: '6px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.08)',
    transition: 'background-color 0.15s ease',
  },
  btnGoogle: {
    width: '100%',
    backgroundColor: '#ffffff',
    color: '#141413',
    padding: '11px 16px',
    borderRadius: '9px',
    border: '1px solid #e8e6dc',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    marginBottom: '0px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.02)',
    transition: 'all 0.15s ease',
  },
  divider: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    margin: '16px 0',
    color: '#87867f',
    fontSize: '11px',
    fontFamily: "'JetBrains Mono', monospace",
    textTransform: 'uppercase',
  },
  dividerLine: {
    flex: 1,
    height: '1px',
    backgroundColor: '#e8e6dc',
  },
  linkBtn: {
    background: 'none',
    border: 'none',
    color: '#5e5d59',
    fontSize: '13px',
    cursor: 'pointer',
    textDecoration: 'underline',
    marginTop: '16px',
    width: '100%',
    textAlign: 'center',
    padding: '4px',
  },
  message: {
    padding: '9px 14px',
    borderRadius: '8px',
    fontSize: '13px',
    marginBottom: '12px',
    textAlign: 'center',
  }
};

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18">
    <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>
    <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/>
    <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707s.102-1.167.282-1.707V4.961H.957C.347 6.175 0 7.55 0 9s.348 2.825.957 4.039l3.007-2.332z"/>
    <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z"/>
  </svg>
);

export default function Login() {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function handleGoogleSignIn() {
    setLoading(true);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin }
    });
    if (error) setError(error.message);
    setLoading(false);
  }

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

        {/* Google Button */}
        <button
          type="button"
          style={styles.btnGoogle}
          onClick={handleGoogleSignIn}
          disabled={loading}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f4ed'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ffffff'}
        >
          <GoogleIcon />
          <span>Continue with Google</span>
        </button>

        {/* Divider */}
        <div style={styles.divider}>
          <div style={styles.dividerLine} />
          <span>or</span>
          <div style={styles.dividerLine} />
        </div>

        {/* Email/Password form */}
        <form onSubmit={handleSubmit}>
          <label style={styles.label}>Email Address</label>
          <input
            type="email"
            style={styles.input}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onFocus={(e) => {
              e.target.style.borderColor = '#c96442';
              e.target.style.boxShadow = '0 0 0 1px #c96442';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#e8e6dc';
              e.target.style.boxShadow = 'none';
            }}
            required
          />
          <label style={styles.label}>Password</label>
          <input
            type="password"
            style={styles.input}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onFocus={(e) => {
              e.target.style.borderColor = '#c96442';
              e.target.style.boxShadow = '0 0 0 1px #c96442';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#e8e6dc';
              e.target.style.boxShadow = 'none';
            }}
            required
          />
          <button
            type="submit"
            style={{ ...styles.btnPrimary, opacity: loading ? 0.7 : 1 }}
            disabled={loading}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.backgroundColor = '#2a2926'; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.backgroundColor = '#141413'; }}
          >
            {loading ? 'Please wait...' : (isLoginMode ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <button
          type="button"
          style={styles.linkBtn}
          onClick={() => { setIsLoginMode(!isLoginMode); setError(''); setMessage(''); }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#141413'}
          onMouseLeave={(e) => e.currentTarget.style.color = '#5e5d59'}
        >
          {isLoginMode ? "Need an account? Sign up" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
