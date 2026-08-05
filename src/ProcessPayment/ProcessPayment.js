import requesterDefaultIcon from '../images/human2.png';
import NavigationButton from '../components/NavigationButton';
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
  accountBalance = 0,
  billingAmount = 0,
  message = '',
  onPayment,
  onBack,
  onReturnTop,
}) {
  const numericBalance = Number(accountBalance);
  const numericBillingAmount = Number(billingAmount);
  const canPay =
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
        <button type="button" className="text-button payment-screen__back" onClick={onBack}>
          戻る
        </button>
      )}

      <section className="payment-screen__section" aria-labelledby="requester-label">
        <p id="requester-label" className="payment-screen__label">請求元</p>
        <div className="payment-screen__requester">
          <img
            className="payment-screen__icon"
            src={requesterIcon}
            alt={`${requesterName}のアイコン`}
          />
          <strong className="payment-screen__name">{requesterName}</strong>
        </div>
      </section>

      <section className="payment-screen__section payment-screen__detail">
        <div className="payment-screen__row">
          <p className="payment-screen__label">口座残高</p>
          <p className="payment-screen__value">{formatYen(accountBalance)}</p>
        </div>

        <div className="payment-screen__row">
          <p className="payment-screen__label">請求金額</p>
          <p className="payment-screen__value payment-screen__amount">
            {formatYen(billingAmount)}
          </p>
        </div>

        <div className="payment-screen__message-block">
          <p className="payment-screen__label">メッセージ</p>
          <p className="payment-screen__message">{message || 'メッセージはありません'}</p>
        </div>
      </section>

      {!canPay && numericBillingAmount > 0 && (
        <p className="payment-screen__warning" role="alert">
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
        支払う
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
