# API エラー仕様（暫定）

> この文書はチーム内で合意するためのドラフトです。現時点の実装と一致しない項目を含みます。

## 方針

- フロントエンドは、入力時の案内とボタンの活性・非活性を担当する。
- バックエンドは、APIを直接呼び出された場合でも不正なデータを保存しないための最終チェックを担当する。
- DB制約やモデルの変更はDB担当者と合意してから行う。
- Step 12までは、送金処理に必要な最小限のエラーのみ定義する。

## 暫定レスポンス形式

```json
{
  "error_code": "ACCOUNT_NOT_FOUND",
  "message": "指定された口座が見つかりません。"
}
```

`error_code` はフロントエンドの分岐に使用し、`message` は画面表示または調査に使用する。

## Step 6までに必要なエラー

| HTTPステータス | error_code | 発生条件 | 実装状況 |
|---|---|---|---|
| 400 | `TRANSFER_AMOUNT_REQUIRED` | `transfer_amount` が未指定 | 一部実装済み（形式は未対応） |
| 400 | `INVALID_TRANSFER_AMOUNT` | 金額が整数でない、または許可範囲外 | 未実装 |
| 400 | `SAME_ACCOUNT_TRANSFER` | 送金元と送金先が同じ | 未実装 |
| 404 | `ACCOUNT_NOT_FOUND` | 指定された口座が存在しない | 一部実装済み（形式は未対応） |
| 409 | `INSUFFICIENT_BALANCE` | 送金額が送金元残高を超えている | 未実装 |
| 500 | `INTERNAL_SERVER_ERROR` | 想定外のサーバ内部エラー | 一部実装済み（内部例外を返している） |

## エンドポイント別の対象

| Endpoint | 想定するエラー |
|---|---|
| `GET /api/user/{account_number}/summary` | `ACCOUNT_NOT_FOUND` |
| `GET /api/user/{account_number}/recipient_list` | `ACCOUNT_NOT_FOUND` |
| `GET /api/user/{sender}/{recipient}/recipient` | `ACCOUNT_NOT_FOUND` |
| `POST /api/user/{sender}/{recipient}/transfer` | 上記すべて |

## チームで決める事項

- 送金額 `0` を許可するか、`1` 以上とするか。
- 残高不足を `400 Bad Request` と `409 Conflict` のどちらにするか。
- `message` の最大文字数と、空文字・nullの扱い。
- エラーメッセージを日本語で固定するか。
- 送金元と送金先のどちらが存在しないかを区別するか。

## Step 12後に検討する事項

- 認証・認可エラー（401、403）。
- リクエスト回数制限（429）。
- エラーログの識別番号。
- 全APIでのレスポンス形式統一。