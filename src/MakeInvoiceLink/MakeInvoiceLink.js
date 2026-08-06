import { useState } from 'react';
import NavigationButton from '../components/NavigationButton';
import './MakeInvoiceLink.css';

function MakeInvoiceLink({ onBack = () => {}, onCreate = () => {} }) {
  const [amount, setAmount] = useState('');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const numericAmount = Number(amount);
  const canCreate = Number.isInteger(numericAmount) && numericAmount > 0;

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canCreate || submitting) return;

    setSubmitting(true);
    setError('');
    try {
      await onCreate({
        amount: numericAmount,
        message: message.trim(),
      });
    } catch (apiError) {
      setError(`請求リンクを作成できませんでした: ${apiError.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="make-invoice-link" onSubmit={handleSubmit}>
      <button
        type="button"
        className="make-invoice-link__back"
        onClick={onBack}
      >
        戻る
      </button>

      <label className="make-invoice-link__amount" htmlFor="invoice-amount">
        <span>請求金額</span>
        <div className="make-invoice-link__amount-box">
          <input
            id="invoice-amount"
            aria-label="請求金額"
            type="number"
            min="1"
            step="1"
            inputMode="numeric"
            placeholder="1,000"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
          <span>円</span>
        </div>
      </label>

      <label className="make-invoice-link__message" htmlFor="invoice-message">
        <span>メッセージ入力</span>
        <textarea
          id="invoice-message"
          aria-label="メッセージ（任意）"
          placeholder="ランチ代をお願いします"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />
      </label>

      <div className="make-invoice-link__submit">
        {error && <p className="screen-message screen-message--error">{error}</p>}
        <NavigationButton onClick={handleSubmit} disabled={!canCreate || submitting}>
          {submitting ? '作成中...' : 'リンク作成'}
        </NavigationButton>
      </div>
    </form>
  );
}

export default MakeInvoiceLink;
