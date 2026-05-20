import './Input.css'

export default function Input({
  label,
  error,
  hint,
  id,
  type = 'text',
  required,
  ...props
}) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className={`field ${error ? 'field--error' : ''}`}>
      {label && (
        <label className="field__label" htmlFor={inputId}>
          {label}
          {required && <span className="field__required" aria-hidden>*</span>}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        className="field__input"
        aria-invalid={!!error}
        aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
        {...props}
      />
      {hint && !error && (
        <p id={`${inputId}-hint`} className="field__hint">{hint}</p>
      )}
      {error && (
        <p id={`${inputId}-error`} className="field__error" role="alert">{error}</p>
      )}
    </div>
  )
}