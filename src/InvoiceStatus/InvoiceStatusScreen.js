import { useEffect, useState } from 'react';
import { getMyInvoices } from '../api/invoices';
import { resolveUserIcon } from '../utils/resolveUserIcon';
import './InvoiceStatusScreen.css';


function formatInvoiceTime(invoiceTime) {
  return invoiceTime?.replace('T', ' ').slice(0, 16) || '---- -- -- --:--';
}

function InvoiceStatusScreen({ account, onBack, onSwitchAccount }) {
  const [invoices, setInvoices] = useState([]);
  const [openInvoiceNumber, setOpenInvoiceNumber] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshCount, setRefreshCount] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    getMyInvoices()
      .then((data) => {
        if (active) setInvoices(data.invoice_list);
      })
      .catch((apiError) => {
        if (active) setError(`請求一覧を取得できませんでした: ${apiError.message}`);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshCount]);

  useEffect(() => {
    const refreshOnFocus = () => setRefreshCount((count) => count + 1);
    window.addEventListener('focus', refreshOnFocus);
    return () => window.removeEventListener('focus', refreshOnFocus);
  }, []);

  async function copyInvoiceLink(invoiceNumber) {
    const invoiceUrl = `${window.location.origin}/invoice/${encodeURIComponent(invoiceNumber)}`;
    try {
      await navigator.clipboard.writeText(invoiceUrl);
      window.alert('リンクをコピーしました。');
    } catch (copyError) {
      window.alert(`リンクをコピーできませんでした: ${copyError.message}`);
    }
  }

  return (
    <main className="invoice-status-screen">
      <section className="invoice-status-panel">
        <header className="invoice-status-header">
          <button
            className="invoice-back-button"
            type="button"
            aria-label="前の画面に戻る"
            onClick={onBack}
          >
            &lt;
          </button>
          <h1 className="invoice-status-title">お願いした請求</h1>
        </header>

        <div className="invoice-status-owner">
          <p>
            請求元：<strong>{account?.user_name || 'ログイン中のアカウント'}</strong>
          </p>
          <p>この画面には、自分が発行した請求だけが表示されます。</p>
          <div className="invoice-status-actions">
            <button
              type="button"
              onClick={() => setRefreshCount((count) => count + 1)}
              disabled={loading}
            >
              {loading ? '更新中...' : '最新の状態に更新'}
            </button>
            {onSwitchAccount && (
              <button type="button" onClick={onSwitchAccount}>
                別の請求元アカウントで確認
              </button>
            )}
          </div>
        </div>

        {loading && <p>読み込み中...</p>}
        {error && <p className="invoice-list-message--error">{error}</p>}
        {!loading && !error && invoices.length === 0 && <p>請求はありません。</p>}

        <div className="invoice-list">
          {invoices.map((invoice) => {
            const isOpen = openInvoiceNumber === invoice.invoice_number;
            const isPaid = invoice.invoice_flag === 'paid';
            const invoiceTime = formatInvoiceTime(invoice.invoice_time);
            const detailsId = `invoice-${invoice.invoice_number}-details`;
            return (
              <article className="invoice-item" key={invoice.invoice_number}>
                <div className="invoice-item-summary">
                  <time dateTime={invoice.invoice_time}>{invoiceTime}</time>
                  <span
                    className={`invoice-item-status ${
                      isPaid ? 'invoice-item-status--paid' : 'invoice-item-status--unpaid'
                    }`}
                  >
                    {isPaid ? '支払済み' : '未払い'}
                  </span>
                  <button
                    className="invoice-toggle"
                    type="button"
                    aria-expanded={isOpen}
                    aria-controls={detailsId}
                    aria-label={`${invoiceTime}の請求詳細を${isOpen ? '閉じる' : '開く'}`}
                    onClick={() => setOpenInvoiceNumber(
                      isOpen ? null : invoice.invoice_number
                    )}
                  >
                    <span
                      className={`invoice-toggle-icon ${
                        isOpen ? 'invoice-toggle-icon--up' : 'invoice-toggle-icon--down'
                      }`}
                      aria-hidden="true"
                    >
                      &lt;
                    </span>
                  </button>
                </div>

                {isOpen && (
                  <div className="invoice-item-details" id={detailsId}>
                    {invoice.paid_by && (
                      <div className="invoice-user-row">
                        <span className="invoice-payer-label">支払人</span>
                        <img
                          className="invoice-face"
                          src={resolveUserIcon(invoice.paid_by.user_icon)}
                          alt={`${invoice.paid_by.user_name}のアイコン`}
                        />
                        <strong>{invoice.paid_by.user_name}</strong>
                      </div>
                    )}
                    {!isPaid && (
                      <p className="invoice-awaiting-payment">支払者からの支払い待ちです。</p>
                    )}
                    <div
                      className={`invoice-amount-row ${
                        isPaid ? 'invoice-amount-row--paid' : 'invoice-amount-row--unpaid'
                      }`}
                    >
                      <p className="invoice-amount">
                        請求金額：{invoice.invoice_amount.toLocaleString('ja-JP')}円
                      </p>
                      {!isPaid && (
                        <button
                          className="invoice-copy-link-button"
                          type="button"
                          onClick={() => copyInvoiceLink(invoice.invoice_number)}
                        >
                          リンクをコピー
                        </button>
                      )}
                    </div>
                    <label className="invoice-message-label">
                      メッセージ
                      <textarea value={invoice.message || ''} readOnly />
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

export default InvoiceStatusScreen;
