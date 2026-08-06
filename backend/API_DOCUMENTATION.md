# 送金システム API仕様書

BASE URL: `http://127.0.0.1:8000/api`

## 認証

ログイン・新規登録以外のAPIはDRF Token Authenticationを使用します。

```http
Authorization: Token <loginまたはsignupで取得したtoken>
```

認証がない、またはトークンが無効な場合は`401 Unauthorized`です。

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

```json
{
  "token": "0123456789abcdef...",
  "username": "yamada",
  "account": {
    "account_number": "1000001",
    "user_icon": "/icons/user1.png",
    "user_name": "山田太郎",
    "account_balance": 97000
  }
}
```

### ログイン状態取得

`GET /auth/me`

保存済みトークンが有効か確認し、UserとAccountを返します。

### ログアウト

`POST /auth/logout`

現在のトークンを削除し、`204 No Content`を返します。

## 口座・送金API

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

### 送金先一覧

`GET /account/recipients`

ログイン中の口座を除くAccountを`recipient_list`で返します。

### 送金先詳細

`GET /account/recipients/{recipient_account_number}`

ログイン中の口座残高と選択した送金先情報を返します。

### 送金

`POST /transfers/{recipient_account_number}`

```json
{
  "transfer_amount": 5000,
  "message": "ランチ代"
}
```

送金元はリクエストURLやJSONでは指定せず、認証トークンに紐づくAccountを使用します。送金元・送金先の残高更新とTransaction作成は`transaction.atomic()`内で実行します。

## 互換API

既存フロントエンドとの移行互換性のため、以下のURLも残しています。

- `GET /user/{account_number}/summary`
- `GET /user/{account_number}/recipient_list`
- `GET /user/{sender}/{recipient}/recipient`
- `POST /user/{sender}/{recipient}/transfer`

すべてトークン認証が必須で、URLの送金元・口座番号がログイン中のAccountと一致しない場合は`403 Forbidden`です。新規コードでは上記の口座・送金APIを使用してください。

## 主なエラー

| ステータス | 意味 |
|---|---|
| `400 Bad Request` | 入力不正、残高不足、ログイン失敗 |
| `401 Unauthorized` | トークンなし、または無効なトークン |
| `403 Forbidden` | 他口座としてアクセス・送金しようとした |
| `404 Not Found` | 口座が存在しない |
| `409 Conflict` | 認証ユーザーにAccountが紐づいていない |

DB定義は[DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)、起動・開発用ログイン情報は[README](../README.md)を参照してください。
