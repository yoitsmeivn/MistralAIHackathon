import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

export const supabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

if (!supabaseConfigured) {
  console.warn(
    "[Canard] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set — auth features disabled. " +
    "Create apps/web/.env with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY."
  );
}

// Create a real client when configured, or a dummy placeholder so imports don't crash
export const supabase: SupabaseClient = supabaseConfigured
  ? createClient(supabaseUrl!, supabaseAnonKey!)
  : (null as unknown as SupabaseClient);
