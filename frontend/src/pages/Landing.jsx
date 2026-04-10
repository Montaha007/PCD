import { useEffect, useId, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Galaxy from '../component/Galaxy';
import BorderGlow from '../component/BorderGlow';
import numaLogo from "../assets/numa.png";
import './Landing.css';

function BrandMark({ className = "" }) {
  const maskId = useId();

  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <mask id={maskId}>
          <rect x="0" y="0" width="24" height="24" fill="#DEB64B" />
          <circle cx="14.8" cy="10.2" r="7.2" fill="#000" />
        </mask>
      </defs>
      {/* Crescent */}
      <circle cx="10.8" cy="12.2" r="8.2" fill="currentColor" mask={`url(#${maskId})`} />
      {/* Metallic highlight + shading (neutral overlays; tinted via CSS filter) */}
      <circle cx="9.2" cy="8.6" r="6.4" fill="#DEB64B" opacity="0.22" mask={`url(#${maskId})`} />
      <circle cx="12.0" cy="16.4" r="6.8" fill="#000" opacity="0.10" mask={`url(#${maskId})`} />

      {/* Small stars */}
      <g stroke="currentColor" strokeLinecap="round" strokeWidth="1.4" opacity="0.95">
        <path d="M6.2 6.4v2.2M5.1 7.5h2.2M5.4 6.7l1.6 1.6M7 6.7L5.4 8.3" />
        <path d="M18.1 7.2v1.8M17.2 8.1H19M17.4 7.4l1.4 1.4M18.8 7.4l-1.4 1.4" opacity="0.75" />
        <path d="M18.4 15.8v2M17.4 16.8h2M17.6 16l1.6 1.6M19.2 16l-1.6 1.6" opacity="0.65" />
      </g>
    </svg>
  );
}

