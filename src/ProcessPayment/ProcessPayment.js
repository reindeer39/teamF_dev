import { useEffect, useState } from 'react';
import {
  useNavigate,
  useParams,
} from 'react-router';

import NavigationButton from '../components/NavigationButton';
import { PAYMENT_ACCOUNT_NUMBER } from '../account';
import { getUserSummary } from '../api/users';
import { resolveUserIcon } from '../userIcons';
import './ProcessPayment.css';

function formatYen(value) {
  const numericValue = Number(value);

  return Number.isFinite(numericValue)
    ? `${numericValue.toLocaleString('ja-JP')}円`
    : '---円';
}

function ProcessPayment({
  requesterName = '請求元ユーザー',
  requesterIcon = '',
  billingAmount = 0,
  message = '',
  onPayment,
  onBack,
}) {
  // URLの /invoice/:invoiceNumber から請求番号を取得する
  const { invoiceNumber } = useParams();

  // URLによる画面遷移に使用する
  const navigate = useNavigate();

  // 支払者の口座情報
  const [payerAccount, setPayerAccount] = useState(null);

  // 口座情報を読み込み中か
  const [loading, setLoading] = useState(true);

  // 支払い処理中か
  const [submitting, setSubmitting] = useState(false);

  // API通信などで発生したエラー
  const [error, setError] = useState('');

  // 支払い成功後の結果
  const [result, setResult] = useState(null);

  useEffect(() => {
    let active = true;

    // URLから請求番号を取得できなかった場合
    if (!invoiceNumber) {
      setError('請求番号を取得できませんでした。');
      setLoading(false);

      return () => {
        active = false;
      };
    }

    setLoading(true);
    setError('');

    // Step 8の支払者の口座情報を取得する
    getUserSummary(PAYMENT_ACCOUNT_NUMBER)
      .then((data) => {
        if (active) {
          setPayerAccount(data);
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

    // APIの返事が来る前に画面を離れた場合の安全対策
    return () => {
      active = false;
    };
  }, [invoiceNumber]);

  // API取得前は0円、取得後は支払者の実際の残高を使用する
  const payerBalance = payerAccount?.account_balance ?? 0;

  // 残高と請求金額を数字へ変換する
  const numericBalance = Number(payerBalance);
  const numericBillingAmount = Number(billingAmount);

  // 支払いボタンを押せる条件
  const canPay =
    !loading &&
    !submitting &&
    !error &&
    Number.isFinite(numericBalance) &&
    Number.isInteger(numericBillingAmount) &&
    numericBillingAmount > 0 &&
    numericBillingAmount <= numericBalance;

  // 支払いボタンを押したときの処理
  const handlePayment = async () => {
    if (!canPay) return;

    setSubmitting(true);
    setError('');

    try {
      // 現在は仮処理。
      // 支払いAPI完成後は、invoiceNumberを使って
      // ここから支払いAPIを呼び出す。
      const paymentResult = onPayment
        ? await onPayment(invoiceNumber)
        : null;

      // 支払いAPIがまだないため、
      // 仮の支払い結果を作って完了画面を表示する。
      setResult({
        ...(paymentResult || {}),
        payment_amount:
          paymentResult?.payment_amount ??
          paymentResult?.invoice_amount ??
          numericBillingAmount,
      });
    } catch (paymentError) {
      setError(
        `支払いできませんでした: ${paymentError.message}`
      );
    } finally {
      setSubmitting(false);
    }
  };

  // トップ画面へ戻る
  const handleReturnTop = () => {
    navigate('/');
  };

  // 支払い完了画面
  if (result) {
    return (
      <main className="payment-screen payment-complete">
        <h1 className="payment-complete__title">
          支払いが完了しました
        </h1>

        <section className="payment-complete__summary">
          <p className="payment-complete__amount-label">
            支払い金額
          </p>

          <strong className="payment-complete__amount">
            {formatYen(result.payment_amount)}
          </strong>
        </section>

        <p className="payment-complete__recipient">
          {requesterName}さんへ支払いました。
        </p>

        {result.transaction_number && (
          <p className="payment-complete__transaction">
            取引番号：{result.transaction_number}
          </p>
        )}

        <NavigationButton
          width="100%"
          height="54px"
          backgroundColor="#e76f75"
          hoverColor="#d75d64"
          onClick={handleReturnTop}
        >
          トップへ戻る
        </NavigationButton>
      </main>
    );
  }

  // 支払い前の通常画面
  return (
    <main className="payment-screen">
      {onBack && (
        <button
          type="button"
          className="text-button payment-screen__back"
          onClick={onBack}
        >
          戻る
        </button>
      )}

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
            src={resolveUserIcon(requesterIcon)}
            alt={`${requesterName}のアイコン`}
          />

          <strong className="payment-screen__name">
            {requesterName}
          </strong>
        </div>
      </section>

      <section className="payment-screen__section payment-screen__detail">
        <div className="payment-screen__row">
          <p className="payment-screen__label">
            口座残高
          </p>

          <p className="payment-screen__value">
            {loading
              ? '読み込み中...'
              : formatYen(payerBalance)}
          </p>
        </div>

        <div className="payment-screen__row">
          <p className="payment-screen__label">
            請求金額
          </p>

          <p className="payment-screen__value payment-screen__amount">
            {formatYen(billingAmount)}
          </p>
        </div>

        <div className="payment-screen__message-block">
          <p className="payment-screen__label">
            メッセージ
          </p>

          <p className="payment-screen__message">
            {message || 'メッセージはありません'}
          </p>
        </div>
      </section>

      {error && (
        <p
          className="payment-screen__warning"
          role="alert"
        >
          {error}
        </p>
      )}

      {!loading &&
        !submitting &&
        !error &&
        !canPay &&
        numericBillingAmount > 0 && (
          <p
            className="payment-screen__warning"
            role="alert"
          >
            口座残高が不足しているため支払いできません。
          </p>
        )}

      <NavigationButton
        width="100%"
        height="54px"
        backgroundColor="#e76f75"
        hoverColor="#d75d64"
        disabled={!canPay}
        onClick={handlePayment}
      >
        {loading
          ? '読み込み中...'
          : submitting
            ? '支払い中...'
            : '支払う'}
      </NavigationButton>

      <button
        type="button"
        className="text-button payment-screen__top-link"
        onClick={handleReturnTop}
      >
        トップ画面へ戻る
      </button>
    </main>
  );
}

export default ProcessPayment;
