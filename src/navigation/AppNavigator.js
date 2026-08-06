import { useEffect, useState } from 'react';
import TopScreen from '../TopScreen/TopScreen';
import SelectSendMoney from '../SelectSendMoney/SelectSendMoney';
import ProcessSendMoney from '../ProcessSendMoney/ProcessSendMoney';
import NextScreen from '../NextScreen/NextScreen';
import AuthScreen from '../auth/AuthScreen';
import { useAuth } from '../auth/AuthContext';
import { getMySummary } from '../api/accounts';

function AppNavigator() {
  const { session, initializing, login, signup, signOut } = useAuth();
  const [currentScreen, setCurrentScreen] = useState('profile');
  const [account, setAccount] = useState(session?.account || null);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadCount, setReloadCount] = useState(0);

  useEffect(() => {
    if (!session) {
      setAccount(null);
      return undefined;
    }

    let active = true;
    setLoading(true);
    setError('');

    // API連携ポイント: 画面表示時と送金完了後に最新残高をDBから再取得する。
    getMySummary()
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
  }, [reloadCount, session]);

  if (initializing) {
    return <p className="screen-message">ログイン状態を確認しています...</p>;
  }

  if (!session) {
    return <AuthScreen onLogin={login} onSignup={signup} />;
  }

  if (currentScreen === 'recipients') {
    return (
      <SelectSendMoney
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

  return (
    <TopScreen
      account={account}
      loading={loading}
      error={error}
      onSelectRecipient={() => setCurrentScreen('recipients')}
      onBilling={() => setCurrentScreen('billing')}
      onLogout={signOut}
    />
  );
}

export default AppNavigator;
