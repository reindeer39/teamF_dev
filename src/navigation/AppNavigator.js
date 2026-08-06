import { useEffect, useState } from 'react';
import { useRoutes } from 'react-router';
import TopScreen from '../TopScreen/TopScreen';
import SelectSendMoney from '../SelectSendMoney/SelectSendMoney';
import ProcessSendMoney from '../ProcessSendMoney/ProcessSendMoney';
import ProcessPayment from '../ProcessSendMoney/ProcessSendMoney';
import MakeInvoiceLink from '../MakeInvoiceLink/MakeInvoiceLink';
import CopyInvoiceLink from '../CopyInvoiceLink/CopyInvoiceLink';
import { ACCOUNT_NUMBER } from '../account';
import { getUserSummary } from '../api/users';

function AppNavigator() {
  const [currentScreen, setCurrentScreen] = useState('profile');
  const [account, setAccount] = useState(null);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadCount, setReloadCount] = useState(0);
  const [invoiceLink, setInvoiceLink] = useState('');

  const invoiceScreen = useRoutes([
    {
      path: '/invoice/:invoiceNumber',
      element: <ProcessPayment requesterName="山田 太郎" billingAmount={3000} message="ランチ代をお願いします" />,
    },
  ]);

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

  if (invoiceScreen) {
    return invoiceScreen;
  }

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
    return (
      <MakeInvoiceLink
        onBack={() => setCurrentScreen('profile')}
        onCreate={({ amount, message }) => {
          const query = new URLSearchParams({ amount: String(amount) });
          if (message) query.set('message', message);
          setInvoiceLink(`${window.location.origin}/invoice?${query.toString()}`);
          setCurrentScreen('copyInvoiceLink');
        }}
      />
    );
  }

  if (currentScreen === 'copyInvoiceLink') {
    return (
      <CopyInvoiceLink
        invoiceLink={invoiceLink}
        onBack={() => setCurrentScreen('profile')}
      />
    );
  }

  return (
    <TopScreen
      account={account}
      loading={loading}
      error={error}
      onSelectRecipient={() => setCurrentScreen('recipients')}
      onBilling={() => setCurrentScreen('billing')}
    />
  );
}

export default AppNavigator;
