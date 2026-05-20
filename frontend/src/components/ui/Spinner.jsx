import './Spinner.css'

export default function Spinner({ size = 'md', center = false }) {
  return (
    <div className={`spinner-wrap ${center ? 'spinner-wrap--center' : ''}`}>
      <div className={`spinner spinner--${size}`} aria-label="Duke ngarkuar..." role="status" />
    </div>
  )
}