/**
 * ChatDashboard.js — Main authenticated view for the Unitwise app.
 *
 * Displays a header with user info and sign-out, plus a placeholder
 * content area that will later hold the chat interface.
 *
 * Props:
 *   session — the active Supabase auth session object.
 */

import { supabase } from '../config/supabaseClient';

// ---------------------------------------------------------------------------
// Styles — dark academic theme, consistent with the Login page palette
// ---------------------------------------------------------------------------

const styles = {
  /* ---------- Full-page wrapper ---------- */
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(160deg, #0f0c29 0%, #1a1a2e 40%, #16213e 100%)',
    fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
    color: '#f0f0f0',
    display: 'flex',
    flexDirection: 'column',
  },

  /* ---------- Top header bar ---------- */
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1rem 2rem',
    background: 'rgba(255, 255, 255, 0.04)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
  },
  headerTitle: {
    margin: 0,
    fontSize: '1.25rem',
    fontWeight: 700,
    letterSpacing: '-0.01em',
    background: 'linear-gradient(135deg, #667eea, #a78bfa)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  email: {
    fontSize: '0.85rem',
    color: 'rgba(255, 255, 255, 0.55)',
  },
  signOutBtn: {
    padding: '0.5rem 1.1rem',
    fontSize: '0.8rem',
    fontWeight: 600,
    color: '#fca5a5',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.25)',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background 0.2s, transform 0.15s',
  },

  /* ---------- Main content area ---------- */
  main: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
  },
  placeholder: {
    textAlign: 'center',
    maxWidth: '480px',
  },
  placeholderIcon: {
    fontSize: '3rem',
    marginBottom: '1rem',
    opacity: 0.6,
  },
  placeholderHeading: {
    margin: '0 0 0.5rem',
    fontSize: '1.5rem',
    fontWeight: 600,
    color: 'rgba(255, 255, 255, 0.85)',
  },
  placeholderText: {
    margin: 0,
    fontSize: '0.95rem',
    color: 'rgba(255, 255, 255, 0.4)',
    lineHeight: 1.6,
  },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ChatDashboard({ session }) {
  /**
   * Sign the user out — clears the Supabase session which will
   * trigger the onAuthStateChange listener in App.js, flipping
   * the view back to the Login page.
   */
  async function handleSignOut() {
    await supabase.auth.signOut();
  }

  return (
    <div style={styles.page}>
      {/* ---- Header ---- */}
      <header style={styles.header}>
        <h1 style={styles.headerTitle}>Unitwise Dashboard</h1>

        <div style={styles.headerRight}>
          <span style={styles.email}>{session.user.email}</span>
          <button
            id="signout-btn"
            onClick={handleSignOut}
            style={styles.signOutBtn}
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* ---- Main content (placeholder for now) ---- */}
      <main style={styles.main}>
        <div style={styles.placeholder}>
          <div style={styles.placeholderIcon}>💬</div>
          <h2 style={styles.placeholderHeading}>Chat interface coming soon…</h2>
          <p style={styles.placeholderText}>
            This is where you'll ask questions about your AKTU syllabus
            and get AI-powered answers grounded in your course material.
          </p>
        </div>
      </main>
    </div>
  );
}
