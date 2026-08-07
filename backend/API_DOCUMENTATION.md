# 送金・請求システム API仕様書

BASE URL: `http://localhost:8000` (`http://127.0.0.1:8000`)

ReactからURL設定、View、ORM、SQLiteへ処理が進む仕組みは[BACKEND_FLOW_GUIDE.md](BACKEND_FLOW_GUIDE.md)を参照してください。

---

## 認証

Step 10 (会員登録・ログイン)以外の利用者向けAPIはDRF Token Authenticationを使用します。

```http
Authorization: Token <make_accountまたはloginで取得したtoken>
```

`get_inf`・`pay`（請求リンクを開いた相手が使うAPI）だけは、リンクを受け取った人が誰でも呼べるよう認証不要です。

---

## 公式Stepとの対応

| 公式Step | バックエンドAPIの役割 | エンドポイント |
|---|---|---|
| Step 1 | ユーザ口座情報を取得する | `GET /api/user/{account_number}/summary` |
| Step 2 | APIなし（フロントエンドの画面遷移） | N/A |
| Step 3 | 送金先一覧を取得する | `GET /api/user/{account_number}/recipient_list` |
| Step 4 | 選択した送金先と情報（アイコン・名前等）を取得する | `GET /api/user/{sender_account_number}/{recipient_account_number}/recipient` |
| Step 5・6 | 送金処理を行う（メッセージ添付可） | `POST /api/user/{sender_account_number}/{recipient_account_number}/transfer` |
| Step 7 | 請求リクエストを発行する (URLリンク生成) | `POST /api/user/{account_number}/invoice_request` |
| Step 8-1 | 請求情報を取得する | `GET /api/{invoice_number}/get_inf` |
| Step 8-2 | 請求の支払い処理を行う | `POST /api/{invoice_number}/pay` |
| Step 9 | 請求リストを取得する | `GET /api/user/{account_number}/invoice_list` |
| Step 10 | 会員登録・ログイン | `POST /api/make_account` / `POST /api/login` |

---

## 10. 会員登録

* **Method**: `POST`
* **Endpoint**: `/api/make_account`
* **Request Content-Type**: `application/json`
  ```json
  {
    "account_number": "1234567",
    "user_name": "表示名",
    "mail_address": "new-user@example.com",
    "password": "十分に強いパスワード"
  }
  ```
* **Response**: `201 Created`
  ```json
  {
    "token": "...",
    "mail_address": "new-user@example.com",
    "account": {
      "account_number": "1234567",
      "user_icon": "",
      "user_name": "表示名",
      "account_balance": 0,
      "mail_address": "new-user@example.com"
    }
  }
  ```

仕様上は成功時にレスポンス本文なしとされていますが、トークン認証を機能させるため`token`・`account`を返します。口座番号は利用者が指定する7桁の数字で、既存Accountと重複できません。メールアドレスは小文字へ正規化し、大文字・小文字を無視して重複を拒否します。入力不正時は`account_number`、`user_name`、`mail_address`、`password`ごとのエラー配列を返します。

## 10. ログイン

* **Method**: `POST`
* **Endpoint**: `/api/login`
* **Request Content-Type**: `application/json`
  ```json
  {
    "mail_address": "yamada@example.com",
    "password": "teamf-dev-pass"
  }
  ```
* **Response 200 OK**: 会員登録と同じ形（`token`・`mail_address`・`account`）
* **Response 400 Bad Request**: `{"error": "メールアドレスまたはパスワードが正しくありません。"}`

メールアドレス不存在、パスワード不一致、Account未紐付けのいずれでも、アカウント推測を防ぐため同じエラーメッセージを返します。

### ログイン状態・ログアウト（仕様外の補助API）

- `GET /api/auth/me/`: 保存済みトークンに紐づくAccountを返す（ページ再読み込み時の復元用）
- `POST /api/auth/logout/`: 現在のトークンを削除し`204 No Content`を返す

---

## 1. ユーザ口座情報取得 (Step 1)
* **Method**: `GET`
* **Endpoint**: `/api/user/{account_number}/summary`
* **認証**: ログイン必須。自分以外の口座番号も取得できる（Step 8-1の請求元プロフィール表示などで使うため）
* **Response**: `200 OK` (application/json)
  ```json
  {
    "account_number": "123456",
    "user_icon": "/static/images/user1.png",
    "user_name": "山田太郎",
    "account_balance": 100000
  }
  ```

---

## 2. 送金先一覧の取得 (Step 3)
* **Method**: `GET`
* **Endpoint**: `/api/user/{account_number}/recipient_list`
* **認証**: ログイン必須。URLの口座番号はログイン中の口座と一致している必要がある（`403`）
* **Response**: `200 OK` (application/json)
  ```json
  {
    "recipient_list": [
      {
        "account_number": "654321",
        "user_icon": "/static/images/user2.png",
        "user_name": "佐藤花子"
      }
    ]
  }
  ```

---

## 3. 送金処理画面情報取得 (Step 4)
* **Method**: `GET`
* **Endpoint**: `/api/user/{sender_account_number}/{recipient_account_number}/recipient`
* **認証**: ログイン必須。`sender_account_number`はログイン中の口座と一致している必要がある（`403`）
* **Response**: `200 OK` (application/json)
  ```json
  {
    "sender_account_number": "123456",
    "sender_account_balance": 100000,
    "recipient_account_number": "654321",
    "recipient_icon": "/static/images/user2.png",
    "recipient_name": "佐藤花子"
  }
  ```

