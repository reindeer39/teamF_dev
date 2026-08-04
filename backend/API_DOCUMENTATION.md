# 送金システム API 仕様書 (まとめ)

BASE URL: `http://localhost:8000` (`http://127.0.0.1:8000`)

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

## 2. 送金先一覧の取得 (Step 2)
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

## 3. 送信先処理画面取得 (Step 3)
* **Method**: `GET`
* **Endpoint**: `/api/user/{sender_account_number}/{recipient_account_number}/recipient`
* **Request Content-Type**: なし
* **Response**: `200 OK` (application/json)
  ```json
  {
    "sender_account_number": "123456",
    "sender_bank_balance": 100000,
    "recipient_icon": "/static/images/user2.png",
    "recipient_name": "佐藤花子"
  }
  ```

---

## 4. 送金処理 (Step 4)
* **Method**: `POST`
* **Endpoint**: `/api/user/{sender_account_number}/{recipient_account_number}/transfer`
* **Request Content-Type**: `application/json`
  ```json
  {
    "transfer_amount": 5000,
    "message": "ランチ代"
  }
  ```
  * `message`: null許容 (optional)
* **Response**: `200 OK` (レスポンスボディなし)

---

## データベーススキーマ一覧

### `main` テーブル (`UserAccount` モデル)
| カラム名 | 意味 | 型 |
|---|---|---|
| `account_number` | 口座番号 (PK) | str |
| `user_icon` | ユーザアイコン | str (path) |
| `user_name` | ユーザ名 | str |
| `account_balance` | 預金残高 | int |

### `transfer_transaction` テーブル (`TransferTransaction` モデル)
| カラム名 | 意味 | 型 |
|---|---|---|
| `transaction_number` | 取引番号 (PK) | str |
| `sender_account_number` | fromの口座番号 (FK) | str |
| `recipient_account_number` | toの口座番号 (FK) | str |
| `transfer_amount` | 金額 | int |
| `message` | メッセージ (null許容) | str |
| `time` | 時間 (自動設定) | str / datetime |
