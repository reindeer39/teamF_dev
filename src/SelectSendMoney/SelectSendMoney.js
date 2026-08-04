import user_icon from './user_icon.png';
import './SelectSendMoney.css';

function SelectSendMoney() {
  return (
    <main className="select-send-money">
      <div className="select-send-money">
        <h1 className="select-send-money__title">
          送信先一覧
        </h1>

        <div className="select-send-money__list">
          とりまかりぐみ
        </div>
      </div>
    </main>
    // <div className="App">
    //   <header className="App-header">
    //     <img src={user_icon} className="App-logo" alt="logo" />
    //     <p>
    //       Lets create SendMoney App!
    //     </p>
    //     <a
    //       className="App-link"
    //       href="https://reactjs.org"
    //       target="_blank"
    //       rel="noopener noreferrer"
    //     >
    //       Learn React
    //     </a>
    //   </header>
    // </div>
  );
}

export default SelectSendMoney;
