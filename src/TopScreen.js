import { useState } from 'react';
import './TopScreen.css';
import icon from '../images/human1.png';
import NavigationButton from './components/NavigationButton';
import BillingScreen from './BillingScreen';
import TransferScreen from './TransferScreen';
import { ACCOUNT_NUMBER } from './account';

const USER = {
  name: 'ユーザー',
  accountBalance: '80,000円',
};

const NAVIGATION_BUTTON_STYLE = {
  width: '80vw',
  height: '72px',
  backgroundColor: '#316745',
  hoverColor: '#9ca3af',
  textColor: '#f5f5f5',
};

const NAVIGATION_BUTTONS = [
  { label: '送金する', destination: 'transfer' },
  { label: '請求する', destination: 'billing' },
];

function TopScreen() {
  const [currentScreen, setCurrentScreen] = useState('profile');

  const openScreen = (screenName) => setCurrentScreen(screenName);
  const openProfileScreen = () => setCurrentScreen('profile');

  if (currentScreen === 'transfer') {
    return <TransferScreen onBack={openProfileScreen} />;
  }

  if (currentScreen === 'billing') {
    return <BillingScreen onBack={openProfileScreen} />;
  }

  return (
    <div className="top-screen">
      <header className="user-profile">
        <div className="user-profile__main">
          <img
            src={icon}
            className="user-profile__icon"
            alt={`${USER.name}のアイコン`}
          />
          <div className="user-profile__details">
            <span className="user-profile__name">{USER.name}</span>
            <span className="user-profile__account-number">
              口座番号：{ACCOUNT_NUMBER}
            </span>
          </div>
        </div>

        <div className="user-profile__balance">
          <span className="user-profile__balance-label">預金残高</span>
          <strong className="user-profile__balance-value">
            {USER.accountBalance}
          </strong>
        </div>
      </header>

      <div className="navigation-actions">
        {NAVIGATION_BUTTONS.map(({ label, destination }) => (
          <NavigationButton
            key={label}
            {...NAVIGATION_BUTTON_STYLE}
            onClick={() => openScreen(destination)}
          >
            {label}
          </NavigationButton>
        ))}
      </div>
    </div>
  );
}

export default TopScreen;
