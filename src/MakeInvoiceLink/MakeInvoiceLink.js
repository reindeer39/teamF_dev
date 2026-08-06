import { useState } from 'react';
import NavigationButton from '../components/NavigationButton';
import MessageInput from '../components/MessageInput';
import './MakeInvoiceLink.css';

function MakeInvoiceLink({ onCreate = () => {} }) {
  const [amount, setAmount] = useState('');
  const [message, setMessage] = useState('');

  const numericAmount = Number(amount);
  const canCreate = Number.isInteger(numericAmount) && numericAmount > 0;

  function handleSubmit(event) {
    event.preventDefault();
    if (!canCreate) return;

    onCreate({
      amount: numericAmount,
      message: message.trim() || null,
    });
  }

  return (
    <form className="make-invoice-link" onSubmit={handleSubmit}>
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

      <MessageInput
        id="invoice-message"
        className="make-invoice-link__message"
        label="メッセージ（任意）"
        placeholder="例：ランチ代をお願いします"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
      />

      <div className="make-invoice-link__submit">
        <NavigationButton onClick={handleSubmit} disabled={!canCreate}>
          リンク作成
        </NavigationButton>
      </div>
    </form>
  );
}

export default MakeInvoiceLink;
