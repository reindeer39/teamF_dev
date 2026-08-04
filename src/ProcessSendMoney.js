import recipientIcon from './icon/human2.png';
import './ProcessSendMoney.css';

function ProcessSendMoney() {
  return (
    <main className="send-money-screen">
      <section className="recipient-section">
        <p className="section-label">送金先</p>

        <div className="recipient-info">
          <img
            className="recipient-icon"
            src={recipientIcon}
            alt="送金先のユーザー"
          />
          <p className="recipient-name">サンプル 氏名</p>
        </div>
      </section>

      <section className="limit-section">
        <p className="section-label">送金上限額</p>
        <p className="limit-amount">50,000円</p>
      </section>

      <section className="amount-section">
        <label className="section-label" htmlFor="send-amount">
          送金金額
        </label>

        <div className="amount-input-wrapper">
          <input
            id="send-amount"
            className="amount-input"
            type="number"
            min="0"
            inputMode="numeric"
            placeholder="金額"
          />
          <span className="yen-label">円</span>
        </div>
      </section>

      <button className="send-button" disabled>
        送金
      </button>
    </main>
  );
}

export default ProcessSendMoney;
