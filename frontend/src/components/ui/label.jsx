import './ui.css';

export function Label({ children, htmlFor, className = '' }) {
  return (
    <label htmlFor={htmlFor} className={`sl-label ${className}`}>
      {children}
    </label>
  );
}
