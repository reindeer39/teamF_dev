import { useEffect, useState } from 'react';
import { getUserSummary } from '../api/users';
import human1 from '../images/human1.png';
import MessageInput from '../components/MessageInput';
import './InvoiceStatusScreen.css';

const USER_ICONS = {
  'user1.png': human1,
};

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

function resolveUserIcon(iconPath) {
  if (!iconPath) return '';

  const normalizedPath = iconPath.replaceAll('\\', '/');
  const fileName = normalizedPath.split('/').pop();
  return USER_ICONS[fileName] || normalizedPath;
}

function formatInvoiceTime(invoiceTime) {
  return invoiceTime?.replace('T', ' ').slice(0, 16) || '---- -- -- --:--';
}

function InvoiceStatusScreen() {
  const [openInvoiceNumber, setOpenInvoiceNumber] = useState(null);
  const [payer, setPayer] = useState(null);
  const [payerLoading, setPayerLoading] = useState(false);
  const [payerError, setPayerError] = useState('');

  useEffect(() => {
    const openInvoice = INVOICE_REQUESTS.find(
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
    <main className="invoice-status-screen">
      <section className="invoice-status-panel">
        <div className="invoice-list">
          {INVOICE_REQUESTS.map((invoice) => {
            const invoiceNumber = invoice.invoice_number;
            const isOpen = openInvoiceNumber === invoiceNumber;
            const invoiceInfo = INVOICE_DETAILS[invoiceNumber];
            const detailsId = `invoice-${invoiceNumber}-details`;
            const invoiceTime = formatInvoiceTime(invoice.invoiced_at);
            const isPaid = invoice.payment_flag === 'pay';

            return (
              <article className="invoice-item" key={invoiceNumber}>
                <div className="invoice-item-summary">
                  <time dateTime={invoice.invoiced_at?.replace(' ', 'T')}>
                    {invoiceTime}
                  </time>
                  <span
                    className={`invoice-item-status ${
                      isPaid
                        ? 'invoice-item-status--paid'
                        : 'invoice-item-status--unpaid'
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
                    onClick={() => toggleInvoice(invoice)}
                  >
                    <span
                      className={`invoice-toggle-icon ${
                        isOpen
                          ? 'invoice-toggle-icon--up'
                          : 'invoice-toggle-icon--down'
                      }`}
                      aria-hidden="true"
                    >
                      &lt;
                    </span>
                  </button>
                </div>

                {isOpen && (
                  <div className="invoice-item-details" id={detailsId}>
                    {invoiceInfo ? (
                      <>
                        {isPaid && payerLoading && <p>支払人情報を読み込み中...</p>}
                        {isPaid && payerError && (
                          <p className="invoice-list-message--error">{payerError}</p>
                        )}
                        {payer && (
                          <div className="invoice-user-row">
                            <span className="invoice-payer-label">支払人</span>
                            <img
                              className="invoice-face"
                              src={resolveUserIcon(payer.user_icon)}
                              alt={`${payer.user_name}のアイコン`}
                            />
                            <strong>{payer.user_name}</strong>
                          </div>
                        )}

                        <div
                          className={`invoice-amount-row ${
                            isPaid
                              ? 'invoice-amount-row--paid'
                              : 'invoice-amount-row--unpaid'
                          }`}
                        >
                          <p className="invoice-amount">
                            請求金額：
                            {Number(invoiceInfo.invoice_amount).toLocaleString('ja-JP')}円
                          </p>

                          {!isPaid && (
                            <button
                              className="invoice-copy-link-button"
                              type="button"
                              onClick={() => copyInvoiceLink(invoiceNumber)}
                            >
                              リンクをコピー
                            </button>
                          )}
                        </div>

                        <MessageInput
                          id={`invoice-message-${invoiceNumber}`}
                          className="invoice-message-input"
                          label="メッセージ"
                          value={invoiceInfo.message || ''}
                          readOnly
                        />
                      </>
                    ) : (
                      <p className="invoice-list-message--error">
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

export default InvoiceStatusScreen;
