/**
 * App.js — Root component and session manager for the Unitwise frontend.
 *
 * Listens for Supabase auth state changes and conditionally renders
 * either the Login page or the ChatDashboard.
 */

import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { supabase } from './config/supabaseClient';
import Login from './pages/Login';
import ChatDashboard from './pages/ChatDashboard';
import LandingPage from './pages/landingpage';
import CustomCursor from './components/CustomCursor';

function App() {
  // ---- Session state (null = not authenticated) ----
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Fetch the current session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    // 2. Subscribe to future auth changes (login, sign-out, token refresh)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setLoading(false);
    });

    // 3. Cleanup the listener when the component unmounts
    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    return null;
  }

  // ---- Conditional rendering based on auth state ----
  return (
    <Router>
      <div className="App">

        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={!session ? <Login /> : <Navigate to="/chat" />} />
          <Route path="/chat" element={session ? <ChatDashboard session={session} /> : <Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
