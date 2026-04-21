// src/pages/lifestyle/LifestyleForm.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { submitLifestyleLog } from "../../api/lifestyle";
import "./LifestyleForm.css";

// Only the 6 raw features — derived ones are computed by Django
const initialState = {
  date: new Date().toISOString().split("T")[0],
  WorkoutTime: 0.5,
  ReadingTime: 0.5,
  PhoneTime: 2,
  WorkHours: 8,
  CaffeineIntake: 100,
  RelaxationTime: 1,
};

export default function LifestyleForm() {
  const [form, setForm] = useState(initialState);
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  // Live preview of what Django will compute — purely UX, not sent
  const previewWorkXCaffeine = (
    Number(form.WorkHours) * Number(form.CaffeineIntake)
  ).toFixed(0);
  const previewScreenIntensity = (
    Number(form.PhoneTime) / (Number(form.RelaxationTime) + 1)
  ).toFixed(2);

  const buildPayload = () => ({
    date: form.date,
    WorkoutTime: Number(form.WorkoutTime),
    ReadingTime: Number(form.ReadingTime),
    PhoneTime: Number(form.PhoneTime),
    WorkHours: Number(form.WorkHours),
    CaffeineIntake: Number(form.CaffeineIntake),
    RelaxationTime: Number(form.RelaxationTime),
    // Derived features intentionally omitted — Django computes them
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFieldErrors({});

    try {
      await submitLifestyleLog(buildPayload());
      toast.success("Lifestyle log saved", {
        description: "Your data has been sent to the AI pipeline.",
      });
      navigate("/dashboard");
    } catch (err) {
      if (err.status === 400 && err.data && typeof err.data === "object") {
        setFieldErrors(err.data);
        toast.error("Please fix the highlighted fields.");
      } else if (err.status === 401) {
        toast.error("Session expired — please log in again.");
        navigate("/login");
      } else {
        toast.error("Could not save your lifestyle log", {
          description: err.data?.detail || "Please try again.",
        });
      }
    } finally {
      setSubmitting(false);
    }
  };

  const ErrMsg = ({ name }) =>
    fieldErrors[name] ? (
      <small className="field-error">
        {Array.isArray(fieldErrors[name])
          ? fieldErrors[name][0]
          : String(fieldErrors[name])}
      </small>
    ) : null;

  // Reusable slider field — every raw input is a slider since they're all bounded
  const SliderField = ({ name, label, min, max, step, unit }) => (
    <div className="field">
      <label htmlFor={name}>
        {label}: <strong>{form[name]}{unit}</strong>
      </label>
      <input
        id={name}
        type="range"
        name={name}
        min={min}
        max={max}
        step={step}
        value={form[name]}
        onChange={handleChange}
      />
      <div className="range-labels">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
      <ErrMsg name={name} />
    </div>
  );

  return (
    <div className="lifestyle-page">
      <header className="lifestyle-header">
        <h1>Lifestyle Log</h1>
        <p>
          Capture today's habits. These six signals feed the lifestyle model
          that detects sleep-disrupting patterns.
        </p>
      </header>

      <form className="lifestyle-form" onSubmit={handleSubmit} noValidate>
        {/* ---------- Date ---------- */}
        <section className="form-section">
          <label htmlFor="date">Date</label>
          <input
            id="date"
            type="date"
            name="date"
            value={form.date}
            onChange={handleChange}
            max={new Date().toISOString().split("T")[0]}
            required
          />
          <ErrMsg name="date" />
        </section>

        {/* ---------- Activity ---------- */}
        <section className="form-section">
          <h2>Activity</h2>
          <SliderField
            name="WorkoutTime"
            label="Workout time"
            min={0} max={3} step={0.25} unit="h"
          />
          <SliderField
            name="ReadingTime"
            label="Reading time"
            min={0} max={2} step={0.25} unit="h"
          />
          <SliderField
            name="RelaxationTime"
            label="Relaxation time"
            min={0} max={2} step={0.25} unit="h"
          />
        </section>

        {/* ---------- Screens & Work ---------- */}
        <section className="form-section">
          <h2>Screens & Work</h2>
          <SliderField
            name="PhoneTime"
            label="Phone time"
            min={1} max={5} step={0.25} unit="h"
          />
          <SliderField
            name="WorkHours"
            label="Work hours"
            min={4} max={10} step={0.5} unit="h"
          />
        </section>

        {/* ---------- Caffeine ---------- */}
        <section className="form-section">
          <h2>Caffeine</h2>
          <SliderField
            name="CaffeineIntake"
            label="Caffeine intake"
            min={0} max={300} step={10} unit="mg"
          />
          <small className="hint">
            1 espresso ≈ 65mg • 1 coffee ≈ 95mg • 1 energy drink ≈ 80mg
          </small>
        </section>

        {/* ---------- Live preview of derived features ---------- */}
        <section className="form-section preview-section">
          <h2>Computed by the AI pipeline</h2>
          <div className="preview-grid">
            <div className="preview-card">
              <span className="preview-label">Work × Caffeine</span>
              <span className="preview-value">{previewWorkXCaffeine}</span>
              <small>WorkHours × CaffeineIntake</small>
            </div>
            <div className="preview-card">
              <span className="preview-label">Screen Time Intensity</span>
              <span className="preview-value">{previewScreenIntensity}</span>
              <small>PhoneTime ÷ (RelaxationTime + 1)</small>
            </div>
          </div>
          <small className="hint">
            These are calculated automatically — you don't submit them.
          </small>
        </section>

        <div className="form-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate("/dashboard")}
            disabled={submitting}
          >
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? "Saving…" : "Save lifestyle log"}
          </button>
        </div>
      </form>
    </div>
  );
}