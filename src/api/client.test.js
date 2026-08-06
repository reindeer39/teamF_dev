import {
  clearStoredToken,
  getStoredToken,
  request,
  storeToken,
} from './client';

beforeEach(() => {
  window.localStorage.clear();
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('保存済みトークンをAPIのAuthorizationヘッダーへ付与する', async () => {
  storeToken('test-token');
  fetch.mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ account_number: '1000001' }),
  });

  await request('/account/summary');

  expect(fetch).toHaveBeenCalledWith(
    'http://127.0.0.1:8000/api/account/summary',
    expect.objectContaining({
      headers: expect.objectContaining({ Authorization: 'Token test-token' }),
    })
  );
});

test('ログアウト時に利用するトークン削除処理', () => {
  storeToken('test-token');
  expect(getStoredToken()).toBe('test-token');

  clearStoredToken();

  expect(getStoredToken()).toBeNull();
});

test('フィールド別APIエラーをメッセージとdataへ保持する', async () => {
  global.fetch.mockResolvedValue({
    ok: false,
    status: 400,
    json: async () => ({
      account_number: ['この口座番号は既に使用されています。'],
    }),
  });

  await expect(request('/auth/signup/')).rejects.toMatchObject({
    message: 'この口座番号は既に使用されています。',
    data: {
      account_number: ['この口座番号は既に使用されています。'],
    },
  });
});
