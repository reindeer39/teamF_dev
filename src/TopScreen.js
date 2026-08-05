import { useEffect, useState } from 'react';
import './TopScreen.css';
import icon from './icons/human1.png';
import NextScreen from './NextScreen';
import ProcessSendMoney from './ProcessSendMoney';
import SelectSendMoney from './SelectSendMoney/SelectSendMoney';
import { ACCOUNT_NUMBER } from './account';
import { getUserSummary } from './api/user';
import NavigationButton from './components/NavigationButton';

function TopScreen() {
  const [currentScreen, setCurrentScreen] = useState('profile');
  const [account, setAccount] = useState(null);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadCount, setReloadCount] = useState(0);
  const buttonWidth = '80vw';
  const buttonHeight = '72px';
  const buttonColor = '#316745';
  const buttonHoverColor = '#9ca3af';
  const buttonTextColor = '#ffffff';

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');

    // API連携ポイント: 画面表示時と送金完了後に最新残高をDBから再取得する。
    getUserSummary(ACCOUNT_NUMBER)
      .then((data) => {
        if (active) setAccount(data);
      })
      .catch((apiError) => {
        if (active) setError(`口座情報を取得できませんでした: ${apiError.message}`);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [reloadCount]);

  if (currentScreen === 'recipients') {
    return (
      <SelectSendMoney
        senderAccountNumber={ACCOUNT_NUMBER}
        onBack={() => setCurrentScreen('profile')}
        onSelectRecipient={(recipient) => {
          setSelectedRecipient(recipient);
          setCurrentScreen('transfer');
        }}
      />
    );
  }

  if (currentScreen === 'transfer' && selectedRecipient) {
    return (
      <ProcessSendMoney
        senderAccountNumber={ACCOUNT_NUMBER}
        recipientAccountNumber={selectedRecipient.account_number}
        accountBalance={account?.account_balance || 0}
        onBack={() => setCurrentScreen('recipients')}
        onTransferComplete={() => {
          setSelectedRecipient(null);
          setCurrentScreen('profile');
          setReloadCount((count) => count + 1);
        }}
      />
    );
  }

  if (currentScreen === 'billing') {
    return <NextScreen onBack={() => setCurrentScreen('profile')} />;
  }

  const userName = account?.user_name || '読み込み中';
  const accountNumber = account?.account_number || ACCOUNT_NUMBER;
  const accountBalance = account
    ? `${account.account_balance.toLocaleString('ja-JP')}円`
    : '---円';

  return (
    <div className="top-screen">
      <header className="user-profile">
        <div className="user-profile__main">
          <img src={icon} className="user-profile__icon" alt={`${userName}のアイコン`} />
          <div className="user-profile__details">
            <span className="user-profile__name">{userName}</span>
            <span className="user-profile__account-number">
              口座番号：{accountNumber}
            </span>
          </div>
        </div>

        <div className="user-profile__balance">
          <span className="user-profile__balance-label">口座残高</span>
          <strong className="user-profile__balance-value">{accountBalance}</strong>
        </div>
      </header>

      {error && <p className="screen-message screen-message--error">{error}</p>}

      <div className="navigation-actions">
        <NavigationButton
          width={buttonWidth}
          height={buttonHeight}
          backgroundColor={buttonColor}
          hoverColor={buttonHoverColor}
          textColor={buttonTextColor}
          disabled={loading || !account}
          onClick={() => setCurrentScreen('recipients')}
        >
          送金する
        </NavigationButton>

        <NavigationButton
          width={buttonWidth}
          height={buttonHeight}
          backgroundColor={buttonColor}
          hoverColor={buttonHoverColor}
          textColor={buttonTextColor}
          onClick={() => setCurrentScreen('billing')}
        >
          請求する
        </NavigationButton>
      </div>
    </div>
  );
}

export default TopScreen;