---

## 4. 送金処理 (Step 5・6)
* **Method**: `POST`
* **Endpoint**: `/api/user/{sender_account_number}/{recipient_account_number}/transfer`
* **認証**: ログイン必須。`sender_account_number`はログイン中の口座と一致している必要がある（`403`）
* **Request Content-Type**: `application/json`
  ```json
  {
    "transfer_amount": 5000,
    "message": "ランチ代"
  }
  ```
  * `message`: null許容 (optional、Step 6)
* **Response**: `200 OK`
  ```json
  {
    "transaction_number": "33333333-3333-4333-8333-333333333333",
    "sender_account_number": "123456",
    "recipient_account_number": "654321",
    "transfer_amount": 5000,
    "message": "ランチ代",
    "sender_account_balance": 95000
  }
  ```
* **エラー制御**: 送金額は1以上の整数、メッセージは200文字以内、送金元と送金先は別口座である必要があります。残高不足の場合は`400 Bad Request`（`{"error": "Insufficient account balance"}`）を返します。
* **DB処理**: 送金元残高の減算、送金先残高の加算、Transaction作成を`transaction.atomic()`内で実行します。途中で失敗した場合はすべてロールバックします。

---

## 5. 請求のリクエスト (Step 7)
* **Method**: `POST`
* **Endpoint**: `/api/user/{account_number}/invoice_request`
* **認証**: ログイン必須。`account_number`はログイン中の口座と一致している必要がある（`403`）
* **Request Content-Type**: `application/json`
  ```json
  {
    "invoice_amount": 10000,
    "message": "飲み会代割り勘"
  }
  ```
* **Response 200 OK**:
  ```json
  {
    "invoice_link": "http://localhost:3000/invoice/33333333-3333-4333-8333-333333333333"
  }
  ```
* **Response 400 Bad Request**: `{"error": "Not enough parameters"}` など

---

## 6. 請求情報の取得 (Step 8-1)
* **Method**: `GET`
* **Endpoint**: `/api/{invoice_number}/get_inf`
* **認証**: 不要（請求リンクを受け取った誰でも呼べる）
* **Response 200 OK**:
  ```json
  {
    "invoice_account_number": "1000001",
    "invoice_amount": "10000",
    "invoice_message": "飲み会代割り勘",
    "invoice_flag": "notpay"
  }
  ```

支払い画面では、このAPIで請求元の口座番号を取得したあと、その口座番号で[1. ユーザ口座情報取得](#1-ユーザ口座情報取得-step-1)を呼んでアイコン・名前を、自分の口座番号でも同APIを呼んで自分の残高を取得する（3回のAPI呼び出しに分ける設計）。

---

## 7. 請求の支払い (Step 8-2)
* **Method**: `POST`
* **Endpoint**: `/api/{invoice_number}/pay`
* **認証**: 不要（請求リンクを受け取った誰でも呼べる）
* **Request Content-Type**: `application/json`
  ```json
  {
    "my_account_number": "1000002",
    "invoice_account_number": "1000001",
    "invoice_amount": 10000,
    "message": "支払いました"
  }
  ```
* **Response 200 OK**: 仕様上はレスポンス本文なしとされていますが、完了画面表示に必要なため以下を返します。
  ```json
  {
    "transaction_number": "...",
    "payment_amount": 10000,
    "payer_account_balance": 42000
  }
  ```
* **Response 400 Bad Request**: パラメータ不足・金額不一致・請求元不一致・残高不足
* **Response 409 Conflict**: `{"error": "Invoice already paid"}`（支払済み請求）
* URLの`invoice_number`から取得したInvoiceを正として、リクエストの請求元と金額がDBの値に一致するか検証します。残高更新、Transaction作成、Invoiceの`paid`更新と関連付けは、すべて同一トランザクション内で実行します。

---

## 8. 請求リストの取得 (Step 9)
* **Method**: `GET`
* **Endpoint**: `/api/user/{account_number}/invoice_list`
* **認証**: ログイン必須。`account_number`はログイン中の口座と一致している必要がある（`403`）
* **Response 200 OK**:
  ```json
  {
    "invoice_list": [
      {
        "invoice_time": "2026-08-06 02:23:25.573786",
        "invoice_flag": "notpay",
        "paid_by": null,
        "invoice_number": "33333333-3333-4333-8333-333333333333"
      }
    ]
  }
  ```
  * `invoice_time`は`YYYY-MM-DD HH:MM:SS.ffffff`形式で、新しい請求が先頭
  * `paid_by`は支払口座の口座番号（未払いは`null`）。金額・メッセージなどの詳細が必要な場合は、一覧の各`invoice_number`で[6. 請求情報の取得](#6-請求情報の取得-step-8-1)を追加で呼ぶ
* **Response 404 Not Found**: `{"error": "not found account"}`

---

## 主なエラー

| ステータス | 意味 |
|---|---|
| `400 Bad Request` | 入力不正、残高不足、請求内容不一致、ログイン失敗 |
| `401 Unauthorized` | トークンなし、または無効なトークン |
| `403 Forbidden` | 他口座として送金・請求・一覧取得しようとした |
| `404 Not Found` | 口座または請求が存在しない |
| `409 Conflict` | 支払済み請求 |

DB定義は[DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)、起動・開発用ログイン情報は[README](../README.md)を参照してください。
