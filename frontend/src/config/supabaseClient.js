import { createClient } from '@supabase/supabase-js';

// We grab the URL and Key from the .env file we will create in the frontend
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

// Create and export the secure connection
export const supabase = createClient(supabaseUrl, supabaseAnonKey);