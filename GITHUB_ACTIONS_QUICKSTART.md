# GitHub Actions クイックスタート ✅

## 📋 チェックリスト

### ステップ1: GitHubアカウント
- [ ] GitHubアカウントを作成（または既存アカウントでログイン）
- [ ] https://github.com にアクセス

### ステップ2: リポジトリ作成
- [ ] 新しいリポジトリを作成
- [ ] 名前: `scirate-discord-bot`
- [ ] Public または Private を選択
- [ ] READMEを追加にチェック

### ステップ3: ファイルをアップロード
- [ ] `scirate_discord_bot.py` をアップロード
- [ ] `requirements.txt` をアップロード
- [ ] `.github/workflows/scirate_bot.yml` を作成

### ステップ4: Secretsを設定
- [ ] Settings → Secrets and variables → Actions
- [ ] `DISCORD_WEBHOOK_URL` を追加
- [ ] `ANTHROPIC_API_KEY` を追加

### ステップ5: テスト実行
- [ ] Actions タブを開く
- [ ] 「Run workflow」で手動実行
- [ ] Discordで論文投稿を確認

### 完了！
- [ ] 明朝9時の自動実行を待つ

---

## 🚀 必要なファイル

以下の3つのファイルをGitHubにアップロード：

1. **scirate_discord_bot.py** (メインスクリプト)
2. **requirements.txt** (依存パッケージ)
3. **.github/workflows/scirate_bot.yml** (ワークフロー設定)

---

## 🔑 必要なSecrets

以下の2つをGitHub Secretsに設定：

1. **DISCORD_WEBHOOK_URL**
   ```
   https://discordapp.com/api/webhooks/1440300959053119538/uMebZxptK0QGMDrGnicpomGxeil_dSUofXY_H10bUdst1utNlPaAI1rHeTEfCXf1ki7s
   ```

2. **ANTHROPIC_API_KEY**
   ```
   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
   ```

---

## ⏰ 実行スケジュール

- **毎日午前9時（日本時間）**
- PCの電源不要
- 完全自動

---

## 📖 詳しい手順

詳細は **GITHUB_ACTIONS_SETUP.md** を参照してください。

---

## 所要時間

**約10分で完了**します！
