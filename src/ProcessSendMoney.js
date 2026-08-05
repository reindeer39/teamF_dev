import { useState } from 'react';
import recipientIcon from './icon/human2.png';
import './ProcessSendMoney.css';
import NavigationButton from './components/NavigationButton';

function ProcessSendMoney() {
  const recipientName = 'サンプル 氏名';
  const accountBalance = 80000;

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

          <p className="recipient-name">
            {recipientName}
          </p>
        </div>
      </section>

      <section className="limit-section">
        <p className="section-label">送金上限額</p>

        <p className="limit-amount">
          {accountBalance.toLocaleString('ja-JP')}円
        </p>
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
            max={accountBalance}
            inputMode="numeric"
            placeholder="金額"
          />

          <span className="yen-label">円</span>
        </div>
      </section>

      <NavigationButton
        className="send-button"
        width="100%"
        backgroundColor="#b8b8b8"
        hoverColor="#b8b8b8"
        textColor="#ffffff"
      >
        送金
      </NavigationButton>
    </main>
  );
}

export default ProcessSendMoney;
