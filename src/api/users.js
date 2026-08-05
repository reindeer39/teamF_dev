const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000/api';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `API request failed (${response.status})`);
  }
  return data;
}

// API連携ポイント: トップ画面の口座情報をDjangoのAccountテーブルから取得する。
export function getUserSummary(accountNumber) {
  return request(`/user/${encodeURIComponent(accountNumber)}/summary`);
}

// API連携ポイント: 送金先一覧をDjangoのAccountテーブルから取得する。
export function getRecipientList(accountNumber) {
  return request(`/user/${encodeURIComponent(accountNumber)}/recipient_list`);
}

// API連携ポイント: 選択した送金先と送金可能残高をDjangoから取得する。
export function getRecipientInfo(senderAccountNumber, recipientAccountNumber) {
  return request(
    `/user/${encodeURIComponent(senderAccountNumber)}/${encodeURIComponent(recipientAccountNumber)}/recipient`
  );
}

// API連携ポイント: 送金ボタンから金額とメッセージをPOSTし、
// Django側で口座残高の更新とTransaction履歴の作成を同時に行う。
export function createTransfer(
  senderAccountNumber,
  recipientAccountNumber,
  transferAmount,
  message
) {
  return request(
    `/user/${encodeURIComponent(senderAccountNumber)}/${encodeURIComponent(recipientAccountNumber)}/transfer`,
    {
      method: 'POST',
      body: JSON.stringify({
        transfer_amount: transferAmount,
        message,
      }),
    }
  );
}
