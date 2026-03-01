import { useState, useEffect, useRef } from "react";
import { Link } from "react-router";
import { motion, useInView, useMotionValue, useTransform, animate, AnimatePresence } from "motion/react";
import CanardLogo from "../../../CanardTransparent.png";
import CanardSecurity from "../../../CanardSecurityTransparent.png";
import {
  Shield, Mic, Brain, Target, ArrowRight, ArrowUp,
  Menu, X, ClipboardList, Rocket, BarChart3,
  Twitter, Linkedin, Github,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */

const features = [
  {
    icon: Mic,
    title: "Voice Simulations",
    description: "AI-generated vishing calls that mimic real-world attack scenarios.",
  },
  {
    icon: Brain,
    title: "AI-Powered Analysis",
    description: "Intelligent scoring and detailed reports on employee responses.",
  },
  {
    icon: Target,
    title: "Targeted Campaigns",
    description: "Custom attack simulations tailored to your organization's risk profile.",
  },
  {
    icon: Shield,
    title: "Real-Time Dashboards",
    description: "Monitor your team's resilience with live threat readiness metrics.",
  },
];

const steps = [
  {
    icon: ClipboardList,
    title: "Design",
    description: "Configure custom vishing scenarios tailored to your team's vulnerabilities.",
  },
  {
    icon: Rocket,
    title: "Launch",
    description: "Deploy AI-driven voice simulations to test employee responses in real time.",
  },
  {
    icon: BarChart3,
    title: "Analyze",
    description: "Review detailed reports and resilience scores to strengthen your defenses.",
  },
];

const stats = [
  { value: 10000, suffix: "+", label: "Simulations Run" },
  { value: 98, suffix: "%", label: "Detection Accuracy" },
  { value: 500, suffix: "+", label: "Teams Protected" },
  { value: 4.9, suffix: "/5", label: "Customer Rating", decimals: 1 },
];

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Contact", href: "#contact" },
];

const footerLinks = {
  Product: ["Features", "Pricing", "Integrations", "Changelog"],
  Company: ["About", "Blog", "Careers", "Press"],
  Resources: ["Documentation", "Help Center", "Security", "Status"],
};

/* ------------------------------------------------------------------ */
/*  Animation variants                                                 */
/* ------------------------------------------------------------------ */

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0, 0, 0.2, 1] as const } },
};

/* ------------------------------------------------------------------ */
/*  AnimatedCounter                                                    */
/* ------------------------------------------------------------------ */

function AnimatedCounter({ value, suffix = "", decimals = 0 }: { value: number; suffix?: string; decimals?: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });
  const motionVal = useMotionValue(0);
  const display = useTransform(motionVal, (v) => `${v.toFixed(decimals)}${suffix}`);

  useEffect(() => {
    if (isInView) {
      animate(motionVal, value, { duration: 2, ease: "easeOut" });
    }
  }, [isInView, motionVal, value]);

  return <motion.span ref={ref}>{display}</motion.span>;
}

/* ------------------------------------------------------------------ */
/*  ScrollToTop                                                        */
/* ------------------------------------------------------------------ */

function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 400);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <AnimatePresence>
      {visible && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          aria-label="Scroll to top"
          className="fixed bottom-6 right-6 z-50 flex h-11 w-11 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/25 transition-colors hover:opacity-90"
        >
          <ArrowUp className="h-5 w-5" />
        </motion.button>
      )}
    </AnimatePresence>
  );
}

/* ------------------------------------------------------------------ */
/*  LandingPage                                                        */
/* ------------------------------------------------------------------ */

