import { useState } from 'react';
import './BillingStatusScreen.css';

const BILLING_REQUESTS = [
  {
    id: 'request-1',
    date: '2026年8月5日',
    status: '支払済み',
    userName: '山田 太郎',
    amount: 100000,
    message: '8月分の請求です。',
  },
  {
    id: 'request-2',
    date: '2026年7月20日',
    status: '支払済み',
    userName: '佐藤 花子',
    amount: 100000,
    message: '昼食代の請求です。',
  },
];

function BillingStatusScreen({ onBack }) {
  const [openRequestId, setOpenRequestId] = useState('request-2');

  const toggleRequest = (requestId) => {
    setOpenRequestId((currentId) =>
      currentId === requestId ? null : requestId
    );
  };

  return (
    <main className="billing-status-screen">
      <section className="billing-status-panel">
        <header className="billing-status-header">
          <button
            className="billing-back-button"
            type="button"
            aria-label="前の画面に戻る"
            onClick={onBack}
          >
            &lt;
          </button>
          <h1 className="billing-status-title">請求リスト</h1>
        </header>

        <div className="billing-list">
          {BILLING_REQUESTS.map((request) => {
            const isOpen = openRequestId === request.id;
            const detailsId = `${request.id}-details`;

            return (
              <article className="billing-item" key={request.id}>
                <div className="billing-item-summary">
                  <time>{request.date}</time>
                  <span className="billing-item-status">{request.status}</span>
                  <button
                    className="billing-toggle"
                    type="button"
                    aria-expanded={isOpen}
                    aria-controls={detailsId}
                    aria-label={`${request.date}の請求詳細を${isOpen ? '閉じる' : '開く'}`}
                    onClick={() => toggleRequest(request.id)}
                  >
                    {isOpen ? '△' : '▽'}
                  </button>
                </div>

                {isOpen && (
                  <div className="billing-item-details" id={detailsId}>
                    <div className="billing-user-row">
                      <div className="billing-face" aria-hidden="true">顔</div>
                      <strong>{request.userName}</strong>
                    </div>

                    <p className="billing-amount">
                      請求金額：{request.amount.toLocaleString('ja-JP')}円
                    </p>

                    <label className="billing-message-label">
                      メッセージ
                      <textarea value={request.message} readOnly />
                    </label>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}

export default BillingStatusScreen;
