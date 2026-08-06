import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { getMySummary } from '../api/accounts';
import { getInvoice, payInvoice } from '../api/invoices';
import requesterDefaultIcon from '../images/human2.png';
import NavigationButton from '../components/NavigationButton';
import './ProcessPayment.css';


function formatYen(value) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue)
    ? `${numericValue.toLocaleString('ja-JP')}円`
    : '---円';
}

function ProcessPayment({ invoiceNumber }) {
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState(null);
  const [payerAccount, setPayerAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');

    Promise.all([getInvoice(invoiceNumber), getMySummary()])
      .then(([invoiceData, accountData]) => {
        if (!active) return;
        setInvoice(invoiceData);
        setPayerAccount(accountData);
      })
      .catch((apiError) => {
        if (active) setError(`請求情報を取得できませんでした: ${apiError.message}`);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [invoiceNumber]);

  const isPaid = invoice?.invoice_flag === 'paid';
  const isOwnInvoice = Boolean(
    invoice && payerAccount && invoice.issuer.account_number === payerAccount.account_number
  );
  const hasEnoughBalance = Boolean(
    invoice && payerAccount && payerAccount.account_balance >= invoice.invoice_amount
  );
  const canPay = !loading && !submitting && !error && !isPaid && !isOwnInvoice && hasEnoughBalance;

  async function handlePayment() {
    if (!canPay) return;
    setSubmitting(true);
    setError('');
    try {
      setResult(await payInvoice(invoiceNumber));
    } catch (apiError) {
      setError(`支払いできませんでした: ${apiError.message}`);
    } finally {
      setSubmitting(false);
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
          {invoice.issuer.user_name}さんへ支払いました。
        </p>
        <p className="payment-complete__transaction">
          取引番号：{result.transaction_number}
        </p>
        <NavigationButton onClick={() => navigate('/')}>
          トップへ戻る
        </NavigationButton>
      </main>
    );
  }

  return (
    <main className="payment-screen">
      <section className="payment-screen__section" aria-labelledby="requester-label">
        <p id="requester-label" className="payment-screen__label">請求元</p>
        <div className="payment-screen__requester">
          <img
            className="payment-screen__icon"
            src={invoice?.issuer.user_icon || requesterDefaultIcon}
            alt={invoice ? `${invoice.issuer.user_name}のアイコン` : ''}
          />
          <strong className="payment-screen__name">
            {loading ? '読み込み中...' : invoice?.issuer.user_name || '---'}
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
            {formatYen(invoice?.invoice_amount)}
          </p>
        </div>
        <div className="payment-screen__message-block">
          <p className="payment-screen__label">メッセージ</p>
          <p className="payment-screen__message">
            {invoice?.message || 'メッセージはありません'}
          </p>
        </div>
      </section>

      {error && <p className="payment-screen__warning" role="alert">{error}</p>}
      {!loading && isPaid && (
        <p className="payment-screen__warning" role="alert">この請求は支払済みです。</p>
      )}
      {!loading && isOwnInvoice && (
        <p className="payment-screen__warning" role="alert">自分が発行した請求は支払えません。</p>
      )}
      {!loading && invoice && !isPaid && !isOwnInvoice && !hasEnoughBalance && (
        <p className="payment-screen__warning" role="alert">
          口座残高が不足しているため支払いできません。
        </p>
      )}

      <NavigationButton disabled={!canPay} onClick={handlePayment}>
        {loading ? '読み込み中...' : submitting ? '支払い中...' : '支払う'}
      </NavigationButton>
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
