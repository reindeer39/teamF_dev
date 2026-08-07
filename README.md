# teamF_dev

チーム開発用のリポジトリです。フロントエンド(React)とバックエンド(Django)で構成されています。

## 目次

- [構成](#構成)
- [セットアップ](#セットアップ)
- [仕様書](#仕様書)
- [データベースとモックデータ](#データベースとモックデータ)
- [React・API・データベース連携](#reactapiデータベース連携)
- [Git運用ルール](#git運用ルール)

## 構成

```
teamF_dev/
├── src/                         # フロントエンド (React / Create React App)
│   ├── navigation/               # 画面遷移(ルーティング)の管理
│   │   └── AppNavigator.js
│   ├── TopScreen/                 # 画面: プロフィール(トップ)
│   ├── SelectSendMoney/            # 画面: 送金先一覧
│   ├── ProcessSendMoney/            # 画面: 送金処理
│   ├── MakeInvoiceLink/             # 画面: 請求リンク作成
│   ├── CopyInvoiceLink/             # 画面: 請求リンク表示・コピー
│   ├── InvoiceStatus/               # 画面: 発行した請求一覧
│   ├── ProcessPayment/              # 画面: 請求リンクの支払い
│   ├── components/                   # 共通UIパーツ
│   ├── auth/                          # 認証状態とログイン・新規登録画面
│   ├── api/                           # 共通HTTPクライアントと機能別API
│   ├── images/
├── public/
├── package.json
└── backend/        # バックエンド (Django)
    ├── config/      # プロジェクト設定
    ├── api/         # APIアプリ
    ├── manage.py
    ├── requirements.txt
    ├── API_DOCUMENTATION.md       # API仕様書
    └── DATABASE_DOCUMENTATION.md  # データベース仕様書
```

## セットアップ

最初に、公開用の安全な設定をコピーします。

```bash
cp .env.example .env
```

ルートの`.env`にある`REACT_APP_DATA_MODE`は、Reactのアイコン表示とDjangoのモックデータ選択で共通して使用されます。通常開発では`public`を使用します。

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

モックデータ投入後は、次の開発用アカウントですぐにログインできます。

| メールアドレス | パスワード | 口座番号 |
|---|---|---|
| `yamada@example.com` | `teamf-dev-pass` | `1000001` |
| `sato@example.com` | `teamf-dev-pass` | `1000002` |
| `suzuki@example.com` | `teamf-dev-pass` | `1000003` |

これらはローカル開発専用です。本番環境では使用しないでください。ログイントークンはブラウザのlocalStorageへ保存されるため、ページを再読み込みしてもログイン状態が復元されます。

## 仕様書

- [React・API・DB連携ガイド](backend/BACKEND_FLOW_GUIDE.md) — ログイン、画面表示、送金を実コードに沿って追う解説
- [API仕様書](backend/API_DOCUMENTATION.md) — エンドポイント一覧、リクエスト/レスポンス形式
- [データベース仕様書](backend/DATABASE_DOCUMENTATION.md) — テーブル定義、制約、ER概要

## データベースとモックデータ

### 今回実装した内容

送金アプリ用として、Djangoの`api`アプリに以下を実装しています。

- SQLiteデータベース: `backend/db.sqlite3`
- 口座モデル・テーブル: `Account` / `accounts`
- 送金履歴モデル・テーブル: `Transaction` / `transactions`
- 請求モデル・テーブル: `Invoice` / `invoices`
- モデルのマイグレーション: `backend/api/migrations/0001_initial.py`
- 公開用モックデータ: `backend/api/mock_data/public/mock_data.json`
- デモ用モックデータ: `backend/api/mock_data/private/mock_data.json`（Git管理外）
- モックデータ投入コマンド: `python manage.py seed_mock_data`
- JSON対象データの安全な再作成: `python manage.py seed_mock_data --reset`
- Account、Transaction、InvoiceのDjango管理画面
- モデル、制約、モックデータ投入処理のテスト

`Account`には口座番号、ユーザーアイコン、ユーザー名、預金残高を保存します。`Transaction`には取引番号、送金元口座、送金先口座、送金金額、メッセージ、送金日時を保存します。`Invoice`には請求リンクで使うUUID形式の請求番号、請求元・支払口座、請求金額、メッセージ、支払状態・日時、対応するTransactionを保存します。

データベース制約により、残高は0以上、送金金額は1以上、送金元と送金先は別口座である必要があります。また、取引から参照されている口座は誤って削除されないように保護されています。

### 共同開発における共有方法

SQLite本体の`backend/db.sqlite3`は、開発者ごとにローカルで作成します。このファイルをGitで直接共有すると、各自の作業データが衝突したり、他の開発者のデータを上書きしたりするため、Git管理対象外にしています。

代わりに、次の2種類のファイルをGitで共有します。

- テーブル構造: `backend/api/models.py`と`backend/api/migrations/`
- 共通で使用する公開データ: `backend/api/mock_data/public/mock_data.json`

各開発者がマイグレーションとモックデータ投入コマンドを実行することで、それぞれの`db.sqlite3`に同じテーブルと同じデータを作成できます。

```text
models.py + migrations（テーブル構造） ─┐
                                         ├─ 各開発者がコマンドを実行 → 各自のdb.sqlite3
public/mock_data.json（共有するレコード） ─┘
```

### public・privateモードとUSBデモ

プロジェクトルートの`.env`で、フロントエンドとバックエンドのデータモードをまとめて切り替えます。

```env
# GitHubで共有する架空名とデフォルトアイコン
REACT_APP_DATA_MODE=public

# USBで配布する本名データとメンバー画像
REACT_APP_DATA_MODE=private
```

privateモードのデモでは、USBから次の2か所へファイルをコピーします。

```text
public/private-avatars/                 # avatar-01.pngなどのメンバー画像
backend/api/mock_data/private/mock_data.json
```

その後、ルートの`.env`を次の内容にして起動します。

```env
REACT_APP_DATA_MODE=private
```

```bash
cd backend
python manage.py seed_mock_data --reset
python manage.py runserver
```

別のターミナルでプロジェクトルートから`npm start`を実行してください。`.env`を変更した場合はReact開発サーバーの再起動が必要です。`.env`、privateモックデータ、メンバー画像はいずれもGit管理外です。

> **公開用ビルドの注意:** Create React Appはmodeに関係なく`public/`配下を`build/`へコピーします。公開用に`npm run build`する前は、`public/private-avatars/`からメンバー画像を取り除いてください。private画像が入ったbuild成果物は公開・共有しないでください。

一時的にモックデータだけを明示して投入する場合は、`.env`より`--mode`が優先されます。

```bash
python manage.py seed_mock_data --mode public
python manage.py seed_mock_data --mode private
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
backend/api/mock_data/public/mock_data.json
```

JSONはDjango fixture固有の形式ではなく、`accounts`、`transactions`、`invoices`を持つ通常のJSONです。主な記載ルールは次のとおりです。

- `account_number`は文字列として記載する
- `transaction_number`はUUID形式の文字列として記載する
- `account_balance`は0以上の整数にする
- `transfer_amount`は1以上の整数にする
- `sender_account_number`と`recipient_account_number`には存在する口座番号を記載する
- 送金元と送金先に同じ口座を指定しない
- 同じ口座番号または取引番号をJSON内で重複させない
- `invoice_number`はUUID形式の文字列、`invoice_amount`は1以上の整数にする
- `invoice_flag`は未払いの`notpay`または支払済みの`paid`にする
- 未払いでは`paid_time`、`paid_by`、`transaction_number`をすべて`null`にする
- 支払済みでは上記3項目をすべて設定し、請求元と支払口座を別口座にする
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
git add backend/api/mock_data/public/mock_data.json
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

Account、Transaction、Invoiceの順に登録します。口座番号、取引番号、請求番号を識別キーとしているため、実行結果は次のようになります。

- 初回実行: JSONのデータを新規登録
- 2回目以降: 同じキーのデータを更新し、レコードは重複しない
- JSONを変更して再実行: 既存データを新しい内容へ更新
- 既存Transactionの更新: `created_at`は変更せず、送金元、送金先、金額、メッセージだけを更新
- 既存Invoiceの更新: `created_time`は変更せず、請求内容と支払状態だけを更新

処理全体はデータベーストランザクションで保護されています。不正なUUID、不足口座、負の残高、0円以下の送金などが見つかった場合は処理を中断し、途中まで登録したデータもすべてロールバックします。

### JSONの内容で対象データを作り直す

JSON対象のデータを一度削除し、JSONの状態から再作成したい場合に使用します。

```bash
python manage.py seed_mock_data --reset
```

削除・登録順序は以下です。

1. JSONに請求番号が記載されているInvoiceだけを削除
2. JSONに取引番号が記載されているTransactionだけを削除
3. JSONに口座番号が記載されているAccountだけを削除
4. JSONのAccountを登録
5. JSONのTransactionを登録
6. JSONのInvoiceを登録

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

### 請求用モックデータを各開発者のSQLiteへ反映する

```bash
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py seed_mock_data
```

JSONの内容どおりに対象モックデータを作り直す場合は、次を実行します。

```bash
python manage.py seed_mock_data --reset
```

公開用モックデータの編集場所は`backend/api/mock_data/public/mock_data.json`です。`backend/db.sqlite3`は各開発者のローカルファイルであり、Gitでは共有・コミットしません。テーブル構造はマイグレーション、共同開発用データはpublic側のJSONで共有します。

## React・API・データベース連携

### 画面操作とAPIの対応

マージしたトップ画面、送金先選択画面、送金処理画面を以下の流れで連携しています。

| Reactの操作 | API | データベース処理 |
|---|---|---|
| 新規登録 | `POST /api/make_account` | 7桁の口座番号・表示名・メール・パスワードからDjango UserとAccountを同時作成 |
| ログイン | `POST /api/login` | 認証トークンと口座情報を取得 |
| ログイン状態を復元 | `GET /api/auth/me/` | トークンに紐づく自分のUserとAccountを取得 |
| トップ画面を表示 | `GET /api/user/{account_number}/summary` | ログイン中の口座を`accounts`から取得 |
| 「送金する」を押す | `GET /api/user/{account_number}/recipient_list` | ログイン口座以外のAccountを取得 |
| 送金先を選択 | `GET /api/user/{sender}/{recipient}/recipient` | 送金先と送金可能残高を取得 |
| 金額・メッセージを入力して「送金」を押す | `POST /api/user/{sender}/{recipient}/transfer` | ログイン口座を送金元として残高更新とTransaction作成 |
| 「請求する」でリンクを作成 | `POST /api/user/{account_number}/invoice_request` | ログイン口座を請求元としてInvoice作成 |
| 請求状態を確認 | `GET /api/user/{account_number}/invoice_list` | ログイン口座が発行したInvoice一覧を取得 |
| `/invoice/{invoice_number}`を開く | `GET /api/{invoice_number}/get_inf`（認証不要） | UUIDから請求元・金額・状態を取得 |
| 「支払う」を押す | `POST /api/{invoice_number}/pay`（認証不要） | 支払口座の残高、Transaction、Invoiceを一括更新 |
| ログアウト | `POST /api/auth/logout/` | サーバーとブラウザのトークンを削除 |

固定の`src/account.js`は廃止しました。送金元口座はReactの定数ではなく、ログイン時にAPIから受け取った`account.account_number`をAppNavigatorが保持し、各画面のURL/propsへ渡します。`get_inf`・`pay`はURL(`/{invoice_number}`)から請求を特定するため、ログインしていない相手でも開けます。

### 画面遷移(ルーティング)の構成

通常画面は`src/navigation/AppNavigator.js`のstateで切り替え、共有する請求URLだけは`react-router-dom`で`/invoice/{invoice_number}`へルーティングします。

- `AppNavigator`が`currentScreen`という状態を持ち、値に応じて通常画面を切り替える
- 口座情報(`account`)の取得も`AppNavigator`が行い、必要な画面へpropsとして渡す
- 各画面は`onBack`や`onSelectRecipient`などのコールバックをpropsで受け取り、通常画面の遷移は`AppNavigator`に委ねる

```text
index.js
  └─ BrowserRouter
       └─ AuthProvider（トークン・ログイン状態を管理）
          └─ AppNavigator
            ├─ 未ログイン                    → AuthScreen
            ├─ currentScreen === 'profile'    → TopScreen
            ├─ currentScreen === 'recipients' → SelectSendMoney
            ├─ currentScreen === 'transfer'   → ProcessSendMoney
            ├─ currentScreen === 'invoice'    → MakeInvoiceLink
            ├─ currentScreen === 'invoiceStatus' → InvoiceStatusScreen
            └─ /invoice/:invoiceNumber        → ProcessPayment
```

画面を追加する場合の手順:

1. 既存画面と同じ形で `src/<画面名>/<画面名>.js` フォルダを作成する
2. `AppNavigator.js` に新しい `currentScreen` の値と、対応する画面コンポーネントの分岐を追加する
3. 画面から次の画面へ遷移したい場合は、直接importせず `AppNavigator` から渡されたコールバックpropsを呼び出す

### API連携コードの場所

- `src/api/client.js`: ベースURL、JSON処理、Authorizationヘッダー、共通エラー処理
- `src/api/auth.js`: signup(`/make_account`)、login(`/login`)、logout、ログイン状態復元
- `src/api/accounts.js`: 口座概要(`/user/{account_number}/summary`)、送金先一覧・詳細
- `src/api/transfers.js`: 送金POST(`/user/{sender}/{recipient}/transfer`)
- `src/api/invoices.js`: 請求作成・一覧・請求情報取得・支払い
- `src/auth/AuthContext.js`: トークン保存とアプリ全体の認証状態
- `src/auth/AuthScreen.js`: ログイン・新規登録フォーム
- `src/navigation/AppNavigator.js`: 画面遷移の管理と口座情報の取得
- `src/TopScreen/TopScreen.js`: トップ画面(プロフィール)の表示
- `src/SelectSendMoney/SelectSendMoney.js`: 送金先一覧の取得
- `src/ProcessSendMoney/ProcessSendMoney.js`: 送金先情報の取得と送金POST
- `backend/api/urls.py`: APIのURL定義
- `backend/api/serializers.py`: 新規登録の4項目と重複・パスワード検証
- `backend/api/views.py`: Accountの取得、残高更新、Transaction登録
- `backend/api/tests.py`: APIリクエストからDB更新までの自動テスト

コード内で次の文字列を検索すると、APIとDBの連携箇所を確認できます。

```bash
rg -n "API連携ポイント" src backend/api
```

各連携箇所には、共同開発者向けに`API連携ポイント`から始まるコメントを記載しています。APIを追加した場合も、Reactの呼び出し元とDjangoのDB更新箇所に同じ形式のコメントを追加してください。

### 開発サーバーの起動

ターミナルを2つ開きます。

ターミナル1（Django）：

```bash
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py seed_mock_data
python manage.py runserver
```

ターミナル2（React・プロジェクトルート）：

```bash
npm install
npm start
```

Reactは`http://localhost:3000`、Django APIは`http://127.0.0.1:8000/api/`で起動します。APIの接続先を変える場合は、React起動前に`REACT_APP_API_BASE_URL`を指定できます。

```bash
REACT_APP_API_BASE_URL=http://127.0.0.1:8000/api npm start
```

### APIとDB連携の確認方法

Django API単体は次のコマンドで確認できます。

```bash
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"mail_address":"yamada@example.com","password":"teamf-dev-pass"}' \
  http://127.0.0.1:8000/api/login | python -c \
  'import json,sys; print(json.load(sys.stdin)["token"])')

curl -H "Authorization: Token $TOKEN" \
  http://127.0.0.1:8000/api/user/1000001/summary
```

送金POSTはDBの残高と履歴を実際に変更します。開発用データであることを確認してから実行してください。

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $TOKEN" \
  -d '{"transfer_amount":1000,"message":"API確認"}' \
  http://127.0.0.1:8000/api/user/1000001/1000002/transfer
```

実行後、Django管理画面で両口座の残高とTransaction履歴を確認できます。自動テストではテスト専用DBを使うため、ローカルの`db.sqlite3`を変更せずに連携を確認できます。

```bash
cd backend
source venv/bin/activate
python manage.py test api
```

React側のAPI呼び出しと画面遷移は次で確認します。

```bash
CI=true npm test -- --watchAll=false
npm run build
```

## Git運用ルール

### データベース・共有データ

- `backend/db.sqlite3` は各開発者のローカルデータベースなのでGitへコミットしない
- `backend/api/mock_data/public/mock_data.json` はチームで共有するためGitへコミットする
- `backend/api/mock_data/private/` と `public/private-avatars/` はGitへコミットしない
- `.env.example` はpublic設定として共有し、`.env`はGitへコミットしない
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
