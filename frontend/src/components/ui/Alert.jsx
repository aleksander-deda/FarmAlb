import './Alert.css'

const ICONS = {
  error:   '✕',
  success: '✓',
  info:    'ℹ',
  warning: '⚠',
}

export default function Alert({ type = 'info', title, children, onDismiss }) {
  return (
    <div className={`alert alert--${type}`} role="alert">
      <span className="alert__icon" aria-hidden>{ICONS[type]}</span>
      <div className="alert__body">
        {title && <p className="alert__title">{title}</p>}
        {children && <p className="alert__message">{children}</p>}
      </div>
      {onDismiss && (
        <button className="alert__close" onClick={onDismiss} aria-label="Dismiss">✕</button>
      )}
    </div>
  )
}