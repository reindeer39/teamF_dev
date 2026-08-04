# teamF_dev

チーム開発用のリポジトリです。フロントエンド(React)とバックエンド(Django)で構成されています。

## 目次

- [構成](#構成)
- [セットアップ](#セットアップ)
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
python manage.py runserver
```

`http://localhost:8000` で起動します。React 開発サーバー(`localhost:3000`)からのアクセスは CORS 許可済みです。

## Git運用ルール

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

1. 作業ブランチを push し、`main` 宛てにPRを作成する
2. PRの説明に変更内容と確認方法(動作確認手順)を書く
3. **レビュー1名以上の承認**を必須とする
4. マージ方法は **Squash and merge** に統一する
5. マージ後、不要になったブランチは削除する

### 禁止事項

- `main` への直接push
- `--force` push(自分だけの作業ブランチを除く)
- レビューなしでのマージ
- コンフリクトを解消せずにマージ依頼を出す
