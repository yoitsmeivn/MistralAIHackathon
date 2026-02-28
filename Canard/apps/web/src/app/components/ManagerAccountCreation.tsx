import { useState } from "react";
import { Link } from "react-router";
import { Eye, EyeOff, UserPlus, ArrowLeft, ShieldCheck } from "lucide-react";
import { motion } from "motion/react";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import logoImg from "../../../CanardSecurityTransparent.png";

export function ManagerAccountCreation() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <div className="min-h-svh flex items-center justify-center bg-gradient-to-br from-[#f4f4f4] via-[#eaeaea] to-[#e0dfd8] px-4 py-10">
      {/* Decorative background accents */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-[#fdfbe1]/40 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-[#252a39]/5 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Back to login */}
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
        >
          <ArrowLeft className="size-4" />
          Back to sign in
        </Link>

        {/* Card */}
        <div className="rounded-2xl border border-black/5 bg-white/80 backdrop-blur-xl shadow-xl shadow-black/5 p-8">
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <div
              className="h-12 w-48 bg-[#252a39]"
              style={{
                WebkitMaskImage: `url(${logoImg})`,
                WebkitMaskSize: "contain",
                WebkitMaskRepeat: "no-repeat",
                WebkitMaskPosition: "center",
                maskImage: `url(${logoImg})`,
                maskSize: "contain",
                maskRepeat: "no-repeat",
                maskPosition: "center",
              }}
              aria-label="Canard Security"
              role="img"
            />
          </div>

          <div className="text-center mb-8">
            <h1 className="text-xl font-medium text-foreground">Create Manager Account</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Request dashboard access for your organization
            </p>
          </div>

          {/* Form */}
          <form onSubmit={(e) => e.preventDefault()} className="space-y-5">
            {/* Role badge */}
            <div className="flex items-center gap-2 rounded-lg border border-[#fdfbe1] bg-[#fdfbe1]/30 px-3 py-2">
              <ShieldCheck className="size-4 text-[#252a39]" />
              <span className="text-sm font-medium text-[#252a39]">Dashboard Manager</span>
            </div>

            <div className="space-y-2">
              <Label htmlFor="manager-name">Full Name *</Label>
              <Input
                id="manager-name"
                placeholder="Jane Doe"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="manager-email">Email *</Label>
              <Input
                id="manager-email"
                type="email"
                placeholder="jane@acme.com"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="company-code">Company Code *</Label>
              <Input
                id="company-code"
                placeholder="e.g. ACME-2026"
                required
              />
              <p className="text-xs text-muted-foreground">
                Enter the unique code provided by your organization to link your account.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="manager-password">Password *</Label>
              <div className="relative">
                <Input
                  id="manager-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="manager-confirm-password">Confirm Password *</Label>
              <div className="relative">
                <Input
                  id="manager-confirm-password"
                  type={showConfirm ? "text" : "password"}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showConfirm ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-[#252a39] text-white hover:bg-[#252a39]/90 h-10"
            >
              <UserPlus className="size-4 mr-2" />
              Request Account
            </Button>
          </form>

          {/* Footer */}
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-foreground font-medium hover:underline underline-offset-4"
            >
              Sign in
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-muted-foreground/50 mt-6">
          Canard Security © 2026
        </p>
      </motion.div>
    </div>
  );
}
