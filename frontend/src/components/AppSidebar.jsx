import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import "./AppSidebar.css";

const API_BASE = "http://localhost:8000";
const SIDEBAR_STATE_KEY = "wellness_sidebar_collapsed";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/dashboard", icon: "dashboard", tone: "1" },
  { label: "Sleep Log", path: "/sleep-log", icon: "moon", tone: "2" },
  { label: "Lifestyle", path: "/lifestyle", icon: "leaf", tone: "3" },
  { label: "Journal", path: "/journal", icon: "book", tone: "4" },
  { label: "Routine Optimizer", path: "/routine-optimizer", icon: "magic", tone: "5" },
  { label: "Audio Therapy", path: "/audio-therapy", icon: "wave", tone: "6" },
  { label: "Weekly Report", path: "/weekly-report", icon: "chart", tone: "7" },
];

function SidebarIcon({ name, tone }) {
  const className = `wellness-sidebar-icon wellness-sidebar-icon--${tone}`;

  if (name === "dashboard") {
    return (
      <span className={className} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <rect x="4" y="4" width="7" height="7" rx="1.4" />
          <rect x="13" y="4" width="7" height="4.8" rx="1.4" />
          <rect x="13" y="11.2" width="7" height="8.8" rx="1.4" />
          <rect x="4" y="13.2" width="7" height="6.8" rx="1.4" />
        </svg>
      </span>
    );
  }

  if (name === "moon") {
    return (
      <span className={className} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M14.1 3.4A8.8 8.8 0 1 0 20.5 18 9.2 9.2 0 0 1 14.1 3.4Z" />
        </svg>
      </span>
    );
  }

  if (name === "leaf") {
    return (
      <span className={className} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M19.6 4.9c-6.6.2-11.1 2.9-13 7.5-1.2 2.8-.7 5.5 1.2 7.2 1.8 1.6 4.3 1.9 6.8.8 4.5-1.9 7.1-6.5 7.2-13.2 0-1.2-1-2.3-2.2-2.3Z" />
          <path d="M8 16.5c2.6-2.5 5.1-4.6 8.3-6.4" />
        </svg>
      </span>
    );
  }

  if (name === "book") {
    return (
      <span className={className} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M6 4.7h7.4a3.1 3.1 0 0 1 3.1 3.1V19H9a3 3 0 0 0-3 3V4.7Z" />
          <path d="M18 19h-8.6a3 3 0 0 0-3 3" />
        </svg>
      </span>
    );
  }

  if (name === "magic") {
    return (
      <span className={className} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="m5 19 9.2-9.2 3 3L8 22H5v-3Z" />
          <path d="m13.2 5.8 1.6-1.6M16.8 9.4l1.6-1.6M8.6 7.2l1.2-2.8M10.8 10.8l2.8-1.2" />
        </svg>
      </span>
    );
  }

  if (name === "wave") {
    return (
      <span className={className} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M4 13c1.4 0 1.4-2.8 2.8-2.8S8.2 15.8 9.6 15.8 11 9 12.4 9s1.4 4.2 2.8 4.2S16.6 11 18 11s1.4 2 2 2" />
        </svg>
      </span>
    );
  }

  if (name === "chart") {
    return (
      <span className={className} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M4 20h16" />
          <path d="M7 20v-8M12 20V8M17 20v-5" />
        </svg>
      </span>
    );
  }

  if (name === "logout") {
    return (
      <span className={className} aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M10 4H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3" />
          <path d="M14.5 8.5 19 12l-4.5 3.5" />
          <path d="M19 12H10" />
        </svg>
      </span>
    );
  }

  return (
    <span className={className} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M12 12a4.2 4.2 0 1 0 0-8.4A4.2 4.2 0 0 0 12 12Z" />
        <path d="M4.6 20.4a7.4 7.4 0 0 1 14.8 0" />
      </svg>
    </span>
  );
}

export default function AppSidebar() {
  const navigate = useNavigate();
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    const savedState = localStorage.getItem(SIDEBAR_STATE_KEY);
    if (savedState === "1") {
      setIsCollapsed(true);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(SIDEBAR_STATE_KEY, isCollapsed ? "1" : "0");
  }, [isCollapsed]);

  const toggleSidebar = () => {
    setIsCollapsed((prev) => !prev);
  };

  const handleSignOut = async () => {
    const accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");

    try {
      if (accessToken && refreshToken) {
        await fetch(`${API_BASE}/accounts/api/logout/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ refresh: refreshToken }),
        });
      }
    } catch {
      // Sign out should still proceed locally if server call fails.
    }

    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login", { replace: true });
  };

  return (
    <aside className={`wellness-sidebar${isCollapsed ? " is-collapsed" : ""}`} aria-label="Main sidebar">
      <div>
        <div className="wellness-sidebar-top">
          <div className="wellness-brand">
            <div className="wellness-brand-mark" aria-hidden="true" />
            <div className="wellness-brand-copy">
              <p className="wellness-brand-title">Numa</p>
              <p className="wellness-brand-sub">Sleep Companion</p>
            </div>
          </div>

          <button
            type="button"
            className="wellness-sidebar-toggle"
            onClick={toggleSidebar}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!isCollapsed}
          >
            <svg
              className={`wellness-sidebar-toggle-icon${isCollapsed ? " is-collapsed" : ""}`}
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <path d="M14 6 8 12l6 6" />
            </svg>
          </button>
        </div>

        <nav className="wellness-nav" aria-label="Primary navigation">
          <span className="wellness-nav-section-label" aria-hidden="true">Navigation</span>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `wellness-nav-item${isActive ? " is-active" : ""}`
              }
              end={item.path === "/dashboard"}
              title={isCollapsed ? item.label : undefined}
            >
              <SidebarIcon name={item.icon} tone={item.tone} />
              <span className="wellness-nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="wellness-sidebar-footer">
        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `wellness-profile-link${isActive ? " is-active" : ""}`
          }
          title={isCollapsed ? "Profile" : undefined}
        >
          <SidebarIcon name="profile" tone="profile" />
          <span className="wellness-nav-label">Profile</span>
        </NavLink>

        <button
          type="button"
          className="wellness-signout-btn"
          onClick={handleSignOut}
          title={isCollapsed ? "Sign out" : undefined}
        >
          <SidebarIcon name="logout" tone="6" />
          <span className="wellness-nav-label">Sign out</span>
        </button>
      </div>
    </aside>
  );
}
