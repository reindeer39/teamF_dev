# バックエンド連携ガイド

この資料は、Reactの操作がどのようにDjango APIへ届き、SQLiteのデータを読み書きし、その結果が再びReactへ返るのかを、Django初心者向けに説明します。

APIの正確なURL・入出力は[API_DOCUMENTATION.md](API_DOCUMENTATION.md)、テーブル定義は[DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)も参照してください。

## 1. 最初に知っておく用語

| 用語 | このプロジェクトでの意味 |
|---|---|
| フロントエンド | ブラウザに画面を表示するReact。`src/`にある |
| バックエンド | APIを受け付け、DBを操作するDjango。`backend/`にある |
| API | ReactとDjangoがJSONを使って情報をやり取りする窓口 |
| HTTPメソッド | `GET`は取得、`POST`は登録・更新に使用する |
| JSON | ReactとDjangoの間で送受信するデータ形式 |
| ORM | SQLを直接書かず、Pythonのモデルを使ってDBを操作するDjangoの機能 |
| モデル | DBテーブルをPythonクラスとして表したもの。`api/models.py`にある |
| マイグレーション | モデルの定義をDBのテーブル構造へ反映する仕組み |
| トランザクション | 複数のDB更新を「全部成功」または「全部取り消し」にする仕組み |

## 2. 関係するファイル

| ファイル | 役割 |
|---|---|
| `src/api/user.js` | ReactからDjango APIへ`fetch()`する |
| `src/TopScreen.js` | 口座情報APIを呼び、ユーザー名と残高を表示する |
| `src/SelectSendMoney/SelectSendMoney.js` | 送金先一覧APIを呼ぶ |
| `src/ProcessSendMoney.js` | 送金先情報取得と送金POSTを行う |
| `backend/config/settings.py` | SQLite、アプリ、CORSなどDjango全体の設定 |
| `backend/config/urls.py` | プロジェクト全体のURL入口。`/api/`をapiアプリへ渡す |
| `backend/api/urls.py` | `/api/`より後ろのURLとViewを結び付ける |
| `backend/api/views.py` | リクエストを受け、モデルを使ってDBを読み書きし、JSONを返す |
| `backend/api/models.py` | `accounts`と`transactions`テーブルの定義 |
| `backend/api/migrations/` | モデルから生成されたテーブル構造の変更履歴 |
| `backend/api/admin.py` | Django管理画面でDBデータを確認する設定 |
| `backend/api/tests.py` | APIからDBまで正しく連携するかテストする |
| `backend/db.sqlite3` | 各開発者のローカルDB本体。Gitでは共有しない |

## 3. 全体の処理経路

トップ画面で口座情報を表示するときは、次の順番で処理されます。

```text
React画面
  │ 1. src/api/user.jsのfetch()でHTTPリクエスト
  ▼
GET http://127.0.0.1:8000/api/user/1000001/summary
  │ 2. /api/ を見てapi.urlsへ渡す
  ▼
backend/config/urls.py
  │ 3. 残りのuser/1000001/summaryをViewへ結び付ける
  ▼
backend/api/urls.py
  │ 4. UserSummaryView.get()を実行
  ▼
backend/api/views.py
  │ 5. Account.objects.get(...)でORMに検索を依頼
  ▼
backend/api/models.py
  │ 6. DjangoがSQLへ変換して検索
  ▼
backend/db.sqlite3 の accountsテーブル
  │ 7. 検索結果をAccountオブジェクトとして返す
  ▼
backend/api/views.py
  │ 8. Response(...)でJSONへ変換
  ▼
src/api/user.js
  │ 9. Reactのstateへ保存
  ▼
ブラウザにユーザー名・残高を表示
```

重要なのは、Reactが`db.sqlite3`を直接読むことはないという点です。Reactは必ずDjango APIへ依頼し、DBを操作できるのはDjango側だけです。

## 4. URLがViewへ届く仕組み

### 4.1 `config/urls.py`

```python
path("api/", include("api.urls"))
```

URLが`/api/`から始まる場合、その後の判定を`api/urls.py`へ渡します。

### 4.2 `api/urls.py`

```python
path(
    "user/<str:account_number>/summary",
    UserSummaryView.as_view(),
)
```

たとえば`/api/user/1000001/summary`が届くと、`1000001`が`account_number`変数になり、`UserSummaryView`へ渡されます。

### 4.3 `api/views.py`

GETリクエストなので、APIViewの`get()`が実行されます。

```python
def get(self, request, account_number):
    user = Account.objects.get(account_number=account_number)
```

POSTリクエストの場合は`post()`が実行され、Reactから送られたJSONは`request.data`で取得できます。

```python
transfer_amount = request.data.get("transfer_amount")
message = request.data.get("message", "")
```

## 5. Django ORMとSQLiteの関係

`models.py`の`Account`クラスはSQLiteの`accounts`テーブル、`Transaction`クラスは`transactions`テーブルに対応します。

```text
Python                                         SQLite
Account.objects.get(account_number="1000001") → SELECT ... FROM accounts ...
sender.save()                                  → UPDATE accounts ...
Transaction.objects.create(...)                → INSERT INTO transactions ...
```

DjangoがPythonコードをSQLへ変換するため、通常のAPI実装ではSQLを直接書く必要がありません。

主なORM処理は次のとおりです。

| ORMコード | DBで起きること |
|---|---|
| `Account.objects.get(...)` | 条件に一致する口座を1件取得 |
| `Account.objects.exclude(...)` | 指定口座以外を一覧取得 |
| `sender.save(update_fields=[...])` | 送金元の残高だけを更新 |
| `Transaction.objects.create(...)` | 新しい送金履歴を登録 |

