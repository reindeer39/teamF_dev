import './BackButton.css';

function BackButton({ onClick, className = '', ariaLabel = '戻る' }) {
  return (
    <button
      type="button"
      className={`back-button ${className}`.trim()}
      aria-label={ariaLabel}
      onClick={onClick}
    >
      <span aria-hidden="true">&lt;</span>
    </button>
  );
}

export default BackButton;
