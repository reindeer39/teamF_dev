import { useEffect, useState } from 'react';
import requesterDefaultIcon from '../images/human2.png';
import NavigationButton from '../components/NavigationButton';
import { PAYMENT_ACCOUNT_NUMBER } from '../account';
import { getUserSummary } from '../api/users';
import './ProcessPayment.css';

function formatYen(value) {
  const numericValue = Number(value);

  return Number.isFinite(numericValue)
    ? `${numericValue.toLocaleString('ja-JP')}円`
    : '---円';
}

function ProcessPayment({
  requesterName = '請求元ユーザー',
  requesterIcon = requesterDefaultIcon,
  billingAmount = 0,
  message = '',
  onPayment,
  onBack,
  onReturnTop,
}) {
  // 支払者の口座情報を保存する
  const [payerAccount, setPayerAccount] = useState(null);

  // 口座情報を読み込み中かどうか
  const [loading, setLoading] = useState(true);

  // API通信で発生したエラー
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

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
  }, []);

  // API取得前は0円、取得後は支払者の実際の残高を使用する
  const payerBalance = payerAccount?.account_balance ?? 0;

  // 比較に使うため数字へ変換する
  const numericBalance = Number(payerBalance);
  const numericBillingAmount = Number(billingAmount);

  // 支払いボタンを押せる条件
  const canPay =
    !loading &&
    !error &&
    Number.isFinite(numericBalance) &&
    Number.isInteger(numericBillingAmount) &&
    numericBillingAmount > 0 &&
    numericBillingAmount <= numericBalance;

  const handlePayment = () => {
    if (canPay && onPayment) {
      onPayment();
    }
  };

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
            src={requesterIcon}
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
        {loading ? '読み込み中...' : '支払う'}
      </NavigationButton>

      {onReturnTop && (
        <button
          type="button"
          className="text-button payment-screen__top-link"
          onClick={onReturnTop}
        >
          トップ画面へ戻る
        </button>
      )}
    </main>
  );
}

export default ProcessPayment;