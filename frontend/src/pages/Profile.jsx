import { useEffect, useState } from "react";
import AppSidebar from "../components/AppSidebar";
import "./Profile.css";

const API_BASE = "http://localhost:8000";

const DEFAULT_FORM = {
  full_name: "",
  age: "",
  gender: "",
  country: "",
  timezone: "UTC",
  language: "en",
  email: "",
  notifications_enabled: true,
};

export default function Profile() {
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [formData, setFormData] = useState(DEFAULT_FORM);

  useEffect(() => {
    const loadProfile = async () => {
      setIsLoading(true);
      setError("");
      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("You are not logged in. Please sign in first.");
        setIsLoading(false);
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/profiles/api/me/`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!res.ok) {
          setError(data.detail || "Could not load your profile.");
          setIsLoading(false);
          return;
        }

        setFormData({
          full_name: data.full_name ?? "",
          age: data.age ?? "",
          gender: data.gender ?? "",
          country: data.country ?? "",
          timezone: data.timezone ?? "UTC",
          language: data.language ?? "en",
          email: data.email ?? "",
          notifications_enabled: Boolean(data.notifications_enabled),
        });
      } catch {
        setError("Network error. Make sure Django server is running.");
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setSuccess("");
    setError("");

    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("You are not logged in. Please sign in first.");
      setIsSaving(false);
      return;
    }

    const payload = {
      full_name: formData.full_name,
      age: Number(formData.age),
      gender: formData.gender,
      country: formData.country,
      timezone: formData.timezone,
      language: formData.language,
      notifications_enabled: formData.notifications_enabled,
    };

    try {
      const res = await fetch(`${API_BASE}/profiles/api/me/`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        const details =
          typeof data === "object"
            ? Object.entries(data)
                .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
                .join(" | ")
            : "Could not save profile.";
        setError(details);
        setIsSaving(false);
        return;
      }

      setFormData({
        full_name: data.full_name ?? "",
        age: data.age ?? "",
        gender: data.gender ?? "",
        country: data.country ?? "",
        timezone: data.timezone ?? "UTC",
        language: data.language ?? "en",
        email: data.email ?? "",
        notifications_enabled: Boolean(data.notifications_enabled),
      });
      setSuccess("Profile saved successfully.");
      setIsEditing(false);
    } catch {
      setError("Network error while saving profile.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="wellness-shell">
      <AppSidebar />

      <main className="wellness-content">
        <section className="profile-panel">
          <div className="profile-header">
            <div>
              <p className="profile-chip">Personal Space</p>
              <h1>My Profile</h1>
              <p className="profile-sub">Manage your personal information and preferences.</p>
            </div>

            {!isEditing ? (
              <button className="profile-btn profile-btn-edit" onClick={() => setIsEditing(true)}>
                Edit Profile
              </button>
            ) : (
              <button className="profile-btn profile-btn-save" onClick={handleSave} disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Changes"}
              </button>
            )}
          </div>

          {error ? <p className="profile-message profile-message-error">{error}</p> : null}
          {success ? <p className="profile-message profile-message-success">{success}</p> : null}

          {isLoading ? (
            <p className="profile-loading">Loading your profile...</p>
          ) : (
            <>
              <div className="profile-hero">
                <div className="profile-avatar" aria-hidden="true">
                  {(formData.full_name || "U").charAt(0).toUpperCase()}
                </div>
                <div>
                  <h2>{formData.full_name || "User"}</h2>
                  <p>{formData.email || "No email yet"}</p>
                </div>
              </div>

              <div className="profile-grid">
                <label className="profile-field">
                  <span>Full Name</span>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData((prev) => ({ ...prev, full_name: e.target.value }))}
                    disabled={!isEditing}
                  />
                </label>

                <label className="profile-field">
                  <span>Age</span>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={formData.age}
                    onChange={(e) => setFormData((prev) => ({ ...prev, age: e.target.value }))}
                    disabled={!isEditing}
                  />
                </label>

                <label className="profile-field">
                  <span>Gender</span>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData((prev) => ({ ...prev, gender: e.target.value }))}
                    disabled={!isEditing}
                  >
                    <option value="">Select</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="X">Prefer not to say</option>
                  </select>
                </label>

                <label className="profile-field">
                  <span>Country</span>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) => setFormData((prev) => ({ ...prev, country: e.target.value }))}
                    disabled={!isEditing}
                  />
                </label>

                <label className="profile-field">
                  <span>Timezone</span>
                  <input
                    type="text"
                    value={formData.timezone}
                    onChange={(e) => setFormData((prev) => ({ ...prev, timezone: e.target.value }))}
                    disabled={!isEditing}
                  />
                </label>

                <label className="profile-field">
                  <span>Language</span>
                  <select
                    value={formData.language}
                    onChange={(e) => setFormData((prev) => ({ ...prev, language: e.target.value }))}
                    disabled={!isEditing}
                  >
                    <option value="en">English</option>
                    <option value="fr">French</option>
                    <option value="es">Spanish</option>
                  </select>
                </label>

                <label className="profile-field profile-field-full">
                  <span>Email</span>
                  <input type="email" value={formData.email} disabled />
                </label>

                <label className="profile-switch-wrap">
                  <span>Notifications</span>
                  <button
                    type="button"
                    className={`profile-switch${formData.notifications_enabled ? " is-on" : ""}`}
                    onClick={() =>
                      isEditing &&
                      setFormData((prev) => ({
                        ...prev,
                        notifications_enabled: !prev.notifications_enabled,
                      }))
                    }
                    aria-pressed={formData.notifications_enabled}
                    disabled={!isEditing}
                  >
                    <span className="profile-switch-knob" />
                  </button>
                </label>
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
