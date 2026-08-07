import { useState } from 'react';
import './CopyInvoiceLink.css';

function CopyInvoiceLink({
  invoiceLink = '',
}) {
  const [copyMessage, setCopyMessage] = useState('');
  const [copyStatus, setCopyStatus] = useState('');

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(invoiceLink);
      setCopyMessage('コピーしました');
      setCopyStatus('success');
    } catch {
      setCopyMessage('コピーできませんでした');
      setCopyStatus('error');
    }
  }

  return (
    <main className="copy-invoice-link">
      <section className="copy-invoice-link__card">
        <span className="copy-invoice-link__icon" aria-hidden="true">✓</span>
        <h2>請求リンクを作成しました</h2>
        <p className="copy-invoice-link__guide">
          以下のリンクを支払う方へ共有してください。
        </p>
        <output className="copy-invoice-link__url">{invoiceLink}</output>
        <button type="button" onClick={handleCopy} disabled={!invoiceLink}>
          リンクをコピー
        </button>
        <p
          className={`copy-invoice-link__status copy-invoice-link__status--${copyStatus}`}
          aria-live="polite"
        >
          {copyMessage}
        </p>
      </section>
    </main>
  );
}

export default CopyInvoiceLink;
