import { useState, useEffect } from "react";
import { Link } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import CanardLogo from "../../../CanardTransparent.png";
import CanardSecurity from "../../../CanardSecurityTransparent.png";
import {
  Shield,
  Mic,
  Brain,
  Target,
  ArrowRight,
  ArrowUp,
  Menu,
  X,
  ClipboardList,
  Rocket,
  BarChart3,
  Search,
  Zap,
  Users,
  FileCheck,
  Headphones,
  UserCog,
  CalendarClock,
  LayoutDashboard,
  MessageSquareText,
  ShieldCheck,
  BookOpen,
} from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */

const coreValueGains = [
  {
    icon: Search,
    title: "Early Vulnerability Detection",
    description:
      "Identify employees most likely to disclose sensitive information under pressure \u2014 before a real attacker does.",
  },
  {
    icon: MessageSquareText,
    title: "Targeted, Just-in-Time Coaching",
    description:
      "Deliver feedback in the moment of failure, turning a high-risk employee into a resilient human firewall.",
  },
  {
    icon: BarChart3,
    title: "Data-Driven Security Posture",
    description:
      "Stop guessing about social engineering risk. Get quantifiable metrics across every department to prove training ROI to the board or compliance auditors.",
  },
];

const dashboardGains = [
  {
    icon: ShieldCheck,
    title: "Proactive Security Posture",
    description:
      "Instead of reacting to breaches, you are actively hunting for vulnerabilities in human behavior.",
  },
  {
    icon: Zap,
    title: "Scale Without Overhead",
    description:
      "Running manual red-team voice calls is expensive and slow. Canard allows you to test 1,000 employees simultaneously using AI, requiring zero human callers.",
  },
  {
    icon: Target,
    title: "Deep Analytics & Blind Spot Mapping",
    description:
      'Discover that while your Engineering team resists attacks perfectly, your Finance team fails 40% of "urgent wire transfer" scenarios. Then, focus your budget and training on Finance.',
  },
  {
    icon: FileCheck,
    title: "Frictionless Compliance",
    description:
      "Generate audit-ready reports instantly, proving that your organization regularly tests and trains against social engineering to meet compliance frameworks (SOC 2, ISO 27001).",
  },
];

const platformFeatures = [
  {
    icon: Headphones,
    title: "AI Voice Simulations",
    subtitle: "Zero Human Effort",
    description:
      "Advanced LLMs and voice synthesis hold dynamic, eerily realistic conversations. The AI adapts in real-time \u2014if the employee resists, it can escalate urgency or pivot tactics.",
  },
  {
    icon: UserCog,
    title: "Customizable Personas & Scripts",
    subtitle: "Tailored Attack Playbooks",
    description:
      'Pre-built and custom attack playbooks: "IT Helpdesk Reset," "Urgent CEO Wire Transfer," "Vendor Invoice Update." Build a persona with a specific voice, accent, and mood.',
  },
  {
    icon: CalendarClock,
    title: "Campaign Builder & Orchestration",
    subtitle: "Launch at Scale",
    description:
      "Launch batch simulations across specific departments or the entire company with just a few clicks. Schedule campaigns incrementally so everyone isn't called on the same day.",
  },
  {
    icon: BarChart3,
    title: "Real-Time Call Analytics",
    subtitle: "Risk Scoring",
    description:
      "Every call is automatically transcribed and analyzed by AI. Employees receive a risk score (0\u2013100) with extracted flags like credential_disclosed or yielded_to_urgency.",
  },
  {
    icon: BookOpen,
    title: "Actionable Coaching Notes",
    subtitle: "Not Punishment",
    description:
      'Rather than just a "fail" grade, Canard generates actionable coaching summaries to help the employee understand exactly how they were manipulated and how to handle it next time.',
  },
  {
    icon: LayoutDashboard,
    title: "Executive Dashboard & Heatmaps",
    subtitle: "Visualize Risk",
    description:
      "Visualize risk across the organization. View time-of-day heatmaps showing when employees are most vulnerable and track repeat offenders to identify systemic risks.",
  },
];

const steps = [
  {
    icon: ClipboardList,
    title: "Design",
    description:
      "Configure custom vishing scenarios tailored to your team's vulnerabilities.",
  },
  {
    icon: Rocket,
    title: "Launch",
    description:
      "Deploy AI-driven voice simulations to test employee responses in real time.",
  },
  {
    icon: BarChart3,
    title: "Analyze",
    description:
      "Review detailed reports and resilience scores to strengthen your defenses.",
  },
];

