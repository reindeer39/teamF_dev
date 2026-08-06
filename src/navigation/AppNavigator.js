import { useEffect, useState } from 'react';
import { Route, Routes } from 'react-router';

import TopScreen from '../TopScreen/TopScreen';
import SelectSendMoney from '../SelectSendMoney/SelectSendMoney';
import ProcessSendMoney from '../ProcessSendMoney/ProcessSendMoney';
import ProcessPayment from '../ProcessPayment/ProcessPayment';
import NextScreen from '../NextScreen/NextScreen';
import { ACCOUNT_NUMBER } from '../account';
import { getUserSummary } from '../api/users';

function MainAppFlow() {
  const [currentScreen, setCurrentScreen] = useState('profile');
  const [account, setAccount] = useState(null);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadCount, setReloadCount] = useState(0);

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError('');

    getUserSummary(ACCOUNT_NUMBER)
      .then((data) => {
        if (active) {
          setAccount(data);
        }
      })
      .catch((apiError) => {
        if (active) {
          setError(
            `口座情報を取得できませんでした: ${apiError.message}`
          );
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [reloadCount]);

  if (currentScreen === 'recipients') {
    return (
      <SelectSendMoney
        senderAccountNumber={ACCOUNT_NUMBER}
        onBack={() => {
          setCurrentScreen('profile');
        }}
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
        recipientAccountNumber={
          selectedRecipient.account_number
        }
        accountBalance={account?.account_balance || 0}
        onBack={() => {
          setCurrentScreen('recipients');
        }}
        onTransferComplete={() => {
          setSelectedRecipient(null);
          setCurrentScreen('profile');
          setReloadCount((count) => count + 1);
        }}
      />
    );
  }

  if (currentScreen === 'billing') {
    return (
      <NextScreen
        onBack={() => {
          setCurrentScreen('profile');
        }}
      />
    );
  }

  return (
    <TopScreen
      account={account}
      loading={loading}
      error={error}
      onSelectRecipient={() => {
        setCurrentScreen('recipients');
      }}
      onBilling={() => {
        setCurrentScreen('billing');
      }}
    />
  );
}

function AppNavigator() {
  return (
    <Routes>
      <Route
        path="/"
        element={<MainAppFlow />}
      />

      <Route
        path="/invoice/:invoiceNumber"
        element={
          <ProcessPayment
            requesterName="山田 太郎"
            billingAmount={3000}
            message="ランチ代をお願いします"
            onPayment={() => {
              console.log(
                '支払いボタンが押されました'
              );
            }}
          />
        }
      />
    </Routes>
  );
}

export default AppNavigator;