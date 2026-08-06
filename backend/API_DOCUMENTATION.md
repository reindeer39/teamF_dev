# 送金・請求システム API 仕様書

BASE URL: `http://localhost:8000` (`http://127.0.0.1:8000`)

ReactからURL設定、View、ORM、SQLiteへ処理が進む仕組みは[BACKEND_FLOW_GUIDE.md](BACKEND_FLOW_GUIDE.md)を参照してください。

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
| Step 9 | 請求リスト一覧を取得する (新しい順) | `GET /api/user/{account_number}/invoice_list` |

---

## 1. ユーザ口座情報取得 (Step 1)
* **Method**: `GET`
* **Endpoint**: `/api/user/{account_number}/summary`
* **Request Content-Type**: なし
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
* **Request Content-Type**: なし
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
* **Request Content-Type**: なし
* **Response**: `200 OK` (application/json)
  ```json
  {
    "sender_account_number": "123456",
    "recipient_icon": "/static/images/user2.png",
    "recipient_name": "佐藤花子"
  }
  ```

---

## 4. 送金処理 (Step 5・6)
* **Method**: `POST`
* **Endpoint**: `/api/user/{sender_account_number}/{recipient_account_number}/transfer`
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
* **Request Content-Type**: `application/json`
  ```json
  {
    "invoice_amount": 10000,
    "message": "飲み会代割り勘"
  }
  ```
  * 請求元口座番号はURLパス `{account_number}` から自動取得されます。
* **Response 200 OK**: `application/json`
  ```json
  {
    "invoice_link": "http://localhost:3000/invoice/33333333-3333-4333-8333-333333333333"
  }
  ```
* **Response 400 Bad Request**:
  ```json
  {
    "error": "Not enough parameters"
  }
  ```

---

## 6. 請求情報の取得 (Step 8-1)
* **Method**: `GET`
* **Endpoint**: `/api/{invoice_number}/get_inf`
* **Request Content-Type**: なし
* **Response 200 OK**: `application/json`
  ```json
  {
    "invoice_account_number": "123456",
    "invoice_amount": "10000",
    "invoice_message": "飲み会代割り勘"
  }
  ```

---

## 7. 請求の支払い用API (Step 8-2)
* **Method**: `POST`
* **Endpoint**: `/api/{invoice_number}/pay`
* **Request Content-Type**: `application/json`
  ```json
  {
    "my_account_number": "654321",
    "invoice_account_number": "123456",
    "invoice_amount": "10000",
    "message": "支払いました"
  }
  ```
* **Response 200 OK**: なし（空レスポンス）
* **Response 400 Bad Request**:
  ```json
  {
    "error": "Not enough parameters"
  }
  ```
* **Response 500 Server Error**:
  ```json
  {
    "error": "Server error"
  }
  ```
* **トランザクション制御と紐付け（橋渡し）**:
  1. 支払元の残高減算 ＆ 請求元の残高加算
  2. 送金DB (`transactions`) に自動で取引レコードが生成され、一意な `transaction_number`（UUID）と送信日時（`created_at`）が発行される。
  3. 請求DB (`invoice`) の `invoice_flag` を `paid` に更新。**`transaction_number` に送金DBの取引番号をそのまま記録**し、`paid_time` に送金DBの作成日時（`created_at` のフォーマット文字列）をセットして完全に統一・同期します。

---

## 8. 請求リストの取得 (Step 9)
* **Method**: `GET`
* **Endpoint**: `/api/user/{account_number}/invoice_list`
* **Request Content-Type**: なし
* **Response 200 OK**: `application/json`
  ```json
  {
    "invoice_list": [
      {
        "invoice_time": "2026-08-06 10:53",
        "invoice_flag": "notpay",
        "paid_by": null,
        "invoice_number": "33333333-3333-4333-8333-333333333333"
      },
      {
        "invoice_time": "2026-08-05 18:30",
        "invoice_flag": "paid",
        "paid_by": "654321",
        "invoice_number": "11111111-1111-4111-8111-111111111111"
      }
    ]
  }
  ```
  * `invoice_time`: 請求作成日時を `YYYY-MM-DD HH:MM` 形式（分まで）に加工。
  * リスト内の並び順: 請求作成日時 (`created_time`) が**新しいものが先頭になる降順（`order_by("-created_time")`）**。
  * `paid_by`: 未払いの場合は `null`。
* **Response 404 Not Found**:
  ```json
  {
    "error": "not found account"
  }
  ```

---

## データベーススキーマ一覧

### 1. 口座テーブル (モデル: `Account`, テーブル名: `accounts`)
| カラム名 | 意味 | 型 |
|---|---|---|
| `account_number` | 口座番号 (PK) | str |
| `user_icon` | ユーザアイコン | str (path) |
| `user_name` | ユーザ名 | str |
| `account_balance` | 預金残高 | int |

### 2. 送金履歴テーブル (モデル: `Transaction`, テーブル名: `transactions`)
| カラム名 | 意味 | 型 |
|---|---|---|
| `transaction_number` | 取引番号 (PK/UUID自動生成) | str / UUID |
| `sender` | 送信元口座 (FK) | str |
| `recipient` | 送信先口座 (FK) | str |
| `transfer_amount` | 金額 | int |
| `message` | メッセージ | str |
| `created_at` | 送金作成日時 (自動生成) | datetime |

### 3. 請求テーブル (モデル: `Invoice`, テーブル名: `invoice`)
| カラム名 | 意味 | 型 |
|---|---|---|
| `invoice_number` | 請求取引番号 (キー/PK) | str / UUID |
| `invoice_amount` | 請求金額 | int |
| `message` | メッセージ | str |
| `account_number` | 請求元口座番号 (FK) | str |
| `created_time` | 請求作成日時 (形式: `YYYY-MM-DD HH:MM:SS.ffffff`) | str |
| `invoice_flag` | フラグ (`notpay` / `paid`) | str |
| `paid_time` | 支払日時 (送金DBの `created_at` と完全一致) | str |
| `paid_by` | 支払った口座 (FK) | str |
| `transaction_number` | 支払時に作成された取引番号 (FK - 送金DBの `transaction_number` と完全一致) | str |
