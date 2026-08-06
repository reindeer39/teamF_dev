# React画面・Django API・SQLite連携ガイド

この資料は、利用者が画面を操作してから、Django APIとSQLiteを経由し、結果がReact画面へ表示されるまでを実際のコードに沿って説明します。

APIの正確な入出力は[API_DOCUMENTATION.md](API_DOCUMENTATION.md)、テーブル定義は[DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)を参照してください。

## 1. 最初に全体像

ReactはSQLiteを直接操作しません。必ずDjango APIを経由します。

```text
利用者の操作
  ↓
React画面コンポーネント
  ↓ 機能別API関数を呼ぶ
src/api/auth.js・accounts.js・transfers.js
  ↓ 共通request()を呼ぶ
src/api/client.js
  ↓ HTTP + JSON + Authorizationヘッダー
Django config/urls.py
  ↓ /api/以降を委譲
backend/api/urls.py
  ↓ URLに対応するView
backend/api/views.py
  ↓ Django ORM
backend/api/models.py
  ↓ SQLへ変換
backend/db.sqlite3
  ↓ JSONレスポンス
Reactのstateを更新
  ↓
画面を再描画
```

重要な責務の分け方は次のとおりです。

| 層 | 主なファイル | 責務 |
|---|---|---|
| 画面 | `src/auth/`, `src/TopScreen/`など | 入力、読み込み中・成功・エラーの表示 |
| 認証状態 | `src/auth/AuthContext.js` | トークン、ログイン状態、ログアウト |
| API関数 | `src/api/auth.js`など | エンドポイントと送信JSONを定義 |
| 共通通信 | `src/api/client.js` | `fetch`、共通ヘッダー、JSON変換、エラー化 |
| URLルーティング | `backend/api/urls.py` | URLをDjango Viewへ結び付ける |
| API処理 | `backend/api/views.py` | 入力検証、認証確認、ORM、レスポンス |
| DB定義 | `backend/api/models.py` | Account、Transaction、Invoiceと制約 |

## 2. React起動時に最初に起きること

入口は`src/index.js`です。

```jsx
<AuthProvider>
  <AppNavigator />
</AuthProvider>
```

`AuthProvider`が外側にあるため、内側の`AppNavigator`や各画面は`useAuth()`でログイン状態を利用できます。

### 保存済みトークンがない場合

`src/auth/AuthContext.js`の起動処理がlocalStorageを確認します。

```js
if (!getStoredToken()) {
  setInitializing(false);
  return undefined;
}
```

トークンがなければ`session`は`null`のままです。`AppNavigator.js`は次の分岐でログイン画面を表示します。

```jsx
if (!session) {
  return <AuthScreen onLogin={login} onSignup={signup} />;
}
```

### 保存済みトークンがある場合

`AuthContext.js`が`getCurrentUser()`を呼びます。

```js
getCurrentUser()
  .then((data) => setSession(data))
  .catch(() => clearStoredToken());
```

これは`src/api/auth.js`の次の関数です。

```js
export function getCurrentUser() {
  return request('/auth/me');
}
```

トークンが有効ならDjangoがUserとAccountを返し、`session`へ保存されてTopScreenへ進みます。無効ならトークンを削除してログイン画面へ戻ります。

## 3. 共通APIクライアント

すべてのReact API関数は`src/api/client.js`の`request()`を通ります。

```js
export async function request(path, options = {}) {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Token ${token}` } : {}),
      ...options.headers,
    },
  });
}
```

ここで共通処理をまとめています。

- APIのベースURLを付ける
- JSONのContent-Typeを付ける
- ログイン済みなら`Authorization: Token ...`を付ける
- レスポンスJSONをJavaScriptオブジェクトへ変換する
- 400や401などをJavaScriptの`Error`へ変換する

そのため各画面で直接`fetch()`を書く必要はありません。

## 4. ログインからTopScreen表示まで

### 4.1 入力とボタン

`src/auth/AuthScreen.js`は入力値をReact stateで持ちます。

```js
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
```

ログインフォーム送信時に、親から受け取った`onLogin`を呼びます。

```js
await onLogin({ email, password });
```

この`onLogin`の実体は`AuthContext.js`の`login`です。

### 4.2 API関数

`src/api/auth.js`が送信先とHTTPメソッドを定義します。

```js
export function login(credentials) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
}
```

ブラウザから送られる内容は次の形です。

```http
POST http://127.0.0.1:8000/api/auth/login
Content-Type: application/json

