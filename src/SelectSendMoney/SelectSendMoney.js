import { useEffect, useState } from 'react';
import { fetchUsers } from '../api/users';
import user_icon from './user_icon.png';
import './SelectSendMoney.css';

function SelectSendMoney() {
  const [users, setUsers] = useStates([]);

  return (
    <main className="select-send-money">
      <div className="select-send-money">
        <h1 className="select-send-money__title">
          送信先一覧
        </h1>
        {users.map((user) => (
          <li key={user.id} className="select-send-money__user">
            <img src={user_icon} className=".select-send-money__icon" alt="logo" />
            {/* <div className="select-send-money__user-name">
              user.user_name
            </div> */}
          </li>
        ))}
        {/* <div className="select-send-money__list">
          とりまかりぐみ
        </div> */}
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
