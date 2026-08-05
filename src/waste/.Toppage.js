import user_icon from './backup/user_icon.png';
import './Toppage.css';

function Toppage({ onOpenSubpage }) {
  return (
    <div className="App">
      <header className="App-header">
        {/* <img src={user_icon} className="App-logo" alt="logo" /> */}
        <p>
          Edit <code>src/Toppage.js</code> and save to reload.
        </p>
        <p>
          v<img src={user_icon} className="App-logo" alt="logo" />v
        </p>
        {/* <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn Hokkaido
        </a> */}
        <a
          className="App-link"
          href="#subpage"
          onClick={(event) => {
            event.preventDefault();
            onOpenSubpage();
          }}
        >
          Subpage画面を開く
        </a>
      </header>
    </div>
  );
}

export default Toppage;