const capabilityGroups = [
  {
    title: "Campaign Generation & Execution",
    icon: Rocket,
    capabilities: [
      "Build reusable attacker personas \u2014like an angry vendor or urgent IT caller \u2014for consistent, repeatable baseline tests across departments.",
      'Launch targeted phishing campaigns with pre-built scripts such as "Wire Transfer Fraud" or "Helpdesk Reset" to measure specific vulnerabilities.',
      "Fully automated AI-driven calls that hold realistic, human-like conversations \u2014no red-team actors or manual dialing required.",
    ],
  },
  {
    title: "Analytics & Vulnerability Detection",
    icon: BarChart3,
    capabilities: [
      "Company-wide aggregate risk scoring to track your human-risk posture quarter-over-quarter at a glance.",
      "Granular flag breakdowns (e.g., credential disclosed, no identity verification, yielded to urgency) across every campaign for targeted training.",
      "Repeat offender identification to surface employees who consistently fail, enabling focused 1-on-1 coaching interventions.",
      "Time-of-day heatmaps showing when employees are most susceptible \u2014so you can proactively warn staff during high-risk windows.",
    ],
  },
  {
    title: "Employee Coaching",
    icon: BookOpen,
    capabilities: [
      "AI-generated call summaries that distill a 5-minute failed call into a concise, actionable breakdown \u2014no need to listen to full recordings.",
      'Constructive, non-punitive coaching notes that teach employees to recognize manipulation tactics rather than simply flagging a failure.',
    ],
  },
  {
    title: "Administration & Setup",
    icon: Users,
    capabilities: [
      "One-click export of campaign results and test histories for audit-ready compliance reporting (SOC 2, ISO 27001).",
      "Department and manager-based employee organization so risk metrics are accurately attributed to the right business units.",
    ],
  },
];

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "Platform", href: "#platform" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Capabilities", href: "#capabilities" },
  { label: "Contact", href: "#contact" },
];

/* ------------------------------------------------------------------ */
/*  Animation variants                                                 */
/* ------------------------------------------------------------------ */

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0, 0, 0.2, 1] as const },
  },
};

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
/*  Section heading helper                                             */
/* ------------------------------------------------------------------ */

