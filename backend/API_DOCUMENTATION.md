# 送金・請求システム API仕様書

BASE URL: `http://127.0.0.1:8000/api`

## 認証

ログイン・新規登録・請求リンク参照以外の利用者向けAPIはDRF Token Authenticationを使用します。

```http
Authorization: Token <loginまたはsignupで取得したtoken>
```

### 新規登録

`POST /auth/signup`

```json
{
  "username": "new-user",
  "password": "十分に強いパスワード",
  "user_name": "表示名",
  "email": "user@example.com"
}
```

Django Userと残高0円のAccountを同一トランザクション内で作成し、`201 Created`でトークンと口座情報を返します。口座番号は重複しない7桁の番号を自動生成します。

### ログイン

`POST /auth/login`

```json
{
  "username": "yamada",
  "password": "teamf-dev-pass"
}
```

成功時は`token`、`username`、紐づく`account`を返します。

### ログイン状態・ログアウト

- `GET /auth/me`: 保存済みトークンに紐づくUserとAccountを返す
- `POST /auth/logout`: 現在のトークンを削除し`204 No Content`を返す

## 認証済み口座・送金API

### 自分の口座概要

`GET /account/summary`

```json
{
  "account_number": "1000001",
  "user_icon": "/icons/user1.png",
  "user_name": "山田太郎",
  "account_balance": 97000
}
```

### 送金先一覧・詳細

- `GET /account/recipients`
- `GET /account/recipients/{recipient_account_number}`

### 送金

`POST /transfers/{recipient_account_number}`

```json
{
  "transfer_amount": 5000,
  "message": "ランチ代"
}
```

送金元はURLやJSONでは指定せず、認証トークンに紐づくAccountを使用します。両口座の残高更新とTransaction作成は`transaction.atomic()`内で実行します。

## 請求API

### 請求作成

`POST /user/{account_number}/invoice_request`

```json
{
  "invoice_amount": 10000,
  "message": "飲み会代割り勘"
}
```

```json
{
  "invoice_link": "http://localhost:3000/invoice/33333333-3333-4333-8333-333333333333"
}
```

### 請求情報取得

`GET /{invoice_number}/get_inf`

```json
{
  "invoice_account_number": "1000001",
  "invoice_amount": "10000",
  "invoice_message": "飲み会代割り勘",
  "invoice_flag": "notpay"
}
```

### 請求支払い

`POST /{invoice_number}/pay`

```json
{
  "my_account_number": "1000002",
  "invoice_account_number": "1000001",
  "invoice_amount": "10000",
  "message": "支払いました"
}
```

URLの`invoice_number`から取得したInvoiceを正として、リクエストの請求元と金額がDBの値に一致するか検証します。残高更新、Transaction作成、Invoiceの`paid`更新と関連付けは、すべて同一トランザクション内で実行します。支払済み請求は`409 Conflict`です。

### 請求一覧

`GET /user/{account_number}/invoice_list`

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

`invoice_time`は`YYYY-MM-DD HH:MM:SS.ffffff`形式で、新しい請求が先頭です。

## 互換API

既存画面との移行互換性のため、以下も残しています。すべてトークン認証が必須で、URLの口座がログイン中のAccountと一致しない場合は`403 Forbidden`です。

- `GET /user/{account_number}/summary`
- `GET /user/{account_number}/recipient_list`
- `GET /user/{sender}/{recipient}/recipient`
- `POST /user/{sender}/{recipient}/transfer`

## 主なエラー

| ステータス | 意味 |
|---|---|
| `400 Bad Request` | 入力不正、残高不足、請求内容不一致、ログイン失敗 |
| `401 Unauthorized` | トークンなし、または無効なトークン |
| `403 Forbidden` | 他口座としてアクセス・送金しようとした |
| `404 Not Found` | 口座または請求が存在しない |
| `409 Conflict` | 支払済み請求、またはUserとAccountの関連不整合 |

DB定義は[DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)、起動・開発用ログイン情報は[README](../README.md)を参照してください。
