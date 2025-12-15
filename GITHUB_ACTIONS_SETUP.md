# GitHub Actions セットアップガイド

毎朝9時（日本時間）にScirate Discord Botを自動実行する設定です。

## 必要なもの

1. **GitHubアカウント**（無料）
2. **Discord Webhook URL**
3. **Google Gemini API Key**（無料枠あり）

所要時間：約10分

---

## ステップ1: GitHubアカウントを作成

### すでにアカウントがある場合
→ ステップ2へ進む

### 新規作成する場合
1. https://github.com/ にアクセス
2. 「Sign up」をクリック
3. メールアドレス、パスワードを入力
4. 認証を完了

---

## ステップ2: 新しいリポジトリを作成

1. GitHubにログイン
2. 右上の「+」→「New repository」をクリック

3. リポジトリ設定：
   - **Repository name**: `scirate-discord-bot`
   - **Description**: `Scirate論文の自動投稿bot`
   - **Public** または **Private**（どちらでもOK）
   - ✅ **Add a README file** にチェック
   - 「Create repository」をクリック

---

## ステップ3: ファイルをアップロード

### 方法A: Web UIで直接アップロード（簡単）

1. リポジトリのページで「Add file」→「Upload files」

2. 以下のファイルをドラッグ&ドロップ：
   - `scirate_discord_bot.py`
   - `requirements.txt`

3. 「Commit changes」をクリック

4. **ワークフローファイルを作成**：
   - リポジトリのページで「Add file」→「Create new file」
   - ファイル名に `.github/workflows/scirate_bot.yml` と入力
   - 以下の内容を貼り付け：

```yaml
name: Scirate Discord Bot

on:
  schedule:
    # 毎日午前9時（日本時間）= 毎日午前0時（UTC）
    - cron: '0 0 * * *'
  
  # 手動実行も可能にする
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest
    
    steps:
    - name: リポジトリをチェックアウト
      uses: actions/checkout@v3
    
    - name: Pythonをセットアップ
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: 依存関係をインストール
      run: |
        pip install requests beautifulsoup4 google-generativeai

    - name: Scirate Botを実行
      env:
        DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        python scirate_discord_bot.py
```

5. 「Commit changes」をクリック

### 方法B: Gitコマンドを使う（上級者向け）

```bash
cd ~/scirate_bot/files

# Gitリポジトリを初期化
git init
git add scirate_discord_bot.py requirements.txt
git add .github/workflows/scirate_bot.yml
git commit -m "Initial commit"

# GitHubリポジトリに接続
git remote add origin https://github.com/あなたのユーザー名/scirate-discord-bot.git
git branch -M main
git push -u origin main
```

---

## ステップ4: Secrets（シークレット）を設定

### 重要：APIキーとWebhook URLを安全に保存

1. リポジトリのページで「Settings」タブをクリック

2. 左サイドバーから「Secrets and variables」→「Actions」をクリック

3. 「New repository secret」をクリック

4. **1つ目のSecret**：
   - **Name**: `DISCORD_WEBHOOK_URL`
   - **Secret**: あなたのDiscord Webhook URL
   - 「Add secret」をクリック

5. **2つ目のSecret**：
   - 「New repository secret」をクリック
   - **Name**: `GEMINI_API_KEY`
   - **Secret**: あなたのGoogle Gemini APIキー（https://aistudio.google.com/ で取得）
   - 「Add secret」をクリック

---

## ステップ5: テスト実行

### 手動で実行してテスト

1. リポジトリのページで「Actions」タブをクリック

2. 左サイドバーから「Scirate Discord Bot」をクリック

3. 右側の「Run workflow」→「Run workflow」をクリック

4. 数分待つと実行が完了

5. Discordを確認 → 論文が投稿されていればOK！✅

### エラーが出た場合

1. ワークフローの実行ログをクリック
2. エラーメッセージを確認
3. Secretsが正しく設定されているか確認

---

## ✅ 完了！

設定が完了しました！

### 自動実行スケジュール

- **毎日午前9時（日本時間）**に自動実行されます
- GitHub Actionsが自動的に実行します
- PCの電源は不要です

### 確認方法

明日の朝9時以降にDiscordを確認してください。

### 手動実行

いつでも「Actions」→「Run workflow」で手動実行できます。

---

## 🔧 カスタマイズ

### 実行時刻を変更

`.github/workflows/scirate_bot.yml` の cron 式を編集：

```yaml
# 毎日午前9時（JST）= 午前0時（UTC）
- cron: '0 0 * * *'

# 毎日午後6時（JST）= 午前9時（UTC）
- cron: '0 9 * * *'

# 毎日午前9時と午後6時（JST）
- cron: '0 0,9 * * *'
```

### 投稿数を変更

`scirate_discord_bot.py` の以下の行を編集：

```python
TOP_N_PAPERS = 10  # 5や20に変更可能
```

---

## 📊 料金

**完全無料**です！

- GitHub Actions: 月2000分まで無料
- このbotは1回2分程度なので、月60分程度
- 十分に無料枠内です

---

## 🐛 トラブルシューティング

### ワークフローが実行されない

1. 「Actions」タブで「Enable workflows」をクリック
2. Secretsが正しく設定されているか確認

### Discordに投稿されない

1. Actions のログを確認
2. Discord Webhook URLが正しいか確認
3. 手動実行でテスト

### 時刻がずれている

cronはUTCで設定されます：
- JST 9:00 = UTC 0:00
- JST 18:00 = UTC 9:00

---

## 🎉 完成！

これでPCの電源に関係なく、毎朝9時に自動投稿されます！

楽しんでください！📊✨
