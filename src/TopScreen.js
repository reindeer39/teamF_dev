import { useState } from 'react';
import './TopScreen.css';
import icon from './icons/human1.png';
import NextScreen from './NextScreen';
import NavigationButton from './components/NavigationButton';

function TopScreen() {
  const [currentScreen, setCurrentScreen] = useState('profile');
  const userName = 'ユーザー';
  const accountNumber = '1234567';
  const accountBalance = '80,000円';
  const buttonWidth = '80vw';
  const buttonHeight = '72px';
  const buttonColor = '#316745';
  const buttonHoverColor = '#9ca3af';
  const buttonTextColor = '#ffffff';

  if (currentScreen === 'next') {
    return <NextScreen onBack={() => setCurrentScreen('profile')} />;
  }

  return (
    <div className="top-screen">
      <header className="user-profile">
        <div className="user-profile__main">
          <img
            src={icon}
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
          <strong className="user-profile__balance-value">
            {accountBalance}
          </strong>
        </div>
      </header>

      <div className="navigation-actions">
        <NavigationButton
          width={buttonWidth}
          height={buttonHeight}
          backgroundColor={buttonColor}
          hoverColor={buttonHoverColor}
          textColor={buttonTextColor}
          onClick={() => setCurrentScreen('next')}
        >
          送金する
        </NavigationButton>

        <NavigationButton
          width={buttonWidth}
          height={buttonHeight}
          backgroundColor={buttonColor}
          hoverColor={buttonHoverColor}
          textColor={buttonTextColor}
          onClick={() => setCurrentScreen('next')}
        >
          請求する
        </NavigationButton>
      </div>
    </div>
  );
}

export default TopScreen;
