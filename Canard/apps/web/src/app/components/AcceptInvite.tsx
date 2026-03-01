import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { supabase } from "../lib/supabase";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

export function AcceptInvite() {
  const navigate = useNavigate();
  const [ready, setReady] = useState(false);
  const [expired, setExpired] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Supabase JS client automatically picks up the token fragment from the
    // invite redirect URL and exchanges it for a session.
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event) => {
        if (event === "SIGNED_IN" || event === "PASSWORD_RECOVERY") {
          setReady(true);
        }
      }
    );

    // If no session is established within a few seconds, the link is invalid
    const timeout = setTimeout(async () => {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        setExpired(true);
      }
    }, 4000);

    return () => {
      subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setSubmitting(true);
    try {
      const { error: updateError } = await supabase.auth.updateUser({
        password,
      });
      if (updateError) throw updateError;
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to set password");
    } finally {
      setSubmitting(false);
    }
  }

  if (expired) {
    return (
      <div className="min-h-svh flex items-center justify-center bg-gray-50 px-4">
        <div className="bg-white rounded-2xl shadow-sm border p-8 w-full max-w-md text-center">
          <h1 className="text-xl font-semibold mb-2">Invalid or Expired Link</h1>
          <p className="text-sm text-muted-foreground mb-6">
            This invite link is no longer valid. Please ask your admin to send a new invite.
          </p>
          <Button
            onClick={() => navigate("/login")}
            className="bg-[#252a39] text-white hover:bg-[#252a39]/90"
          >
            Go to Login
          </Button>
        </div>
      </div>
    );
  }

  if (!ready) {
    return (
      <div className="min-h-svh flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#252a39]" />
      </div>
    );
  }

  return (
    <div className="min-h-svh flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white rounded-2xl shadow-sm border p-8 w-full max-w-md">
        <h1 className="text-xl font-semibold mb-1">Set Your Password</h1>
        <p className="text-sm text-muted-foreground mb-6">
          Choose a password to finish setting up your account.
        </p>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Minimum 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm-password">Confirm Password</Label>
            <Input
              id="confirm-password"
              type="password"
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          <Button
            type="submit"
            disabled={submitting}
            className="w-full bg-[#252a39] text-white hover:bg-[#252a39]/90"
          >
            {submitting ? "Setting Password..." : "Set Password"}
          </Button>
        </form>
      </div>
    </div>
  );
}