{"email":"yamada@example.com","password":"..."}
```

### 4.3 Django URLルーティング

`backend/config/urls.py`が`/api/`を`api.urls`へ渡します。

```python
path("api/", include("api.urls"))
```

`backend/api/urls.py`が残りの`auth/login`をViewへ結び付けます。

```python
path("auth/login", LoginView.as_view(), name="login")
```

POSTなので`LoginView.post()`が実行されます。

### 4.4 Djangoで認証

`backend/api/views.py`の`LoginView`はメールアドレスからUserを探し、Djangoの`authenticate()`でハッシュ化済みパスワードを照合します。

```python
user_by_email = User.objects.filter(email__iexact=email).first()
user = authenticate(
    request=request,
    username=authentication_name,
    password=password,
)
```

成功するとUserに紐づくAccountとトークンを返します。

```python
token, _ = Token.objects.get_or_create(user=user)
return Response({
    "token": token.key,
    "email": user.email,
    "account": account_data(account),
})
```

メール不存在、パスワード不一致、Account未紐付けは、アカウントの存在を推測されないよう同じエラーになります。

### 4.5 Reactでログイン状態を保存

レスポンスは`AuthContext.js`へ戻ります。

```js
const data = await requestFunction(values);
storeToken(data.token);
setSession({ email: data.email, account: data.account });
```

`session`が`null`ではなくなるため、`AppNavigator`が再描画されます。ログイン画面の分岐を通らなくなり、最後の`TopScreen`が返されます。

```jsx
return (
  <TopScreen
    account={account}
    loading={loading}
    error={error}
    onLogout={signOut}
  />
);
```

## 5. TopScreenの口座情報が表示されるまで

ログイン直後のレスポンスにもAccountは含まれますが、最新残高を取得するため`AppNavigator.js`は`getMySummary()`を呼び直します。

```js
getMySummary()
  .then((data) => setAccount(data))
  .catch((apiError) => setError(apiError.message))
  .finally(() => setLoading(false));
```

`src/api/accounts.js`では次のAPIに対応します。

```js
export function getMySummary() {
  return request('/account/summary');
}
```

`request()`が保存済みトークンを付けるため、Reactから口座番号を送る必要はありません。

Django側は`MyAccountSummaryView`で、認証Userに紐づくAccountを取得します。

```python
account = authenticated_account(request)
return Response(account_data(account))
```

レスポンス例です。

```json
{
  "account_number": "1000001",
  "user_icon": "/icons/user1.png",
  "user_name": "山田太郎",
  "account_balance": 97000
}
```

`setAccount(data)`でstateが変わると、`TopScreen.js`が再描画されます。

```js
const userName = account?.user_name || '読み込み中';
const accountBalance = account
  ? `${account.account_balance.toLocaleString('ja-JP')}円`
  : '---円';
```

そしてJSXの次の部分へ表示されます。

```jsx
<span className="user-profile__name">{userName}</span>
<strong className="user-profile__balance-value">{accountBalance}</strong>
```

つまり、JSONの`user_name`と`account_balance`が、React stateを経由して画面の文字になります。

## 6. 送金先一覧が表示されるまで

TopScreenの「送金する」を押すと、`AppNavigator`が画面状態を変更します。

```jsx
onSelectRecipient={() => setCurrentScreen('recipients')}
```

`currentScreen === 'recipients'`になると`SelectSendMoney`が表示されます。

`SelectSendMoney.js`は初回表示時の`useEffect`でAPIを呼びます。

```js
getRecipientList()
  .then((data) => setUsers(data.recipient_list));
```

対応するAPI関数です。

```js
export function getRecipientList() {
  return request('/account/recipients');
}
```

Djangoの`AuthenticatedRecipientListView`はログイン口座を除外します。

```python
users = Account.objects.exclude(pk=account.pk)
```

Reactへ戻った配列は`map()`で1件ずつボタンになります。

```jsx
{users.map((user) => (
  <li key={user.account_number}>
    <strong>{user.user_name}</strong>
    <span>口座番号：{user.account_number}</span>
  </li>
))}
```

## 7. 送金処理画面が表示されるまで

送金先を押すと、選択したAccount情報を`AppNavigator`へ渡します。

```js
setSelectedRecipient(recipient);
setCurrentScreen('transfer');
```

`ProcessSendMoney`には送金先口座番号だけをpropsで渡します。

```jsx
<ProcessSendMoney
  recipientAccountNumber={selectedRecipient.account_number}
/>
```

画面表示時に`getRecipientInfo()`を呼びます。

```js
getRecipientInfo(recipientAccountNumber)
  .then((data) => setRecipient(data));
