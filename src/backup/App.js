import logo from './icon/human2.png';
import './App.css';
import { useState } from 'react';
import TransferScreen from './TransferScreen';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          ウイルスに感染しました
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>

        <button>送金する</button>
      </header>
    </div>
  );
}

export default App;
