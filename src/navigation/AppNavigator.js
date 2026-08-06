import { useEffect, useState } from 'react';
import { useNavigate, useRoutes } from 'react-router';
import AppLayout from '../components/AppLayout';
import TopScreen from '../TopScreen/TopScreen';
import SelectSendMoney from '../SelectSendMoney/SelectSendMoney';
import ProcessSendMoney from '../ProcessSendMoney/ProcessSendMoney';
import ProcessPayment from '../ProcessSendMoney/ProcessSendMoney';
import MakeInvoiceLink from '../MakeInvoiceLink/MakeInvoiceLink';
import CopyInvoiceLink from '../CopyInvoiceLink/CopyInvoiceLink';
import InvoiceStatusScreen from '../InvoiceStatus/InvoiceStatusScreen';
import { ACCOUNT_NUMBER } from '../account';
import { getUserSummary } from '../api/users';

function AppNavigator() {
  const navigate = useNavigate();
  const [currentScreen, setCurrentScreen] = useState('profile');
  const [account, setAccount] = useState(null);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [isTransferComplete, setIsTransferComplete] = useState(false);
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
    return (
      <AppLayout title="支払い" onBack={() => navigate('/')}>
        {invoiceScreen}
      </AppLayout>
    );
  }

  if (currentScreen === 'recipients') {
    return (
      <AppLayout title="送金先一覧" onBack={() => setCurrentScreen('profile')}>
      <SelectSendMoney
        senderAccountNumber={ACCOUNT_NUMBER}
        onSelectRecipient={(recipient) => {
          setSelectedRecipient(recipient);
          setIsTransferComplete(false);
          setCurrentScreen('transfer');
        }}
      />
      </AppLayout>
    );
  }

  if (currentScreen === 'transfer' && selectedRecipient) {
    return (
      <AppLayout
        title={isTransferComplete ? '送金完了' : '送金'}
        onBack={() => {
          if (isTransferComplete) {
            setSelectedRecipient(null);
            setIsTransferComplete(false);
            setCurrentScreen('profile');
            setReloadCount((count) => count + 1);
            return;
          }

          setCurrentScreen('recipients');
        }}
      >
      <ProcessSendMoney
        senderAccountNumber={ACCOUNT_NUMBER}
        recipientAccountNumber={selectedRecipient.account_number}
        accountBalance={account?.account_balance || 0}
        onTransferSuccess={() => setIsTransferComplete(true)}
      />
      </AppLayout>
    );
  }

  if (currentScreen === 'invoice') {
    return (
      <AppLayout title="請求" onBack={() => setCurrentScreen('profile')}>
      <MakeInvoiceLink
        onCreate={({ amount, message }) => {
          const query = new URLSearchParams({ amount: String(amount) });
          if (message) query.set('message', message);
          setInvoiceLink(`${window.location.origin}/invoice?${query.toString()}`);
          setCurrentScreen('copyInvoiceLink');
        }}
      />
      </AppLayout>
    );
  }

  if (currentScreen === 'copyInvoiceLink') {
    return (
      <AppLayout title="請求リンク" onBack={() => setCurrentScreen('profile')}>
      <CopyInvoiceLink
        invoiceLink={invoiceLink}
      />
      </AppLayout>
    );
  }

  if (currentScreen === 'invoiceStatus') {
    return (
      <AppLayout title="請求状態確認" onBack={() => setCurrentScreen('profile')}>
      <InvoiceStatusScreen />
      </AppLayout>
    );
  }

  return (
    <AppLayout title="トップ">
    <TopScreen
      account={account}
      loading={loading}
      error={error}
      onSelectRecipient={() => setCurrentScreen('recipients')}
      onInvoice={() => setCurrentScreen('invoice')}
      onInvoiceStatus={() => setCurrentScreen('invoiceStatus')}
    />
    </AppLayout>
  );
}

export default AppNavigator;
