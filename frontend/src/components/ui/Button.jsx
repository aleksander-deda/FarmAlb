import './Button.css'

export default function Button({
  children,
  variant = 'primary',   // primary | secondary | ghost | danger
  size = 'md',           // sm | md | lg
  loading = false,
  fullWidth = false,
  type = 'button',
  disabled,
  onClick,
  ...props
}) {
  return (
    <button
      type={type}
      className={[
        'btn',
        `btn--${variant}`,
        `btn--${size}`,
        fullWidth ? 'btn--full' : '',
        loading  ? 'btn--loading' : '',
      ].filter(Boolean).join(' ')}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && <span className="btn__spinner" aria-hidden="true" />}
      <span className={loading ? 'btn__label btn__label--hidden' : 'btn__label'}>
        {children}
      </span>
    </button>
  )
}