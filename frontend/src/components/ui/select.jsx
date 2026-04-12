import { createContext, useContext } from 'react';
import './ui.css';

const SelectCtx = createContext(null);

export function Select({ value, onValueChange, children }) {
  return (
    <SelectCtx.Provider value={{ value, onValueChange }}>
      <div className="sl-select-wrap">{children}</div>
    </SelectCtx.Provider>
  );
}

// Stub — the native <select> is rendered inside SelectContent
export function SelectTrigger() { return null; }
export function SelectValue() { return null; }

export function SelectContent({ children }) {
  const { value, onValueChange } = useContext(SelectCtx);
  return (
    <select
      className="sl-native-select"
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
    >
      {children}
    </select>
  );
}

export function SelectItem({ value, children }) {
  return <option value={value}>{children}</option>;
}