```

API URLは次のように組み立てられます。

```js
request(`/account/recipients/${encodeURIComponent(recipientAccountNumber)}`)
```

Djangoの`AuthenticatedRecipientInfoView`が、ログイン中の送金元残高と送金先情報を返します。このJSONが`recipient` stateに入り、送金先名と送金上限額として表示されます。

## 8. 送金ボタンからDB更新、完了画面まで

### 8.1 ReactからPOST

`ProcessSendMoney.js`の`handleSubmit()`が呼ばれます。

```js
const transferResult = await createTransfer(
  recipientAccountNumber,
  numericAmount,
  message
);
setResult(transferResult);
```

`src/api/transfers.js`が送信JSONを作ります。

```js
return request(`/transfers/${encodeURIComponent(recipientAccountNumber)}`, {
  method: 'POST',
  body: JSON.stringify({
    transfer_amount: transferAmount,
    message,
  }),
});
```

送金元口座番号は送信しません。Djangoがトークンから確定するため、別口座になりすますことを防げます。

### 8.2 DjangoでDB更新

URLは`AuthenticatedTransferView`へ到達します。

```python
path(
    "transfers/<str:recipient_account_number>",
    AuthenticatedTransferView.as_view(),
)
```

Viewは認証UserのAccountを送金元として`TransferView`の共通処理へ渡します。

```python
sender = authenticated_account(request)
return super().post(
    request,
    sender.account_number,
    recipient_account_number,
)
```

`TransferView`は次の処理を`transaction.atomic()`内で実行します。

```python
with transaction.atomic():
    sender = Account.objects.select_for_update().get(...)
    recipient = Account.objects.select_for_update().get(...)

    sender.account_balance -= transfer_amount
    recipient.account_balance += transfer_amount
    sender.save(update_fields=["account_balance"])
    recipient.save(update_fields=["account_balance"])

    transfer = Transaction.objects.create(
        sender=sender,
        recipient=recipient,
        transfer_amount=transfer_amount,
        message=message,
    )
```

途中で失敗した場合は、両口座の残高更新とTransaction作成がすべてロールバックされます。

### 8.3 完了画面

Djangoは取引番号などをJSONで返します。Reactは`setResult()`で保存します。

```jsx
if (result) {
  return (
    <main className="transfer-complete">
      <h1>送金が完了しました</h1>
      <p>{result.transfer_amount.toLocaleString('ja-JP')}円を送金しました。</p>
      <p>取引番号：{result.transaction_number}</p>
    </main>
  );
}
```

`result`が設定されたこと自体が、入力画面から完了画面へ切り替わる条件です。

## 9. エラーが画面へ表示されるまで

Djangoが400などを返すと、`client.js`が`Error`を作ってthrowします。

```js
if (!response.ok) {
  const error = new Error(errorMessage(data || {}, response.status));
  error.status = response.status;
  throw error;
}
```

画面側の`catch`がメッセージをstateへ保存します。

```js
catch (apiError) {
  setError(`送金できませんでした: ${apiError.message}`);
}
```

stateに文字列が入ると、次の条件付きJSXが表示されます。

```jsx
{error && <p className="screen-message screen-message--error">{error}</p>}
```

ログイン失敗も同じ流れです。Djangoはセキュリティ上、メール不存在とパスワード不一致を区別せず、同じメッセージを返します。

## 10. 新規登録とログアウト

### 新規登録

`AuthScreen`は次を呼びます。

```js
onSignup({ email, password, user_name: userName })
```

`SignupView`は`transaction.atomic()`内でDjango UserとAccountを同時作成します。

```python
with transaction.atomic():
    user = User.objects.create_user(...)
    account = Account.objects.create(
        account_number=generate_account_number(),
        user=user,
        user_name=user_name,
        account_balance=0,
    )
    token = Token.objects.create(user=user)
