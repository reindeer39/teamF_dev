# 送金システム データベース仕様書

DB: SQLite (`backend/db.sqlite3`)
定義: `backend/api/models.py` / マイグレーション: `backend/api/migrations/`

---

## 1. `accounts` テーブル (`Account` モデル)

口座情報を保存する。

| カラム名 | 型 | 制約 | 意味 |
|---|---|---|---|
| `account_number` | CharField(max_length=20) | PK | 口座番号 |
| `auth_user_id` | OneToOneField → Django User | null可, unique, on_delete=CASCADE | 認証ユーザー |
| `user_icon` | CharField(max_length=255) | blank可, default="" | ユーザーアイコンのパス |
| `user_name` | CharField(max_length=100) | 必須 | ユーザー名 |
| `account_balance` | PositiveBigIntegerField | default=0 | 預金残高 |

### 制約

- `account_balance_gte_0` — `account_balance >= 0`（残高がマイナスになる更新は保存時にエラーになる）

### 削除保護

`Transaction`から参照されている`Account`は`on_delete=PROTECT`により削除できない（送金履歴の整合性を守るため）。

新規登録APIで作成するAccountには必ず認証Userを設定する。認証Userを削除した場合、そのUserに属するAccountも`CASCADE`で削除する。既存モック・移行データとの互換性のため、`auth_user`自体はnullを許可する。

---

## 2. `transactions` テーブル (`Transaction` モデル)

送金履歴を保存する。

| カラム名 | 型 | 制約 | 意味 |
|---|---|---|---|
| `transaction_number` | UUIDField | PK, default=uuid4, editable不可 | 取引番号 |
| `sender` | ForeignKey → `Account.account_number` | on_delete=PROTECT, related_name=`sent_transactions` | 送金元口座 |
| `recipient` | ForeignKey → `Account.account_number` | on_delete=PROTECT, related_name=`received_transactions` | 送金先口座 |
| `transfer_amount` | PositiveBigIntegerField | MinValueValidator(1) | 送金金額 |
| `message` | CharField(max_length=200) | blank可, default="" | メッセージ |
| `created_at` | DateTimeField | auto_now_add | 送金日時（自動設定・変更不可） |

### 制約

- `transfer_amount_gte_1` — `transfer_amount >= 1`（0円以下の送金は不可）
- `sender_recipient_different` — `sender != recipient`（自分自身への送金は不可）

### 並び順

`Meta.ordering = ["-created_at"]`（新しい取引が先頭）

---

## ER概要

```
Account (accounts)
  account_number (PK)
  auth_user_id → auth_user (CASCADE, OneToOne, related_name=bank_account)
     ├─< sent_transactions ─── Transaction.sender
     └─< received_transactions ─ Transaction.recipient

Transaction (transactions)
  transaction_number (PK)
  sender      → Account (PROTECT)
  recipient   → Account (PROTECT)
```

---

## モックデータ

チームで共有する初期データは `backend/api/mock_data/mock_data.json` にJSON形式で定義し、`python manage.py seed_mock_data` で反映する。投入ルール・運用手順はREADMEの[データベースとモックデータ](../README.md#データベースとモックデータ)を参照。

---

## 管理画面

`/admin/` から `Account` / `Transaction` / `Invoice` の一覧・検索・編集が可能（`backend/api/admin.py`）。

- `AccountAdmin`: 口座番号・ユーザー名・残高・認証User・メールアドレスを一覧表示し、口座番号/ユーザー名/認証情報で検索
- `TransactionAdmin`: 取引番号・送信元・送信先・金額・メッセージ・日時で一覧表示、日時でフィルタ、口座番号/ユーザー名/メッセージで検索。`transaction_number`と`created_at`は編集不可
