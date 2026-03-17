import { createClient } from "@supabase/supabase-js";

/*
  Replace these with values from:
  Supabase Dashboard → Settings → API
*/

const supabaseUrl = "https://qvdzlwzjodciqsvizbgf.supabase.co";
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2ZHpsd3pqb2RjaXFzdml6YmdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxMTYyNzAsImV4cCI6MjA4ODY5MjI3MH0.2mqj_-ZL0A2PiuR-sOkvL2a347iFibkRqMZi-ABAqRo";

/*
  Create Supabase client
  This will be used across the entire React application
*/

export const supabase = createClient(
  supabaseUrl,
  supabaseAnonKey
);

/*
  Optional helper functions for authentication
*/

// Sign Up
export const signUpUser = async (email, password) => {
  const { data, error } = await supabase.auth.signUp({
    email: email,
    password: password,
  });

  return { data, error };
};

// Sign In
export const signInUser = async (email, password) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email: email,
    password: password,
  });

  return { data, error };
};

// Sign Out
export const signOutUser = async () => {
  const { error } = await supabase.auth.signOut();
  return { error };
};

// Get Current Logged In User
export const getCurrentUser = async () => {
  const { data, error } = await supabase.auth.getUser();
  return { data, error };
};