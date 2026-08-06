import { useState } from 'react';
import NavigationButton from '../components/NavigationButton';
import './CopyInvoiceLink.css';

function CopyInvoiceLink({
  invoiceLink = '',
  onBack = () => {},
}) {
  const [copyMessage, setCopyMessage] = useState('');

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(invoiceLink);
      setCopyMessage('コピーしました');
    } catch {
      setCopyMessage('コピーできませんでした');
    }
  }

  return (
    <main className="copy-invoice-link">
      <div className="copy-invoice-link__display">
        <p>リンクの表示</p>
        <p className="copy-invoice-link__url">{invoiceLink}</p>
      </div>

      <div className="copy-invoice-link__copy-area">
        <button type="button" onClick={handleCopy} disabled={!invoiceLink}>
          リンクをコピー
        </button>
        <p aria-live="polite">{copyMessage}</p>
      </div>

      <div className="copy-invoice-link__top-button">
        <NavigationButton onClick={onBack}>トップに戻る</NavigationButton>
      </div>
    </main>
  );
}

export default CopyInvoiceLink;
