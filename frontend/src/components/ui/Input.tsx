import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", ...props }, ref) => (
    <div className="input-group">
      {label && <label>{label}</label>}
      <input
        ref={ref}
        className={`input ${error ? "input-error" : ""} ${className}`}
        {...props}
      />
      {error && <span className="error-text">{error}</span>}
    </div>
  )
);

Input.displayName = "Input";
export default Input;
