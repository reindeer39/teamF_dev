import './TopBar.css';
import BackButton from './BackButton';

function TopBar({ title, onBack, onLogout }) {
  return (
    <header className="top-bar">
      <div className="top-bar__side">
        {onBack && <BackButton onClick={onBack} />}
      </div>
      <h1 className="top-bar__title">{title}</h1>
      <div className="top-bar__side">
        {onLogout && (
          <button
            type="button"
            className="top-bar__logout"
            aria-label="ログアウト"
            title="ログアウト"
            onClick={onLogout}
          >
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              focusable="false"
            >
              <path d="M10 4H5.5A1.5 1.5 0 0 0 4 5.5v13A1.5 1.5 0 0 0 5.5 20H10" />
              <path d="M14 8l4 4-4 4" />
              <path d="M9 12h9" />
            </svg>
          </button>
        )}
      </div>
    </header>
  );
}

export default TopBar;
