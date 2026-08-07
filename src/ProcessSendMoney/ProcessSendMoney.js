import { useEffect, useState } from 'react';
import { getRecipientInfo } from '../api/accounts';
import { createTransfer } from '../api/transfers';
import './ProcessSendMoney.css';
import NavigationButton from '../components/NavigationButton';
import MessageInput from '../components/MessageInput';
import AmountInput from '../components/AmountInput';
import { resolveUserIcon } from '../userIcons';

function ProcessSendMoney({
  senderAccountNumber,
  recipientAccountNumber,
  accountBalance,
  onTransferSuccess,
}) {
  const [recipient, setRecipient] = useState(null);
  const [amount, setAmount] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    let active = true;

    // API連携ポイント: 選択した送金先と現在の送金可能残高をDBから取得する。
    getRecipientInfo(senderAccountNumber, recipientAccountNumber)
      .then((data) => {
        if (active) setRecipient(data);
      })
      .catch((apiError) => {
        if (active) setError(`送金情報を取得できませんでした: ${apiError.message}`);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [senderAccountNumber, recipientAccountNumber]);

  const currentBalance = recipient?.sender_account_balance ?? accountBalance;
  const numericAmount = Number(amount);
  const canSubmit =
    Number.isInteger(numericAmount) &&
    numericAmount >= 1 &&
    numericAmount <= Number(currentBalance) &&
    !loading &&
    !submitting;

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError('');
    try {
      // API連携ポイント: 送金ボタンでDjango APIを呼び、SQLiteの両口座残高と
      // Transaction履歴を1回の処理で更新する。
      const transferResult = await createTransfer(
        senderAccountNumber,
        recipientAccountNumber,
        numericAmount,
        message
      );
      setResult(transferResult);
      onTransferSuccess?.();
    } catch (apiError) {
      setError(`送金できませんでした: ${apiError.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    return (
      <main className="send-money-screen transfer-complete">
        <section className="transfer-complete__card">
          <span className="transfer-complete__icon" aria-hidden="true">✓</span>
          <h1>送金が完了しました</h1>
          <p className="transfer-complete__guide">正常に送金処理が完了しました。</p>
          <div className="transfer-complete__summary">
            <span>送金額</span>
            <strong>{result.transfer_amount.toLocaleString('ja-JP')}円</strong>
          </div>
          <p className="transfer-complete__transaction">
            取引番号：{result.transaction_number}
          </p>
        </section>
      </main>
    );
  }

  return (
    <form className="send-money-screen" onSubmit={handleSubmit}>
      <section className="recipient-section">
        <p className="section-label">送金先</p>
        <div className="recipient-info">
          <img
            className="recipient-icon"
            src={resolveUserIcon(recipient?.recipient_icon)}
            alt={`${recipient?.recipient_name || '送金先ユーザー'}のアイコン`}
          />
          <p className="recipient-name">
            {loading ? '読み込み中...' : recipient?.recipient_name}
          </p>
        </div>
      </section>

      <section className="limit-section">
        <p className="section-label">送金上限額</p>
        <p className="limit-amount">{currentBalance.toLocaleString('ja-JP')}円</p>
      </section>

      <section className="amount-section">
        <AmountInput
          id="send-amount"
          label="送金金額"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
        />
      </section>

      <section className="message-section">
        <MessageInput
          id="transfer-message"
          label="メッセージ（任意）"
          maxLength={200}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="例：昼食代"
        />
      </section>

      {error && <p className="screen-message screen-message--error">{error}</p>}
      <NavigationButton
        width="100%"
        height="10vh"
        disabled={!canSubmit}
        onClick={handleSubmit}
      >
        {submitting ? '送金中...' : '送金'}
      </NavigationButton>
    </form>
  );
}

export default ProcessSendMoney;