export function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="relative min-h-screen bg-background overflow-hidden">
      {/* Skip-to-content */}
      <a href="#main" className="skip-to-content">
        Skip to content
      </a>

      {/* Dot grid */}
      <div
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          backgroundImage:
            "radial-gradient(circle, hsl(0 0% 75% / 0.45) 1.2px, transparent 1.2px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* ---- Nav ---- */}
      <motion.nav
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className={`sticky top-0 z-40 flex items-center justify-between px-6 py-4 md:px-12 transition-all duration-300 ${
          scrolled
            ? "bg-background/80 backdrop-blur-lg shadow-sm border-b border-border/50"
            : "bg-transparent"
        }`}
      >
        <img src={CanardSecurity} alt="Canard Security" className="h-10 md:h-12" />

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
          <Link
            to="/login"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            Log In
          </Link>
          <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}>
            <Link
              to="/signup"
              className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition-colors hover:opacity-90"
            >
              Get Started
            </Link>
          </motion.div>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden flex h-10 w-10 items-center justify-center rounded-lg text-foreground transition-colors hover:bg-accent"
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
        >
          {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </motion.nav>

      {/* Mobile menu overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: [0, 0, 0.2, 1] }}
            className="sticky top-[72px] z-30 overflow-hidden border-b border-border bg-background/95 backdrop-blur-lg md:hidden"
          >
            <div className="flex flex-col gap-1 px-6 py-4">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-lg px-4 py-3 text-sm font-medium text-foreground transition-colors hover:bg-accent"
                >
                  {link.label}
                </a>
              ))}
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="rounded-lg px-4 py-3 text-sm font-medium text-foreground transition-colors hover:bg-accent"
              >
                Log In
              </Link>
              <Link
                to="/signup"
                onClick={() => setMobileMenuOpen(false)}
                className="mt-2 rounded-lg bg-primary px-4 py-3 text-center text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20"
              >
                Get Started
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ---- Hero ---- */}
      <motion.section
        id="main"
        variants={container}
        initial="hidden"
        animate="show"
        className="relative z-10 mx-auto max-w-5xl px-6 pt-16 pb-24 text-center md:pt-28"
      >
        <motion.div variants={fadeUp} className="mb-8 flex justify-center">
          <img
            src={CanardLogo}
            alt="Canard"
            className="h-28 w-28 drop-shadow-xl md:h-36 md:w-36"
          />
        </motion.div>

        <motion.h1
          variants={fadeUp}
          className="hero-gradient-text mx-auto max-w-3xl text-4xl font-extrabold leading-tight tracking-tight md:text-6xl"
        >
          Test your team before attackers do.
        </motion.h1>

        <motion.p
          variants={fadeUp}
          className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground md:text-xl"
        >
          AI-powered voice simulations. Real-world resilience.
        </motion.p>

        <motion.div variants={fadeUp} className="mt-10 flex flex-wrap justify-center gap-4">
          <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}>
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-7 py-3 text-base font-semibold text-primary-foreground shadow-lg shadow-primary/20"
            >
              Get Started <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>
          <motion.a
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.97 }}
            href="#features"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-7 py-3 text-base font-semibold text-foreground shadow-md"
          >
            Learn More
          </motion.a>
        </motion.div>
      </motion.section>

      {/* ---- Features ---- */}
      <motion.section
        id="features"
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.15 }}
        className="relative z-10 mx-auto max-w-6xl px-6 pb-28"
      >
        <motion.h2
          variants={fadeUp}
          className="mb-14 text-center text-2xl font-bold text-foreground md:text-3xl"
        >
          Why Canard?
        </motion.h2>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 40, scale: 0.95 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.5, delay: i * 0.1, ease: [0, 0, 0.2, 1] as const }}
              whileHover={{ y: -6, scale: 1.02 }}
              className="feature-card rounded-xl border border-border bg-card p-6 shadow-lg shadow-foreground/5 hover:shadow-xl"
            >
              <motion.div
                whileHover={{ rotate: [0, -8, 8, 0] }}
                transition={{ duration: 0.5 }}
                className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-accent shadow-sm"
              >
                <f.icon className="h-6 w-6 text-accent-foreground" />
              </motion.div>
              <h3 className="mb-2 text-lg font-bold text-foreground">{f.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{f.description}</p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ---- How It Works ---- */}
      <motion.section
        id="how-it-works"
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.15 }}
        className="relative z-10 mx-auto max-w-5xl px-6 pb-28"
      >
        <motion.h2
          variants={fadeUp}
          className="mb-4 text-center text-2xl font-bold text-foreground md:text-3xl"
        >
          How It Works
        </motion.h2>
        <motion.p
          variants={fadeUp}
          className="mx-auto mb-14 max-w-lg text-center text-muted-foreground"
        >
          Three simple steps to build a resilient team.
        </motion.p>

        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.5, delay: i * 0.15, ease: [0, 0, 0.2, 1] as const }}
              className="relative text-center"
            >
              {/* Step number */}
              <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
                <step.icon className="h-7 w-7" />
              </div>

              {/* Connector line (between steps on desktop) */}
              {i < steps.length - 1 && (
                <div className="absolute top-8 left-[calc(50%+40px)] hidden h-px w-[calc(100%-80px)] bg-border md:block" />
              )}

              <h3 className="mb-2 text-lg font-bold text-foreground">
                <span className="mr-1 text-muted-foreground">{i + 1}.</span> {step.title}
              </h3>
              <p className="mx-auto max-w-xs text-sm leading-relaxed text-muted-foreground">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ---- Stats / Social Proof ---- */}
      <motion.section
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.6, ease: [0, 0, 0.2, 1] as const }}
        className="relative z-10 mx-auto max-w-5xl px-6 pb-28"
      >
        <div className="rounded-2xl border border-border bg-card p-10 shadow-lg shadow-foreground/5 md:p-14">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl font-extrabold text-foreground md:text-4xl">
                  <AnimatedCounter value={stat.value} suffix={stat.suffix} decimals={stat.decimals ?? 0} />
                </p>
                <p className="mt-1 text-sm font-medium text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* ---- CTA ---- */}
      <motion.section
        id="contact"
        initial={{ opacity: 0, y: 50, scale: 0.97 }}
        whileInView={{ opacity: 1, y: 0, scale: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.65, ease: [0, 0, 0.2, 1] as const }}
        className="relative z-10 mx-auto max-w-3xl px-6 pb-32"
      >
        <div className="rounded-2xl border border-border bg-card p-10 text-center shadow-xl shadow-foreground/5 md:p-14">
          <h2 className="text-2xl font-bold text-foreground md:text-3xl">
            Ready to strengthen your defenses?
          </h2>
          <p className="mx-auto mt-4 max-w-md text-muted-foreground">
            Join forward-thinking security teams using Canard to train employees
            against social engineering attacks.
          </p>
          <motion.a
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.97 }}
            href="mailto:hello@canardsecurity.com"
            className="mt-8 inline-flex items-center gap-2 rounded-lg bg-primary px-8 py-3 text-base font-semibold text-primary-foreground shadow-lg shadow-primary/20"
          >
            Contact Us <ArrowRight className="h-4 w-4" />
          </motion.a>
        </div>
      </motion.section>

      {/* ---- Footer ---- */}
      <motion.footer
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="relative z-10 border-t border-border"
      >
        <div className="mx-auto max-w-6xl px-6 py-14 md:px-12">
          <div className="grid gap-10 md:grid-cols-4">
            {/* Brand column */}
            <div>
              <img src={CanardSecurity} alt="Canard Security" className="mb-4 h-10" />
              <p className="text-sm leading-relaxed text-muted-foreground">
                AI-powered voice simulations to build real-world resilience against social engineering.
              </p>
              <div className="mt-5 flex gap-3">
                {[Twitter, Linkedin, Github].map((Icon, i) => (
                  <a
                    key={i}
                    href="#"
                    aria-label={Icon.displayName ?? "social"}
                    className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                  >
                    <Icon className="h-4 w-4" />
                  </a>
                ))}
              </div>
            </div>

            {/* Link columns */}
            {Object.entries(footerLinks).map(([heading, links]) => (
              <div key={heading}>
                <h4 className="mb-3 text-sm font-semibold text-foreground">{heading}</h4>
                <ul className="space-y-2">
                  {links.map((link) => (
                    <li key={link}>
                      <a
                        href="#"
                        className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                      >
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-12 border-t border-border pt-6 text-center text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Canard Security. All rights reserved.
          </div>
        </div>
      </motion.footer>

      {/* Scroll-to-top */}
      <ScrollToTop />
    </div>
  );
}
