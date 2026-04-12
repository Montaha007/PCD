import './ui.css';

export function Button({ children, type = 'button', className = '', ...props }) {
  return (
    <button type={type} className={`sl-btn ${className}`} {...props}>
      {children}
    </button>
  );
}