## 6. 各画面とAPIの流れ

### 6.1 トップ画面

1. `TopScreen.js`が`getUserSummary("1000001")`を呼ぶ
2. `UserSummaryView`が`accounts`から口座を検索する
3. ユーザー名・口座番号・残高をJSONで返す
4. ReactがJSONをstateへ保存して表示する

### 6.2 送金先一覧

1. 「送金する」を押す
2. `SelectSendMoney.js`が`getRecipientList("1000001")`を呼ぶ
3. `RecipientListView`が送金元以外のAccountを取得する
4. Reactが取得した配列を`map()`して一覧表示する

### 6.3 送金処理画面

1. 一覧から送金先を選ぶ
2. `ProcessSendMoney.js`が`getRecipientInfo()`を呼ぶ
3. `RecipientInfoView`が送金元残高と送金先情報を取得する
4. Reactが送金上限額と送金先名を表示する

### 6.4 送金ボタン

Reactは次のJSONをPOSTします。

```json
{
  "transfer_amount": 3000,
  "message": "昼食代"
}
```

`TransferView.post()`は次の順番で処理します。

1. `transfer_amount`と`message`を`request.data`から取得
2. 金額が1以上の整数か確認
3. 送金元と送金先が別口座か確認
4. メッセージが200文字以内か確認
5. `transaction.atomic()`を開始
6. 送金元と送金先をDBから取得してロック
7. 残高不足でないか確認
8. 送金元残高から金額を引く
9. 送金先残高へ金額を足す
10. `transactions`へ送金履歴を追加
11. 全処理が成功したら確定
12. 取引番号と更新後残高をJSONでReactへ返す

## 7. なぜ`transaction.atomic()`が必要か

送金では最低でも3つのDB更新が必要です。

```text
送金元 -3,000円
送金先 +3,000円
送金履歴を追加
```

履歴登録だけ失敗した場合に残高更新だけが残ると、帳尻が合わなくなります。`transaction.atomic()`で囲むと、途中のどこかで例外が起きた場合、3つの変更をすべて取り消せます。

```text
全処理成功 → COMMIT（すべて確定）
途中で失敗 → ROLLBACK（すべて取り消し）
```

`select_for_update()`は、同じ口座に複数の送金が同時に届いたときの競合を抑えるために使用しています。SQLiteでは書き込み時にDB単位のロックになりますが、将来ほかのDBへ移行した場合にも意図が分かる実装です。

## 8. モデルとDB制約による二重チェック

APIの入力チェックだけでなく、DBにも次の制約があります。

- 口座残高は0以上
- 送金金額は1以上
- 送金元と送金先は別口座
- 取引から参照されている口座は削除しない

APIで不正値を早く発見し、最後にDB制約でも不整合を防ぐ二重構造です。

## 9. JSONレスポンスとHTTPステータス

Django REST Frameworkの`Response`へPythonの辞書を渡すと、自動的にJSONへ変換されます。

```python
return Response(
    {"account_number": "1000001", "account_balance": 97000},
    status=status.HTTP_200_OK,
)
```

Reactの`src/api/user.js`は`response.ok`を確認し、成功ならJSONを返し、失敗なら画面へ表示するエラーを生成します。

| ステータス | 意味 | 例 |
|---|---|---|
| 200 | 成功 | 口座取得、送金成功 |
| 400 | 入力が不正 | 0円送金、残高不足、自分宛て送金 |
| 404 | データがない | 存在しない口座番号 |
| 500 | サーバー内部エラー | 想定外のDB障害など |

## 10. CORSとは

Reactは`localhost:3000`、Djangoは`127.0.0.1:8000`で動くため、ブラウザから見ると別の接続先です。`settings.py`の`CORS_ALLOWED_ORIGINS`でReact開発サーバーからのAPIアクセスを許可しています。

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

CORSエラーが発生した場合、Reactを開いているURLがこの一覧に含まれているか確認します。本番環境では実際のフロントエンドURLだけを許可してください。

## 11. 動作確認

### サーバーを起動

ターミナル1：

```bash
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py seed_mock_data
python manage.py runserver
```

ターミナル2：

```bash
npm start
```

ブラウザで`http://localhost:3000`を開き、送金完了まで操作します。Djangoを起動したターミナルには、呼ばれたAPIとHTTPステータスが表示されます。

### APIだけ確認

```bash
curl http://127.0.0.1:8000/api/user/1000001/summary
curl http://127.0.0.1:8000/api/user/1000001/recipient_list
```

### DBを確認

`http://127.0.0.1:8000/admin/`でAccountsとTransactionsを確認します。

### 自動テスト

```bash
cd backend
source venv/bin/activate
python manage.py test api
```

APIテストは、HTTPリクエスト、レスポンス、残高更新、履歴作成、エラー時にDBが変更されないことまで確認します。テスト専用DBを使用するため、ローカルの`db.sqlite3`は変更しません。

## 12. APIを変更するときの確認場所

APIを追加・変更するときは、次の順番で確認すると漏れを防げます。

1. `api/models.py`: 新しいデータ項目やテーブルが必要か
2. `api/migrations/`: モデル変更時にマイグレーションを作成したか
3. `api/views.py`: 入力検証、ORM処理、レスポンスを実装したか
4. `api/urls.py`: Viewへ到達するURLを追加したか
5. `api/tests.py`: 正常系と異常系を追加したか
6. `src/api/user.js`: React側のAPI関数を追加したか
7. React画面: 読み込み中、成功、エラーを表示できるか
8. API仕様書とこのガイドを更新したか

コード内の連携箇所は次のコマンドで探せます。

```bash
rg -n "API連携ポイント|DB操作" src backend/api
```