function IconMoon({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M14.2 3.3a8.8 8.8 0 1 0 6.5 14.7A9.5 9.5 0 0 1 14.2 3.3Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconSleepLog({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="5" y="4" width="14" height="16" rx="2.2" stroke="currentColor" strokeWidth="1.8" />
      <path d="M9 9h6M9 12h6M9 15h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconAi({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="6" y="6" width="12" height="12" rx="3" stroke="currentColor" strokeWidth="1.8" />
      <path d="M12 9.2v5.6M9.2 12h5.6M4 12h2M18 12h2M12 4v2M12 18v2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconRecommendations({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M12 4.5a5.2 5.2 0 0 0-3.9 8.6c.6.7 1 1.5 1.1 2.4h5.6c.1-.9.5-1.7 1.1-2.4A5.2 5.2 0 0 0 12 4.5Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M10.2 18h3.6M10.7 20h2.6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconProgress({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M5 18V8M10 18V11M15 18V6M20 18V13" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M4 18h17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconHealth({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M12 3.5 5.2 6.6v5.2c0 4 2.5 7.2 6.8 8.7 4.3-1.5 6.8-4.7 6.8-8.7V6.6L12 3.5Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M9 12h6M12 9v6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconPersonalized({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M5 7h10M5 17h14M15 7v10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="15" cy="12" r="2.5" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function IconPattern({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M3.5 12c1.8 0 1.8-4 3.6-4s1.8 8 3.6 8 1.8-6 3.6-6 1.8 4 3.6 4 1.8-2 2.6-2"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconLock({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8.8 11V8.9a3.2 3.2 0 0 1 6.4 0V11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconEvidence({ className = "" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M10 4h4M12 4v5l4.8 8.2A1.8 1.8 0 0 1 15.3 20H8.7a1.8 1.8 0 0 1-1.5-2.8L12 9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9.5 14.2h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

const NAV_LINKS = ["Features", "How It Works", "Benefits"];

const FEATURES = [
  {
    icon: IconSleepLog,
    title: "Log Your Sleep",
    body: "Capture schedule, quality, latency, awakenings, mood, caffeine, and screen time — all in one concise daily log.",
  },
  {
    icon: IconAi,
    title: "AI Analysis",
    body: "Multi-agent AI detects insomnia patterns, ranks root causes, and surfaces insights you'd never spot alone.",
  },
  {
    icon: IconRecommendations,
    title: "Get Recommendations",
    body: "Personalized routines, breathing exercises, audio therapy, and hygiene tweaks — built around your data.",
  },
  {
    icon: IconProgress,
    title: "Track Progress",
    body: "Weekly reports and a unified dashboard that shows exactly how far you've come — and what to do next.",
  },
];

const BENEFITS = [
  { label: "Clinically-aligned metrics", icon: IconHealth },
  { label: "Personalized, not generic advice", icon: IconPersonalized },
  { label: "Understand your patterns", icon: IconPattern },
  { label: "Private & secure by design", icon: IconLock },
  { label: "Evidence-based recommendations", icon: IconEvidence },
];

const GLOW_COLORS = ["#848cfc", "#2222e9", "#38bdf8"];
const CARD_BG_COLOR = "##00008B";

export default function Landing() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const heroRef = useRef(null);

  useEffect(() => {
    // Google Fonts — Syne + DM Sans
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap";
    document.head.appendChild(link);

    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      document.head.removeChild(link);
    };
  }, []);

  const goSignup = () => navigate("/register");

  return (
    <div className="landing-page">
      {/* ── Galaxy Background ── */}
      <div className="galaxy-background" aria-hidden="true">
        <Galaxy
            starSpeed={0.5}
            density={1}
            hueShift={140}
            speed={0.1}
            glowIntensity={0.3}
            saturation={0}
            mouseRepulsion
            trackCursorGlobally
            repulsionStrength={2}
            twinkleIntensity={0.3}
            rotationSpeed={0.1}
            transparent
        />
      </div>
      {/* ── Navbar ── */}
      <nav className={`nav${scrolled ? " scrolled" : ""}`}>
        <div className="nav-logo">
          <BrandMark className="brand-mark" />
          <img className="nav-logo-img" src={numaLogo} alt="Numa logo" />
        </div>
        <div className="nav-links">
          {NAV_LINKS.map((l) => (
            <a key={l} href={`#${l.toLowerCase().replace(/\s+/g, "-")}`}>
              {l}
            </a>
          ))}
        </div>
        <button className="nav-cta" onClick={goSignup}>
          Sign Up Free
        </button>
      </nav>

      {/* ══════════════════════════════════════════ HERO */}
      <section className="hero" ref={heroRef}>
        <div className="hero-eyebrow">
          <IconMoon className="hero-eyebrow-icon" /> AI-Powered Sleep Intelligence
        </div>
        <h1 className="hero-headline">
          Sleep Better.{" "}
          <span>Understand Why.</span>
          {" "}Improve Faster.
        </h1>
        <p className="hero-sub">
          An intelligent platform that turns your sleep, mood, and lifestyle data
          into precise, personalized insights — so you finally rest the way you deserve.
        </p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={goSignup}>
            Get Started Free →
          </button>
          <button className="btn-ghost" onClick={() => document.getElementById("how-it-works").scrollIntoView()}>
            See How It Works
          </button>
        </div>
        <p className="hero-meta">No credit card required &nbsp;·&nbsp; Free to start</p>
      </section>

      <div className="section-divider" />

      {/* ══════════════════════════════════════════ HOW IT WORKS */}
      <section className="section" id="how-it-works">
        <p className="section-label">Process</p>
        <h2 className="section-title">How It Works</h2>
        <p className="section-sub">
          Four steps. One dashboard. A complete picture of your sleep — and a clear path to better nights.
        </p>

        <div className="feature-grid" id="features">
          {FEATURES.map((f, i) => (
            <FadeUp key={f.title}>
              {(() => {
                const FeatureIcon = f.icon;
                return (
              <BorderGlow
                edgeSensitivity={30}
                glowColor="40 80 80"
                backgroundColor={CARD_BG_COLOR}
                borderRadius={24}
                glowIntensity={1}
                coneSpread={25}
                animated={false}
                colors={GLOW_COLORS}
              >
                <div className="feature-card">
                  <FeatureIcon className="feature-icon" />
                  <div className="feature-title">{f.title}</div>
                  <p className="feature-body">{f.body}</p>
                  <div className="moon-deco" />
                </div>
              </BorderGlow>
                );
              })()}
            </FadeUp>
          ))}
        </div>
      </section>

      <div className="section-divider" />

      {/* ══════════════════════════════════════════ BENEFITS */}
      <section className="section" id="benefits">
        <p className="section-label">Why Numa</p>
        <h2 className="section-title">Built Around You</h2>
        <p className="section-sub">
          Every insight is grounded in evidence — and shaped by your unique patterns, not a generic template.
        </p>

        <div className="benefits-grid">
          {BENEFITS.map((b, i) => (
            <div key={b.label}>
              {(() => {
                const BenefitIcon = b.icon;
                return (
              <BorderGlow
                edgeSensitivity={30}
                glowColor="40 80 80"
                backgroundColor={CARD_BG_COLOR}
                borderRadius={20}
                glowIntensity={1}
                coneSpread={25}
                animated={false}
                colors={GLOW_COLORS}
              >
                <div className="benefit-card">
                  <BenefitIcon className="benefit-icon" />
                  <span className="benefit-label">{b.label}</span>
                </div>
              </BorderGlow>
                );
              })()}
            </div>
          ))}
        </div>
      </section>

      {/* ══════════════════════════════════════════ CTA */}
      <section className="cta-section">
        <BorderGlow
            edgeSensitivity={40}
            glowColor="80 40 120"
            backgroundColor={CARD_BG_COLOR}
            borderRadius={32}
            glowIntensity={1.2}
            coneSpread={30}
            animated={false}
            colors={GLOW_COLORS}
          >
            <div className="cta-box">
              <p className="section-label cta-label" style={{ textAlign: "center" }}>
                <BrandMark className="cta-label-icon" />
                Start Tonight
              </p>
              <h2 className="cta-headline">Ready to sleep better?</h2>
              <p className="cta-sub">
                Join thousands of people who finally understand — and control — their sleep.
              </p>
              <button className="btn-primary" onClick={goSignup} style={{ fontSize: "1.05rem", padding: "18px 52px" }}>
                Sign Up Now →
              </button>
              <p className="cta-fine">Free to start &nbsp;·&nbsp; No credit card needed</p>
            </div>
          </BorderGlow>
      </section>

      {/* ══════════════════════════════════════════ FOOTER */}
      <footer className="footer">
        <div className="footer-logo">
          <BrandMark className="brand-mark" />
          <img className="footer-logo-img" src={numaLogo} alt="Numa logo" />
        </div>
        <div className="footer-links">
          {["About", "Privacy", "Contact", "Blog"].map((l) => (
            <a key={l} href="#">{l}</a>
          ))}
        </div>
        <span className="footer-copy">© {new Date().getFullYear()} Somnia. All rights reserved.</span>
      </footer>
    </div>
  );
}

/* ── Scroll Fade-Up Utility ─────────────────────────────────────────────────── */
function FadeUp({ children }) {
  return <>{children}</>;
}