import logo from './logo.svg';
import './Subpage.css';

function Subpage() {
  return (
    <div className="Subpage">
      <header className="Subpage-header">
        <img src={logo} className="Subpage-logo" alt="logo" />

        <p>Subpageです</p>

        <a
          className="Subpage-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default Subpage;
