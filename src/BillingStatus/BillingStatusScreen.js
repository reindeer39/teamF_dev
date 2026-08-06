import { useEffect, useState } from 'react';
import { getUserSummary } from '../api/users';
import human1 from '../images/human1.png';
import './BillingStatusScreen.css';

const USER_ICONS = {
  'user1.png': human1,
};

const BILLING_REQUESTS = [
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

function resolveUserIcon(iconPath) {
  if (!iconPath) return '';

  const normalizedPath = iconPath.replaceAll('\\', '/');
  const fileName = normalizedPath.split('/').pop();
  return USER_ICONS[fileName] || normalizedPath;
}

function formatInvoiceTime(invoiceTime) {
  return invoiceTime?.replace('T', ' ').slice(0, 16) || '---- -- -- --:--';
}

function BillingStatusScreen({ onBack }) {
  const [openInvoiceNumber, setOpenInvoiceNumber] = useState(null);
  const [payer, setPayer] = useState(null);
  const [payerLoading, setPayerLoading] = useState(false);
  const [payerError, setPayerError] = useState('');

  useEffect(() => {
    const openInvoice = BILLING_REQUESTS.find(
      (invoice) => invoice.invoice_number === openInvoiceNumber
    );

    setPayer(null);
    setPayerError('');

    if (!openInvoice?.payer_account_number) {
      setPayerLoading(false);
      return undefined;
    }

    let active = true;
    setPayerLoading(true);

    getUserSummary(openInvoice.payer_account_number)
      .then((data) => {
        if (active) setPayer(data);
      })
      .catch((apiError) => {
        if (active) {
          setPayerError(`支払人情報を取得できませんでした: ${apiError.message}`);
        }
      })
      .finally(() => {
        if (active) setPayerLoading(false);
      });

    return () => {
      active = false;
    };
  }, [openInvoiceNumber]);

  const toggleInvoice = (invoice) => {
    const invoiceNumber = invoice.invoice_number;

    if (openInvoiceNumber === invoiceNumber) {
      setOpenInvoiceNumber(null);
      return;
    }

    setOpenInvoiceNumber(invoiceNumber);
  };

  const copyInvoiceLink = async (invoiceNumber) => {
    const invoiceUrl = `${window.location.origin}/invoice/${encodeURIComponent(
      invoiceNumber
    )}`;

    try {
      await navigator.clipboard.writeText(invoiceUrl);
      window.alert('リンクをコピーしました。');
    } catch (error) {
      window.alert(`リンクをコピーできませんでした: ${error.message}`);
    }
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
          {BILLING_REQUESTS.map((invoice) => {
            const invoiceNumber = invoice.invoice_number;
            const isOpen = openInvoiceNumber === invoiceNumber;
            const invoiceInfo = INVOICE_DETAILS[invoiceNumber];
            const detailsId = `invoice-${invoiceNumber}-details`;
            const invoiceTime = formatInvoiceTime(invoice.invoiced_at);
            const isPaid = invoice.payment_flag === 'pay';

            return (
              <article className="billing-item" key={invoiceNumber}>
                <div className="billing-item-summary">
                  <time dateTime={invoice.invoiced_at?.replace(' ', 'T')}>
                    {invoiceTime}
                  </time>
                  <span
                    className={`billing-item-status ${
                      isPaid
                        ? 'billing-item-status--paid'
                        : 'billing-item-status--unpaid'
                    }`}
                  >
                    {isPaid ? '支払済み' : '未払い'}
                  </span>
                  <button
                    className="billing-toggle"
                    type="button"
                    aria-expanded={isOpen}
                    aria-controls={detailsId}
                    aria-label={`${invoiceTime}の請求詳細を${isOpen ? '閉じる' : '開く'}`}
                    onClick={() => toggleInvoice(invoice)}
                  >
                    <span
                      className={`billing-toggle-icon ${
                        isOpen
                          ? 'billing-toggle-icon--up'
                          : 'billing-toggle-icon--down'
                      }`}
                      aria-hidden="true"
                    >
                      &lt;
                    </span>
                  </button>
                </div>

                {isOpen && (
                  <div className="billing-item-details" id={detailsId}>
                    {invoiceInfo ? (
                      <>
                        {isPaid && payerLoading && <p>支払人情報を読み込み中...</p>}
                        {isPaid && payerError && (
                          <p className="billing-list-message--error">{payerError}</p>
                        )}
                        {payer && (
                          <div className="billing-user-row">
                            <span className="billing-payer-label">支払人</span>
                            <img
                              className="billing-face"
                              src={resolveUserIcon(payer.user_icon)}
                              alt={`${payer.user_name}のアイコン`}
                            />
                            <strong>{payer.user_name}</strong>
                          </div>
                        )}

                        <div
                          className={`billing-amount-row ${
                            isPaid
                              ? 'billing-amount-row--paid'
                              : 'billing-amount-row--unpaid'
                          }`}
                        >
                          <p className="billing-amount">
                            請求金額：
                            {Number(invoiceInfo.invoice_amount).toLocaleString('ja-JP')}円
                          </p>

                          {!isPaid && (
                            <button
                              className="billing-copy-link-button"
                              type="button"
                              onClick={() => copyInvoiceLink(invoiceNumber)}
                            >
                              リンクをコピー
                            </button>
                          )}
                        </div>

                        <label className="billing-message-label">
                          メッセージ
                          <textarea value={invoiceInfo.message || ''} readOnly />
                        </label>
                      </>
                    ) : (
                      <p className="billing-list-message--error">
                        請求詳細の仮データが見つかりません。
                      </p>
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

export default BillingStatusScreen;