```

レスポンス形式はログインと同じなので、そのまま`AuthContext.authenticate()`がトークンとsessionを保存し、TopScreenへ進みます。

### ログアウト

TopScreenのログアウトボタンは`signOut`を呼びます。

```js
await logoutRequest();
clearStoredToken();
setSession(null);
```

Djangoはサーバー側のTokenを削除し、ReactはlocalStorageとsessionを削除します。`session === null`になり、`AppNavigator`がログイン画面を表示します。

## 11. 請求APIの現在位置

Djangoには次の請求APIとSQLite連携があります。

| 操作 | API | DB処理 |
|---|---|---|
| 請求作成 | `POST /api/user/{account}/invoice_request` | Invoiceを作成 |
| 請求取得 | `GET /api/{invoice_number}/get_inf` | Invoiceを1件取得 |
| 請求支払い | `POST /api/{invoice_number}/pay` | 残高、Transaction、Invoiceを一括更新 |
| 請求一覧 | `GET /api/user/{account}/invoice_list` | 作成日時降順でInvoiceを取得 |

これらは`backend/api/views.py`の`InvoiceRequestView`、`InvoiceInfoView`、`InvoicePayView`、`InvoiceListView`です。

ただし、現在のReactで「請求する」を押した先は`NextScreen`であり、請求APIを呼ぶ`src/api/invoices.js`や`/invoice/{invoice_number}`画面はまだありません。つまり、請求はバックエンドAPIとDBまでは完成していますが、React画面との接続は今後の実装対象です。

## 12. APIと画面の対応表

| 画面・タイミング | React API関数 | Django View | 主なモデル |
|---|---|---|---|
| 新規登録 | `signup()` | `SignupView` | User, Account, Token |
| ログイン | `login()` | `LoginView` | User, Account, Token |
| 起動時の認証復元 | `getCurrentUser()` | `CurrentUserView` | User, Account |
| TopScreen | `getMySummary()` | `MyAccountSummaryView` | Account |
| 送金先一覧 | `getRecipientList()` | `AuthenticatedRecipientListView` | Account |
| 送金処理画面 | `getRecipientInfo()` | `AuthenticatedRecipientInfoView` | Account |
| 送金ボタン | `createTransfer()` | `AuthenticatedTransferView` | Account, Transaction |
| ログアウト | `logout()` | `LogoutView` | Token |

## 13. 画面とAPIを実際に確認する方法

### サーバー起動

ターミナル1：

```bash
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py seed_mock_data
python manage.py runserver
```

ターミナル2：

```bash
npm start
```

ブラウザで`http://localhost:3000`を開きます。

### ブラウザの開発者ツール

Chromeの場合はDevToolsのNetworkタブを開き、Fetch/XHRで絞り込みます。

1. ログインボタンを押す
2. `auth/login`を選ぶ
3. Payloadで送信JSONを見る
4. ResponseでDjangoから返ったJSONを見る
5. Headersで`Authorization`の有無を見る

TopScreen表示時は`account/summary`、送金先画面では`account/recipients`、送金時は`transfers/{口座番号}`が確認できます。

### Django側ログ

`runserver`を実行したターミナルには次のように出ます。

```text
"POST /api/auth/login HTTP/1.1" 200
"GET /api/account/summary HTTP/1.1" 200
```

### SQLiteの確認

```bash
cd backend
python manage.py shell
```

```python
from api.models import Account, Transaction, Invoice

Account.objects.values("account_number", "user_name", "account_balance")
Transaction.objects.values("transaction_number", "sender_id", "recipient_id", "transfer_amount")
Invoice.objects.values("invoice_number", "invoice_flag", "created_time")
```

## 14. APIを追加するときの実装順序

1. `backend/api/models.py`: 保存項目や関連が既存モデルで足りるか確認
2. `backend/api/urls.py`: URLとViewを接続
3. `backend/api/views.py`: 入力検証、認証、ORM、Responseを実装
4. `backend/api/tests.py`: 正常系、入力不正、認証不正、DBロールバックをテスト
5. `src/api/`: 機能単位のAPI関数を追加
6. React画面: `loading`、成功データ、`error`をstateで管理
7. `API_DOCUMENTATION.md`: URLとJSONを更新
8. このガイドの画面フローを更新

画面コンポーネントに直接`fetch()`を増やさず、必ず`src/api/client.js`と機能別APIファイルを使うと、認証ヘッダーとエラー処理を一か所に保てます。

## 15. よくある調査ポイント

| 症状 | 最初に見る場所 |
|---|---|
| ボタンを押してもAPIが呼ばれない | 画面の`onClick` / `onSubmit`とDevTools Network |
| URLが404 | `src/api/*.js`と`backend/api/urls.py`の文字列 |
| 401になる | localStorageの`teamf.authToken`とAuthorizationヘッダー |
| APIは200だが表示されない | `.then()`後の`setState`とJSXの参照キー |
| 400の理由が分からない | NetworkのResponseと`views.py`の入力検証 |
| DBが変わらない | 対応ViewのORM処理と`transaction.atomic()` |
| Reactだけ古い値 | state更新、`reloadCount`、再取得APIの実行有無 |

自動テストは次で実行できます。

```bash
cd backend
python manage.py test api

cd ..
CI=true npm test -- --watchAll=false
```
