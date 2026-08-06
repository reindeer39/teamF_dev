import { useEffect, useState } from 'react';
import recipientIcon from '../images/human2.png';
import { createTransfer, getRecipientInfo } from '../api/users';
import './ProcessSendMoney.css';
import NavigationButton from '../components/NavigationButton';
import MessageInput from '../components/MessageInput';

function ProcessSendMoney({
  senderAccountNumber,
  recipientAccountNumber,
  accountBalance,
  onTransferSuccess,
  onTransferComplete,
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
        <h1>送金が完了しました</h1>
        <p>{result.transfer_amount.toLocaleString('ja-JP')}円を送金しました。</p>
        <p>取引番号：{result.transaction_number}</p>
        <button type="button" className="send-button" onClick={onTransferComplete}>
          トップへ戻る
        </button>
      </main>
    );
  }

  return (
    <form className="send-money-screen" onSubmit={handleSubmit}>
      <section className="recipient-section">
        <p className="section-label">送金先</p>
        <div className="recipient-info">
          <img className="recipient-icon" src={recipientIcon} alt="送金先のユーザー" />
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
        <label className="section-label" htmlFor="send-amount">送金金額</label>
        <div className="amount-input-wrapper">
          <input
            id="send-amount"
            className="amount-input"
            type="number"
            min="1"
            step="1"
            inputMode="numeric"
            placeholder="金額"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
          />
          <span className="yen-label">円</span>
        </div>
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
        backgroundColor="#e76f75"
        hoverColor="#d75d64"
        disabled={!canSubmit}
        onClick={handleSubmit}
      >
        {submitting ? '送金中...' : '送金'}
      </NavigationButton>
    </form>
  );
}

export default ProcessSendMoney;
