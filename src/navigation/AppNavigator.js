import { useEffect, useState } from 'react';
import { useMatch, useNavigate } from 'react-router-dom';
import TopScreen from '../TopScreen/TopScreen';
import SelectSendMoney from '../SelectSendMoney/SelectSendMoney';
import ProcessSendMoney from '../ProcessSendMoney/ProcessSendMoney';
import AuthScreen from '../auth/AuthScreen';
import { useAuth } from '../auth/AuthContext';
import { getUserSummary } from '../api/accounts';
import ProcessPayment from '../ProcessPayment/ProcessPayment';
import MakeInvoiceLink from '../MakeInvoiceLink/MakeInvoiceLink';
import CopyInvoiceLink from '../CopyInvoiceLink/CopyInvoiceLink';
import InvoiceStatusScreen from '../InvoiceStatus/InvoiceStatusScreen';
import { createInvoice } from '../api/invoices';

function AppNavigator() {
  const { session, initializing, login, signup, signOut } = useAuth();
  const navigate = useNavigate();
  const [currentScreen, setCurrentScreen] = useState('profile');
  const [account, setAccount] = useState(session?.account || null);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadCount, setReloadCount] = useState(0);
  const [invoiceLink, setInvoiceLink] = useState('');

  const invoiceMatch = useMatch('/invoice/:invoiceNumber');
  const myAccountNumber = session?.account?.account_number;

  useEffect(() => {
    if (!myAccountNumber) {
      setAccount(null);
      return undefined;
    }

    let active = true;
    setLoading(true);
    setError('');

    // API連携ポイント: 画面表示時と送金完了後に最新残高をDBから再取得する。
    getUserSummary(myAccountNumber)
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
  }, [reloadCount, myAccountNumber]);

  if (initializing) {
    return <p className="screen-message">ログイン状態を確認しています...</p>;
  }

  if (!session) {
    return <AuthScreen onLogin={login} onSignup={signup} />;
  }

  if (invoiceMatch) {
    return (
      <ProcessPayment
        invoiceNumber={invoiceMatch.params.invoiceNumber}
        myAccountNumber={myAccountNumber}
        onSwitchAccount={signOut}
      />
    );
  }

  if (currentScreen === 'recipients') {
    return (
      <SelectSendMoney
        accountNumber={myAccountNumber}
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
        senderAccountNumber={myAccountNumber}
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

  if (currentScreen === 'invoice') {
    return (
      <MakeInvoiceLink
        onBack={() => setCurrentScreen('profile')}
        onCreate={async ({ amount, message }) => {
          const result = await createInvoice(myAccountNumber, amount, message || '');
          setInvoiceLink(result.invoice_link);
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
        onOpenAsAnotherAccount={async () => {
          const invoicePath = new URL(invoiceLink, window.location.origin).pathname;
          setCurrentScreen('profile');
          await signOut();
          navigate(invoicePath);
        }}
      />
    );
  }

  if (currentScreen === 'invoiceStatus') {
    return (
      <InvoiceStatusScreen
        account={account}
        accountNumber={myAccountNumber}
        onBack={() => setCurrentScreen('profile')}
        onSwitchAccount={signOut}
      />
    );
  }

  return (
    <TopScreen
      account={account}
      loading={loading}
      error={error}
      onSelectRecipient={() => setCurrentScreen('recipients')}
      onInvoice={() => setCurrentScreen('invoice')}
      onInvoiceStatus={() => setCurrentScreen('invoiceStatus')}
      onLogout={signOut}
    />
  );
}

export default AppNavigator;
