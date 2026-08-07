import './TopScreen.css';
import NavigationButton from '../components/NavigationButton';
import { resolveUserIcon } from '../userIcons';

function TopScreen({
  account,
  loading,
  error,
  onSelectRecipient,
  onInvoice,
  onInvoiceStatus,
  onLogout,
}) {
  const buttonWidth = '80vw';
  const buttonHeight = '7vh';
  const buttonTextColor = '#ffffff';

  const userName = account?.user_name || '読み込み中';
  const accountNumber = account?.account_number || '---';
  const accountBalance = account
    ? `${account.account_balance.toLocaleString('ja-JP')}円`
    : '---円';

  return (
    <div className="top-screen">
      <header className="user-profile">
        <div className="user-profile__main">
          <img
            src={resolveUserIcon(account?.user_icon)}
            className="user-profile__icon"
            alt={`${userName}のアイコン`}
          />
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
        <button type="button" className="top-screen__logout" onClick={onLogout}>
          ログアウト
        </button>
      </header>

      {error && <p className="screen-message screen-message--error">{error}</p>}

      <div className="navigation-actions">
        <NavigationButton
          width={buttonWidth}
          height={buttonHeight}
          textColor={buttonTextColor}
          disabled={loading || !account}
          onClick={onSelectRecipient}
        >
          送金する
        </NavigationButton>

        <NavigationButton
          width={buttonWidth}
          height={buttonHeight}
          textColor={buttonTextColor}
          onClick={onInvoice}
        >
          請求する
        </NavigationButton>

        <NavigationButton
          width={buttonWidth}
          height={buttonHeight}
          textColor={buttonTextColor}
          onClick={onInvoiceStatus}
        >
          請求状態確認
        </NavigationButton>
      </div>
    </div>
  );
}

export default TopScreen;
