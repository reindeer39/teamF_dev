import './TopBar.css';
import BackButton from './BackButton';

function TopBar({ title, onBack }) {
  return (
    <header className="top-bar">
      <div className="top-bar__side">
        {onBack && <BackButton onClick={onBack} />}
      </div>
      <h1 className="top-bar__title">{title}</h1>
      <div className="top-bar__side" aria-hidden="true" />
    </header>
  );
}

export default TopBar;
