import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { getUserSummary } from '../api/accounts';
import { getInvoiceInfo, payInvoice } from '../api/invoices';
import NavigationButton from '../components/NavigationButton';
import MessageInput from '../components/MessageInput';
import { resolveUserIcon } from '../userIcons';
import './ProcessPayment.css';


function formatYen(value) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue)
    ? `${numericValue.toLocaleString('ja-JP')}円`
    : '---円';
}

function ProcessPayment({ invoiceNumber, myAccountNumber, onSwitchAccount }) {
  const navigate = useNavigate();
  const [invoiceInfo, setInvoiceInfo] = useState(null);
  const [issuer, setIssuer] = useState(null);
  const [payerAccount, setPayerAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [switchingAccount, setSwitchingAccount] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');

    // API連携ポイント: Miroの設計通り、請求情報・請求元プロフィール・
    // 自分の口座情報を別々のAPIから取得する。
    async function load() {
      try {
        const [info, payer] = await Promise.all([
          getInvoiceInfo(invoiceNumber),
          getUserSummary(myAccountNumber),
        ]);
        const issuerData = await getUserSummary(info.invoice_account_number);
        if (!active) return;
        setInvoiceInfo(info);
        setPayerAccount(payer);
        setIssuer(issuerData);
      } catch (apiError) {
        if (active) setError(`請求情報を取得できませんでした: ${apiError.message}`);
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [invoiceNumber, myAccountNumber]);

  const invoiceAmount = Number(invoiceInfo?.invoice_amount);
  const isPaid = invoiceInfo?.invoice_flag === 'paid';
  const isOwnInvoice = Boolean(
    invoiceInfo && payerAccount && invoiceInfo.invoice_account_number === payerAccount.account_number
  );
  const hasEnoughBalance = Boolean(
    invoiceInfo && payerAccount && payerAccount.account_balance >= invoiceAmount
  );
  const canPay = !loading && !submitting && !error && !isPaid && !isOwnInvoice && hasEnoughBalance;

  async function handlePayment() {
    if (!canPay) return;
    setSubmitting(true);
    setError('');
    try {
      const paymentResult = await payInvoice(invoiceNumber, {
        my_account_number: myAccountNumber,
        invoice_account_number: invoiceInfo.invoice_account_number,
        invoice_amount: invoiceAmount,
        message: invoiceInfo.invoice_message,
      });
      setResult(paymentResult);
    } catch (apiError) {
      setError(`支払いできませんでした: ${apiError.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSwitchAccount() {
    if (!onSwitchAccount || switchingAccount) return;
    setSwitchingAccount(true);
    setError('');
    try {
      await onSwitchAccount();
    } catch (switchError) {
      setError(`ログアウトできませんでした: ${switchError.message}`);
      setSwitchingAccount(false);
    }
  }

  if (result) {
    return (
      <main className="payment-screen payment-complete">
        <h1 className="payment-complete__title">支払いが完了しました</h1>
        <section className="payment-complete__summary">
          <p className="payment-complete__amount-label">支払い金額</p>
          <strong className="payment-complete__amount">
            {formatYen(result.payment_amount)}
          </strong>
        </section>
        <p className="payment-complete__recipient">
          {issuer.user_name}さんへ支払いました。
        </p>
        {result.transaction_number && (
          <p className="payment-complete__transaction">
            取引番号：{result.transaction_number}
          </p>
        )}

        <NavigationButton
          width="100%"
          height="54px"
          onClick={() => navigate('/')}
        >
          トップへ戻る
        </NavigationButton>
      </main>
    );
  }

  return (
    <main className="payment-screen">
      <section
        className="payment-screen__section"
        aria-labelledby="requester-label"
      >
        <p
          id="requester-label"
          className="payment-screen__label"
        >
          請求元
        </p>
        <div className="payment-screen__requester">
          <img
            className="payment-screen__icon"
            src={resolveUserIcon(issuer?.user_icon)}
            alt={issuer ? `${issuer.user_name}のアイコン` : ''}
          />
          <strong className="payment-screen__name">
            {loading ? '読み込み中...' : issuer?.user_name || '---'}
          </strong>
        </div>
      </section>

      <section className="payment-screen__section payment-screen__detail">
        <div className="payment-screen__row">
          <p className="payment-screen__label">口座残高</p>
          <p className="payment-screen__value">
            {loading ? '読み込み中...' : formatYen(payerAccount?.account_balance)}
          </p>
        </div>
        <div className="payment-screen__row">
          <p className="payment-screen__label">請求金額</p>
          <p className="payment-screen__value payment-screen__amount">
            {formatYen(invoiceAmount)}
          </p>
        </div>
        <MessageInput
          id="payment-message"
          className="payment-screen__message-block"
          label="メッセージ"
          value={invoiceInfo?.invoice_message || 'メッセージはありません'}
          readOnly
        />
      </section>

      {error && <p className="payment-screen__warning" role="alert">{error}</p>}
      {!loading && isPaid && (
        <p className="payment-screen__warning" role="alert">この請求は支払済みです。</p>
      )}
      {!loading && isOwnInvoice && (
        <p className="payment-screen__warning" role="alert">
          自分が発行した請求は支払えません。支払者のアカウントへ切り替えてください。
        </p>
      )}
      {!loading && invoiceInfo && !isPaid && !isOwnInvoice && !hasEnoughBalance && (
        <p className="payment-screen__warning" role="alert">
          口座残高が不足しているため支払いできません。
        </p>
      )}

      <NavigationButton
        width="100%"
        height="54px"
        disabled={!canPay}
        onClick={handlePayment}
      >
        {loading ? '読み込み中...' : submitting ? '支払い中...' : '支払う'}
      </NavigationButton>
      {onSwitchAccount && (
        <button
          type="button"
          className="text-button payment-screen__top-link"
          onClick={handleSwitchAccount}
          disabled={switchingAccount}
        >
          {switchingAccount ? 'ログアウト中...' : '別のアカウントでログイン'}
        </button>
      )}
      <button
        type="button"
        className="text-button payment-screen__top-link"
        onClick={() => navigate('/')}
      >
        トップ画面へ戻る
      </button>
    </main>
  );
}

export default ProcessPayment;
