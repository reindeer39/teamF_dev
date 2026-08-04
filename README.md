# teamF_dev

チーム開発用のリポジトリです。フロントエンド(React)とバックエンド(Django)で構成されています。

## 目次

- [構成](#構成)
- [セットアップ](#セットアップ)
- [データベースとモックデータ](#データベースとモックデータ)
- [Git運用ルール](#git運用ルール)

## 構成

```
teamF_dev/
├── src/            # フロントエンド (React / Create React App)
├── public/
├── package.json
└── backend/        # バックエンド (Django)
    ├── config/      # プロジェクト設定
    ├── api/         # APIアプリ
    ├── manage.py
    └── requirements.txt
```

## セットアップ

### フロントエンド (React)

```bash
npm install
npm start
```

`http://localhost:3000` で起動します。

その他のコマンド:

- `npm test` — テストランナーを起動
- `npm run build` — 本番用ビルドを `build/` に出力

Create React App で構築されています。詳細は [CRAドキュメント](https://facebook.github.io/create-react-app/docs/getting-started) を参照してください。

### バックエンド (Django)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_mock_data
python manage.py runserver
```

`http://localhost:8000` で起動します。React 開発サーバー(`localhost:3000`)からのアクセスは CORS 許可済みです。

## データベースとモックデータ

### 今回実装した内容

送金アプリ用として、Djangoの`api`アプリに以下を実装しています。

- SQLiteデータベース: `backend/db.sqlite3`
- 口座モデル・テーブル: `Account` / `accounts`
- 送金履歴モデル・テーブル: `Transaction` / `transactions`
- モデルのマイグレーション: `backend/api/migrations/0001_initial.py`
- 共有用モックデータ: `backend/api/mock_data/mock_data.json`
- モックデータ投入コマンド: `python manage.py seed_mock_data`
- JSON対象データの安全な再作成: `python manage.py seed_mock_data --reset`
- AccountとTransactionのDjango管理画面
- モデル、制約、モックデータ投入処理のテスト

`Account`には口座番号、ユーザーアイコン、ユーザー名、預金残高を保存します。`Transaction`には取引番号、送金元口座、送金先口座、送金金額、メッセージ、送金日時を保存します。

データベース制約により、残高は0以上、送金金額は1以上、送金元と送金先は別口座である必要があります。また、取引から参照されている口座は誤って削除されないように保護されています。

### 共同開発における共有方法

SQLite本体の`backend/db.sqlite3`は、開発者ごとにローカルで作成します。このファイルをGitで直接共有すると、各自の作業データが衝突したり、他の開発者のデータを上書きしたりするため、Git管理対象外にしています。

代わりに、次の2種類のファイルをGitで共有します。

- テーブル構造: `backend/api/models.py`と`backend/api/migrations/`
- 共通で使用するデータ: `backend/api/mock_data/mock_data.json`

各開発者がマイグレーションとモックデータ投入コマンドを実行することで、それぞれの`db.sqlite3`に同じテーブルと同じデータを作成できます。

```text
models.py + migrations（テーブル構造） ─┐
                                         ├─ 各開発者がコマンドを実行 → 各自のdb.sqlite3
mock_data.json（共有するレコード） ─────┘
```

### 初めて環境を作る開発者

リポジトリを取得した後、プロジェクトルートから以下を実行してください。

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_mock_data
python manage.py runserver
```

`migrate`がローカルの`db.sqlite3`にテーブルを作成し、`seed_mock_data`が共有JSONの口座と送金履歴を登録します。

### pull後に共有データを自分のDBへ反映する

他のメンバーの変更を取り込み、共有されたテーブル構造とデータを自分のDBへ反映するには、プロジェクトルートで以下を実行してください。

```bash
git pull
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py seed_mock_data
```

新しいマイグレーションがなければ`migrate`は何も変更しません。`seed_mock_data`は何度実行しても、同じ口座番号や取引番号のレコードを重複登録しません。既存レコードはJSONの内容で更新されます。

通常、共同開発者が最新データを取り込むために必要なコマンドは次の2つです。

```bash
python manage.py migrate
python manage.py seed_mock_data
```

### モックデータを変更してチームへ共有する

共通データを追加・変更する担当者は、以下のファイルを編集します。

```text
backend/api/mock_data/mock_data.json
```

JSONはDjango fixture固有の形式ではなく、`accounts`と`transactions`を持つ通常のJSONです。主な記載ルールは次のとおりです。

- `account_number`は文字列として記載する
- `transaction_number`はUUID形式の文字列として記載する
- `account_balance`は0以上の整数にする
- `transfer_amount`は1以上の整数にする
- `sender_account_number`と`recipient_account_number`には存在する口座番号を記載する
- 送金元と送金先に同じ口座を指定しない
- 同じ口座番号または取引番号をJSON内で重複させない
- JSONにはコメントを書かない。補足説明はREADMEへ記載する

編集した担当者は、コミット前に以下を実行して内容を確認してください。

```bash
cd backend
source venv/bin/activate
python manage.py seed_mock_data
python manage.py test api
```

問題がなければ、JSONをGitへコミットしてpushします。`db.sqlite3`はコミットしません。

```bash
cd ..
git add backend/api/mock_data/mock_data.json
git commit -m "feat: モックデータを更新"
git push
```

変更を受け取るメンバーはpull後に以下を実行します。

```bash
git pull
cd backend
source venv/bin/activate
python manage.py seed_mock_data
```

これにより、Gitで共有されたJSONの内容が各メンバーのローカルSQLiteへ反映されます。

### `seed_mock_data`の動作

```bash
python manage.py seed_mock_data
```

Accountを先に登録し、その後Transactionを登録します。口座番号と取引番号を識別キーとしているため、実行結果は次のようになります。

- 初回実行: JSONのデータを新規登録
- 2回目以降: 同じキーのデータを更新し、レコードは重複しない
- JSONを変更して再実行: 既存データを新しい内容へ更新
- 既存Transactionの更新: `created_at`は変更せず、送金元、送金先、金額、メッセージだけを更新

処理全体はデータベーストランザクションで保護されています。不正なUUID、不足口座、負の残高、0円以下の送金などが見つかった場合は処理を中断し、途中まで登録したデータもすべてロールバックします。

### JSONの内容で対象データを作り直す

JSON対象のデータを一度削除し、JSONの状態から再作成したい場合に使用します。

```bash
python manage.py seed_mock_data --reset
```

削除・登録順序は以下です。

1. JSONに取引番号が記載されているTransactionだけを削除
2. JSONに口座番号が記載されているAccountだけを削除
3. JSONのAccountを登録
4. JSONのTransactionを登録

データベース全体のflushや全件削除は行いません。JSONに記載されていない手動追加データは残ります。また、JSON外のTransactionが対象Accountを参照している場合は、安全のため削除せず処理全体をロールバックします。

通常のデータ更新には`seed_mock_data`を使用し、対象データをJSONから完全に作り直す必要がある場合だけ`--reset`を使用してください。

### モデルを変更した場合の共有方法

モデルのフィールド追加など、データベース構造を変更した担当者は以下を実行します。

```bash
cd backend
source venv/bin/activate
python manage.py makemigrations api
python manage.py migrate
python manage.py test api
```

変更した`models.py`だけでなく、生成されたマイグレーションファイルもGitへコミットしてください。

```bash
cd ..
git add backend/api/models.py backend/api/migrations/
git commit -m "feat: データベース構造を更新"
git push
```

変更を受け取ったメンバーは、pull後に次を実行します。通常、受け取る側で`makemigrations`を実行する必要はありません。

```bash
git pull
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py seed_mock_data
```

### 管理画面でデータを確認する

初回のみ管理ユーザーを作成します。

```bash
cd backend
source venv/bin/activate
python manage.py createsuperuser
python manage.py runserver
```

ブラウザで`http://127.0.0.1:8000/admin/`を開いてください。Accountでは口座番号、ユーザー名、残高を、Transactionでは取引番号、送金元、送金先、送金金額、メッセージ、送金日時を確認できます。

## Git運用ルール

### データベース・共有データ

- `backend/db.sqlite3` は各開発者のローカルデータベースなのでGitへコミットしない
- `backend/api/mock_data/mock_data.json` はチームで共有するためGitへコミットする
- `models.py` を変更した場合は、生成したマイグレーションファイルもコミットする
- pull後に新しいマイグレーションがある場合は、`python manage.py migrate` を実行する
- `mock_data.json` が更新された場合は、`python manage.py seed_mock_data` を実行する

### ブランチ戦略

- `main` — 常に動作する安定版。直接pushしない。
- `feature/*` — 新機能開発用
- `fix/*` — バグ修正用

すべての変更は `main` から派生したブランチで作業し、Pull Request経由でマージします。

### ブランチ命名

```
<種別>/<内容が分かる短い説明>
```

例:
- `feature/login-form`
- `fix/cors-error`

Issueがある場合は番号も入れる: `feature/12-login-form`

### コミットメッセージ

先頭に種別のprefixを付けます。

| prefix | 用途 |
|---|---|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみの変更 |
| `style` | フォーマットなど動作に影響しない変更 |
| `refactor` | 挙動を変えないコード整理 |
| `test` | テストの追加・修正 |
| `chore` | ビルド設定・依存関係更新など |

例: `feat: ログイン画面を追加`

### Pull Request

1. 作業ブランチを push し、`dev` 宛てにPRを作成する
2. PRの説明に変更内容と確認方法(動作確認手順)を書く
3. **レビュー1名以上の承認**を必須とする
4. マージ方法は **Squash and merge** に統一する
5. マージ後、不要になったブランチは削除する

### 禁止事項

- `main` への直接push
- `--force` push(自分だけの作業ブランチを除く)
- レビューなしでのマージ
- コンフリクトを解消せずにマージ依頼を出す
