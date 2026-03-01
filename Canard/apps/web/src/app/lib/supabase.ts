import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

export const supabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

if (!supabaseConfigured) {
  console.warn(
    "[Canard] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set — auth features disabled. " +
    "Create apps/web/.env with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY."
  );
}

const dummySupabase = new Proxy({}, {
  get(_target, prop) {
    if (prop === "auth") {
      return new Proxy({}, {
        get(_authTarget, authProp) {
          return () => {
            if (authProp === "getSession") return Promise.resolve({ data: { session: null }, error: null });
            if (authProp === "onAuthStateChange") return { data: { subscription: { unsubscribe: () => {} } } };
            throw new Error("Cannot connect to Supabase: Configuration missing in apps/web/.env");
          };
        }
      });
    }
    return () => {
      throw new Error("Cannot connect to Supabase: Configuration missing.");
    };
  }
}) as unknown as SupabaseClient;

// Create a real client when configured, or a dummy proxy so imports/clicks don't hard crash
export const supabase: SupabaseClient = supabaseConfigured
  ? createClient(supabaseUrl!, supabaseAnonKey!)
  : dummySupabase;
