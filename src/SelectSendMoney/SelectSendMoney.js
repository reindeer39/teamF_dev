import { useEffect, useState } from 'react';
import { fetchUsers } from '../api/users';
import user_icon from '../images/human1.png';
import './SelectSendMoney.css';

function SelectSendMoney({ onSelectUser }) {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    async function loadUsers() {
      const result = await fetchUsers();
      setUsers(result);
    }

    loadUsers();
  }, []);

  return (
    <main className="select-send-money">
      <h1 className="select-send-money__title">送信先一覧</h1>

      <ul className="select-send-money__list">
        {users.map((user) => (
          <li key={user.id} className="select-send-money__user">
            <button
              type="button"
              className="select-send-money__user-button"
              onClick={() => onSelectUser(user.user_id)}
            >
              <img
                className="select-send-money__icon"
                src={user.iconUrl ?? user_icon}
                alt=""
              />
            </button>
            <span>{user.name}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}

export default SelectSendMoney;
