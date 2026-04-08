/**
 * App.js — Root component and session manager for the Unitwise frontend.
 *
 * Listens for Supabase auth state changes and conditionally renders
 * either the Login page or the ChatDashboard.
 */

import { useState, useEffect } from 'react';
import { supabase } from './config/supabaseClient';
import Login from './pages/Login';
import ChatDashboard from './pages/ChatDashboard';

function App() {
  // ---- Session state (null = not authenticated) ----
  const [session, setSession] = useState(null);

  useEffect(() => {
    // 1. Fetch the current session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    // 2. Subscribe to future auth changes (login, sign-out, token refresh)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    // 3. Cleanup the listener when the component unmounts
    return () => subscription.unsubscribe();
  }, []);

  // ---- Conditional rendering based on auth state ----
  return (
    <div className="App">
      {!session ? (
        <Login />
      ) : (
        <ChatDashboard session={session} />
      )}
    </div>
  );
}

export default App;
