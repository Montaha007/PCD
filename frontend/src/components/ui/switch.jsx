import './ui.css';

export function Switch({ id, checked, onCheckedChange }) {
  return (
    <button
      type="button"
      id={id}
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange(!checked)}
      className={`sl-switch${checked ? ' is-on' : ''}`}
    >
      <span className="sl-switch-knob" />
    </button>
  );
}