function SectionHeading({
  tag,
  title,
  subtitle,
}: {
  tag?: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <motion.div variants={fadeUp} className="mx-auto mb-14 max-w-2xl text-center">
      {tag && (
        <span className="mb-3 inline-block rounded-full bg-card px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-foreground">
          {tag}
        </span>
      )}
      <h2 className="text-2xl font-bold text-foreground md:text-3xl lg:text-4xl">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-base text-muted-foreground md:text-lg">
          {subtitle}
        </p>
      )}
    </motion.div>
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
    <div className="landing-page relative min-h-screen bg-background">
      {/* Skip-to-content */}
      <a href="#main" className="skip-to-content">
        Skip to content
      </a>

      {/* Dot grid */}
      <div
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          backgroundImage:
            "radial-gradient(circle, hsl(0 0% 75% / 0.35) 1.2px, transparent 1.2px)",
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
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
          aria-label="Back to top"
        >
          <img src={CanardSecurity} alt="Canard Security" className="h-10 md:h-12" />
        </a>

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
          {mobileMenuOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
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

      {/* ============================================================ */}
      {/*  HERO                                                         */}
      {/* ============================================================ */}
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

        <motion.div
          variants={fadeUp}
          className="mt-10 flex flex-wrap justify-center gap-4"
        >
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

      {/* ============================================================ */}
      {/*  CORE VALUE                                                   */}
      {/* ============================================================ */}
      <motion.section
        id="features"
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.1 }}
        className="relative z-10 mx-auto max-w-6xl px-6 pb-28"
      >
        <SectionHeading
          tag="Why Canard Matters"
          title="Your Biggest Risk Isn't a Flawed Firewall"
          subtitle="It's an employee handing over sensitive information over the phone. Traditional training doesn't prepare people for the emotional manipulation of a live call. Canard solves this with safe, realistic, automated voice phishing simulations."
        />

        <div className="grid gap-6 md:grid-cols-3">
          {coreValueGains.map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 40, scale: 0.95 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{
                duration: 0.5,
                delay: i * 0.1,
                ease: [0, 0, 0.2, 1] as const,
              }}
              whileHover={{ y: -6, scale: 1.02 }}
              className="feature-card rounded-xl border border-border bg-card p-8 shadow-lg shadow-foreground/5 hover:shadow-xl"
            >
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-accent shadow-sm">
                <item.icon className="h-6 w-6 text-accent-foreground" />
              </div>
              <h3 className="mb-2 text-lg font-bold text-foreground">
                {item.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {item.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ============================================================ */}
      {/*  DASHBOARD MANAGER GAINS                                      */}
      {/* ============================================================ */}
      <motion.section
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.1 }}
        className="relative z-10 mx-auto max-w-6xl px-6 pb-28"
      >
        <SectionHeading
          tag="For Security Leaders"
          title="What Your Company Gains"
          subtitle="Actionable intelligence, scale, and compliance \u2014 all from one platform."
        />

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {dashboardGains.map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 40, scale: 0.95 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{
                duration: 0.5,
                delay: i * 0.1,
                ease: [0, 0, 0.2, 1] as const,
              }}
              whileHover={{ y: -6, scale: 1.02 }}
              className="feature-card rounded-xl border border-border bg-card p-6 shadow-lg shadow-foreground/5 hover:shadow-xl"
            >
              <motion.div
                whileHover={{ rotate: [0, -8, 8, 0] }}
                transition={{ duration: 0.5 }}
                className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-accent shadow-sm"
              >
                <item.icon className="h-6 w-6 text-accent-foreground" />
              </motion.div>
              <h3 className="mb-2 text-lg font-bold text-foreground">
                {item.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {item.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ============================================================ */}
      {/*  CORE PLATFORM FEATURES                                       */}
      {/* ============================================================ */}
      <motion.section
        id="platform"
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.05 }}
        className="relative z-10 mx-auto max-w-6xl px-6 pb-28"
      >
        <SectionHeading
          tag="Platform"
          title="Core Platform Features"
          subtitle="Everything you need to simulate, analyze, and coach \u2014powered by AI."
        />

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {platformFeatures.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 40, scale: 0.95 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{
                duration: 0.5,
                delay: i * 0.08,
                ease: [0, 0, 0.2, 1] as const,
              }}
              whileHover={{ y: -6, scale: 1.02 }}
              className="feature-card rounded-xl border border-border bg-card p-7 shadow-lg shadow-foreground/5 hover:shadow-xl"
            >
              <motion.div
                whileHover={{ rotate: [0, -8, 8, 0] }}
                transition={{ duration: 0.5 }}
                className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-accent shadow-sm"
              >
                <f.icon className="h-6 w-6 text-accent-foreground" />
              </motion.div>
              <h3 className="mb-1 text-lg font-bold text-foreground">
                {f.title}
              </h3>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {f.subtitle}
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {f.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ============================================================ */}
      {/*  HOW IT WORKS                                                 */}
      {/* ============================================================ */}
      <motion.section
        id="how-it-works"
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.15 }}
        className="relative z-10 mx-auto max-w-5xl px-6 pb-28"
      >
        <SectionHeading
          tag="Process"
          title="How It Works"
          subtitle="Three simple steps to build a resilient team."
        />

        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{
                duration: 0.5,
                delay: i * 0.15,
                ease: [0, 0, 0.2, 1] as const,
              }}
              className="relative text-center"
            >
              <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
                <step.icon className="h-7 w-7" />
              </div>

              {i < steps.length - 1 && (
                <div className="absolute top-8 left-[calc(50%+40px)] hidden h-px w-[calc(100%-80px)] bg-border md:block" />
              )}

              <h3 className="mb-2 text-lg font-bold text-foreground">
                <span className="mr-1 text-muted-foreground">{i + 1}.</span>{" "}
                {step.title}
              </h3>
              <p className="mx-auto max-w-xs text-sm leading-relaxed text-muted-foreground">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* ============================================================ */}
      {/*  CAPABILITIES                                                 */}
      {/* ============================================================ */}
      <motion.section
        id="capabilities"
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.05 }}
        className="relative z-10 mx-auto max-w-4xl px-6 pb-28"
      >
        <SectionHeading
          tag="Capabilities"
          title="What You Can Do with Canard"
          subtitle="Explore key capabilities organized by workflow. Expand each category to see what the platform delivers."
        />

        <motion.div variants={fadeUp}>
          <Accordion
            type="single"
            collapsible
            defaultValue="group-0"
            className="rounded-xl border border-border bg-card shadow-lg shadow-foreground/5"
          >
            {capabilityGroups.map((group, groupIdx) => (
              <AccordionItem
                key={group.title}
                value={`group-${groupIdx}`}
                className="border-border px-6 last:border-b-0"
              >
                <AccordionTrigger className="gap-3 py-5 text-left text-base font-semibold text-foreground hover:no-underline">
                  <span className="flex items-center gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent">
                      <group.icon className="h-4 w-4 text-accent-foreground" />
                    </span>
                    {group.title}
                  </span>
                </AccordionTrigger>
                <AccordionContent className="pb-5">
                  <ul className="space-y-3">
                    {group.capabilities.map((cap, j) => (
                      <li
                        key={j}
                        className="flex items-start gap-3 rounded-lg bg-background/60 px-4 py-3 text-sm leading-relaxed text-muted-foreground"
                      >
                        <span className="mt-1.5 block h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                        {cap}
                      </li>
                    ))}
                  </ul>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </motion.section>

      {/* ============================================================ */}
      {/*  CTA                                                          */}
      {/* ============================================================ */}
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

      {/* ============================================================ */}
      {/*  FOOTER                                                       */}
      {/* ============================================================ */}
      <motion.footer
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="relative z-10 border-t border-border"
      >
        <div className="mx-auto max-w-6xl px-6 py-14 md:px-12">
          <div className="flex flex-col items-center text-center">
            <img
              src={CanardSecurity}
              alt="Canard Security"
              className="mb-4 h-10"
            />
            <p className="max-w-md text-sm leading-relaxed text-muted-foreground">
              AI-powered voice simulations to build real-world resilience
              against social engineering.
            </p>
          </div>

          <div className="mt-12 border-t border-border pt-6 text-center text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Canard Security. All rights
            reserved.
          </div>
        </div>
      </motion.footer>

      {/* Scroll-to-top */}
      <ScrollToTop />
    </div>
  );
}
