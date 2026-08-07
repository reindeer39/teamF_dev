import { useEffect, useState } from 'react';
import { useMatch, useNavigate } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
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
  const [isTransferComplete, setIsTransferComplete] = useState(false);
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
    return (
      <AppLayout title="読み込み中">
        <p className="screen-message">ログイン状態を確認しています...</p>
      </AppLayout>
    );
  }

  if (!session) {
    return (
      <AppLayout title="アカウント">
        <AuthScreen onLogin={login} onSignup={signup} />
      </AppLayout>
    );
  }

  if (invoiceMatch) {
    return (
      <AppLayout title="支払い" onBack={() => navigate('/')} onLogout={signOut}>
        <ProcessPayment
          invoiceNumber={invoiceMatch.params.invoiceNumber}
          myAccountNumber={myAccountNumber}
          onPaymentComplete={(paymentResult) => {
            if (Number.isFinite(paymentResult?.payer_account_balance)) {
              setAccount((currentAccount) => (
                currentAccount
                  ? {
                      ...currentAccount,
                      account_balance: paymentResult.payer_account_balance,
                    }
                  : currentAccount
              ));
            }
            setCurrentScreen('profile');
            navigate('/');
            setReloadCount((count) => count + 1);
          }}
        />
      </AppLayout>
    );
  }

  if (currentScreen === 'recipients') {
    return (
      <AppLayout title="送金先一覧" onBack={() => setCurrentScreen('profile')} onLogout={signOut}>
      <SelectSendMoney
        accountNumber={myAccountNumber}
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
        title={isTransferComplete ? '送金完了' : '送金画面'}
        onLogout={signOut}
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
        senderAccountNumber={myAccountNumber}
        recipientAccountNumber={selectedRecipient.account_number}
        accountBalance={account?.account_balance || 0}
        onTransferSuccess={() => setIsTransferComplete(true)}
      />
      </AppLayout>
    );
  }

  if (currentScreen === 'invoice') {
    return (
      <AppLayout title="請求" onBack={() => setCurrentScreen('profile')} onLogout={signOut}>
      <MakeInvoiceLink
        onCreate={async ({ amount, message }) => {
          const result = await createInvoice(myAccountNumber, amount, message || '');
          setInvoiceLink(result.invoice_link);
          setCurrentScreen('copyInvoiceLink');
        }}
      />
      </AppLayout>
    );
  }

  if (currentScreen === 'copyInvoiceLink') {
    return (
      <AppLayout title="請求リンク" onBack={() => setCurrentScreen('profile')} onLogout={signOut}>
      <CopyInvoiceLink
        invoiceLink={invoiceLink}
      />
      </AppLayout>
    );
  }

  if (currentScreen === 'invoiceStatus') {
    return (
      <AppLayout title="請求リスト" onBack={() => setCurrentScreen('profile')} onLogout={signOut}>
      <InvoiceStatusScreen
        account={account}
        accountNumber={myAccountNumber}
        onSwitchAccount={signOut}
      />
      </AppLayout>
    );
  }

  return (
    <AppLayout title="トップ" onLogout={signOut}>
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
