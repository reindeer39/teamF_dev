import { useEffect, useState } from 'react';
import MessageInput from '../components/MessageInput';
import { getUserSummary } from '../api/accounts';
import { getInvoiceInfo, getMyInvoices } from '../api/invoices';
import { resolveUserIcon } from '../userIcons';
import './InvoiceStatusScreen.css';

const INVOICE_REQUESTS = [
  {
    invoiced_at: '2026-08-05 12:30:00.000000',
    payment_flag: 'pay',
    payer_account_number: '1000001',
    invoice_number: 'invoice-001',
  },
  {
    invoiced_at: '2026-07-20 09:15:00.000000',
    payment_flag: 'notpay',
    payer_account_number: null,
    invoice_number: 'invoice-002',
  },
];

const INVOICE_DETAILS = {
  'invoice-001': {
    message: '8月分の請求です。',
    invoice_amount: 100000,
  },
  'invoice-002': {
    message: 'hogehogehogehogehoeegehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehoge',
    invoice_amount: 100000,
  },
};

function formatInvoiceTime(invoiceTime) {
  return invoiceTime?.replace('T', ' ').slice(0, 16) || '---- -- -- --:--';
}

function InvoiceStatusScreen({ account, accountNumber, onSwitchAccount }) {
  const [invoices, setInvoices] = useState([]);
  const [openInvoiceNumber, setOpenInvoiceNumber] = useState(null);
  const [details, setDetails] = useState({});
  const [detailLoading, setDetailLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshCount, setRefreshCount] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    getMyInvoices(accountNumber)
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
  }, [accountNumber, refreshCount]);

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

  // API連携ポイント: 一覧APIは金額・メッセージ・支払人情報を含まないため、
  // 「開く」操作をした請求だけ詳細API(get_inf・summary)を追加で取得する。
  async function openInvoiceDetails(invoice) {
    if (openInvoiceNumber === invoice.invoice_number) {
      setOpenInvoiceNumber(null);
      return;
    }
    setOpenInvoiceNumber(invoice.invoice_number);
    if (details[invoice.invoice_number]) return;

    setDetailLoading(true);
    try {
      const [info, payer] = await Promise.all([
        getInvoiceInfo(invoice.invoice_number),
        invoice.paid_by ? getUserSummary(invoice.paid_by) : Promise.resolve(null),
      ]);
      setDetails((current) => ({
        ...current,
        [invoice.invoice_number]: {
          amount: Number(info.invoice_amount),
          message: info.invoice_message,
          payer,
        },
      }));
    } catch (apiError) {
      setError(`請求詳細を取得できませんでした: ${apiError.message}`);
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <main className="invoice-status-screen">
      <section className="invoice-status-panel">
        {/* <div className="invoice-status-owner">
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
        </div> */}

        {loading && <p>読み込み中...</p>}
        {error && <p className="invoice-list-message--error">{error}</p>}
        {!loading && !error && invoices.length === 0 && <p>請求はありません。</p>}

        <div className="invoice-list">
          {invoices.map((invoice) => {
            const isOpen = openInvoiceNumber === invoice.invoice_number;
            const isPaid = invoice.invoice_flag === 'paid';
            const invoiceTime = formatInvoiceTime(invoice.invoice_time);
            const detailsId = `invoice-${invoice.invoice_number}-details`;
            const detail = details[invoice.invoice_number];
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
                    onClick={() => openInvoiceDetails(invoice)}
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
                    {!detail && detailLoading && <p>読み込み中...</p>}
                    {detail && (
                      <>
                        {detail.payer && (
                          <div className="invoice-user-row">
                            <span className="invoice-payer-label">支払人</span>
                            <img
                              className="invoice-face"
                              src={resolveUserIcon(detail.payer.user_icon)}
                              alt={`${detail.payer.user_name}のアイコン`}
                            />
                            <strong>{detail.payer.user_name}</strong>
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
                            請求金額：{detail.amount.toLocaleString('ja-JP')}円
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
                        <MessageInput
                          id={`invoice-message-${invoice.invoice_number}`}
                          className="invoice-message-input"
                          label="メッセージ"
                          value={detail.message || ''}
                          readOnly
                        />
                      </>
                    )}
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
