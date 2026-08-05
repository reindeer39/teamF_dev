# 送金システム API 仕様書

BASE URL: `http://localhost:8000` (`http://127.0.0.1:8000`)

---

## 公式Stepとの対応

| 公式Step | バックエンドAPIの役割 |
|---|---|
| Step 1 | ユーザ口座情報を取得する |
| Step 2 | APIなし（フロントエンドの画面遷移） |
| Step 3 | 送金先一覧を取得する |
| Step 4 | 選択した送金先と送金可能額を取得する |
| Step 5 | 送金処理を行う |
| Step 6 | 送金処理に任意のメッセージを添付する |

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
* **Response**: `200 OK` (レスポンスボディなし)
* **エラー制御**: 送金額が送金元の預金残高を超える場合 (`account_balance < transfer_amount`)、バックエンド側で `400 Bad Request` (`{"error": "Insufficient account balance"}`) を返却します。

---

## 5. エラーレスポンス仕様

各APIにおいて例外・異常が発生した場合、以下の標準HTTPステータスコードとJSON構造で応答します。

* **Content-Type**: `application/json`
* **レスポンス構造**:
  ```json
  {
    "error": "[エラー詳細メッセージ]"
  }
  ```

### HTTPステータスコード定義一覧

| ステータスコード | 意味 | 発生条件の例 |
|---|---|---|
| `400 Bad Request` | リクエスト不正 / 残高不足 | 送金パラメータ (`transfer_amount`) の不足、または **残高不足 (`account_balance < transfer_amount`)** の場合 |
| `404 Not Found` | リソース非存在 | 指定された口座番号 (`account_number`) がデータベースに存在しない場合 |
| `500 Internal Server Error` | サーバー内部エラー | データベース接続失敗やシステム障害、モデル未定義の場合 |

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
| `time` | 時間  | str (`YYYY-MM-DD HH:MM:SS.ffffff`) |
