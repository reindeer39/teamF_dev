import { useEffect, useState } from 'react';
import { getRecipientList } from '../api/accounts';
import userIcon from '../images/human1.png';
import './SelectSendMoney.css';

function SelectSendMoney({ accountNumber, onSelectRecipient, onBack }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    // API連携ポイント: 送金元以外の口座をDBから取得して一覧表示する。
    getRecipientList(accountNumber)
      .then((data) => {
        if (active) setUsers(data.recipient_list);
      })
      .catch((apiError) => {
        if (active) setError(`送金先を取得できませんでした: ${apiError.message}`);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [accountNumber]);

  return (
    <main className="select-send-money">
      <div className="select-send-money__header">
        <button type="button" className="text-button" onClick={onBack}>戻る</button>
        <h1 className="select-send-money__title">送金先一覧</h1>
      </div>

      {loading && <p className="screen-message">読み込み中...</p>}
      {error && <p className="screen-message screen-message--error">{error}</p>}

      <ul className="select-send-money__list">
        {users.map((user) => (
          <li key={user.account_number} className="select-send-money__user">
            <button
              type="button"
              className="select-send-money__user-button"
              onClick={() => onSelectRecipient(user)}
            >
              <img src={userIcon} className="select-send-money__icon" alt="" />
              <span className="select-send-money__user-details">
                <strong>{user.user_name}</strong>
                <span>口座番号：{user.account_number}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}

export default SelectSendMoney;
