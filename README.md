# Scirate Discord Bot

quant-phカテゴリの**scites数上位論文**をAI要約付きでDiscordに自動投稿するbotです。

## 機能

- **arXiv最新論文取得**: quant-phカテゴリから最新論文を取得
- **Scites数取得**: Scirateトップページから直接scites数順の論文を取得
- **自動ソート**: scites数順に並んだ上位8件を選択
- **AI要約生成**: Google Gemini APIで各論文を2-3文で簡潔に要約
- **Discord投稿**: 綺麗なEmbed形式でDiscordに自動投稿
- **SciRateリンク**: 投稿の最上部にSciRateの直リンクを表示
- **自動実行**: GitHub Actionsで毎朝9時（JST）に自動実行
- **キャッシュ機能**: API呼び出し削減のためのキャッシュ
- **レート制限対策**: インテリジェントなRPM制限対応

## 必要なもの

1. **Python 3.8以上**
2. **Discord Webhook URL**
3. **Google Gemini API Key**（無料枠あり）

## セットアップ

### 1. Python環境の確認

```bash
python --version  # Python 3.8以上
```

### 2. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
export DISCORD_WEBHOOK_URL="your_webhook_url"
export GEMINI_API_KEY="your_gemini_api_key"
```

### 4. スクリプトの実行

```bash
python scirate_discord_bot.py
```

## カスタマイズ

スクリプトの冒頭部分で設定を変更できます：

```python
ARXIV_CATEGORY = "quant-ph"  # 変更可能: cs.AI, cs.LG など
TOP_N_PAPERS = 8  # 投稿する論文数
SUMMARY_LANGUAGE = "ja"  # 要約言語 (ja=日本語, en=英語)
```

### 利用可能なarXivカテゴリ例

- `quant-ph`: 量子物理
- `cs.AI`: 人工知能
- `cs.LG`: 機械学習
- `cs.CL`: 計算言語学
- `math.CO`: 組合せ論
- `hep-th`: 高エネルギー物理理論

## 自動実行（GitHub Actions）

GitHub Actionsで毎朝9時（JST）に自動実行されます。

### 必要なSecrets設定

GitHubリポジトリの Settings > Secrets and variables > Actions で以下を設定：

| Secret名 | 内容 |
|----------|------|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL |
| `GEMINI_API_KEY` | Google Gemini APIキー |

### 手動実行

Actions タブから「Run workflow」で手動実行も可能です。

### ローカルでの自動実行（cron）

```bash
# cronに登録
crontab -e

# 以下を追加（毎朝9時に実行）
0 9 * * * cd /path/to/scirate_bot && python scirate_discord_bot.py >> bot.log 2>&1
```

## 実行例

```
Scirate Discord Bot 起動 (Gemini API 改善版)
キャッシュ: 5件のエントリ
Scirate quant-phカテゴリのトップページから論文を取得中...
50件の論文を発見
投稿する論文（Top 8）:
  1. [45 scites] 2512.xxxxx - ...
...
Discordに投稿中...
Using model: gemini-2.5-flash-lite (RPM: 10)
完了！8件の論文をDiscordに投稿しました
```

## 注意事項

1. **Gemini API制限**: 無料枠があります（RPM/RPD制限）。キャッシュ機能で節約しています。
2. **Discordレート制限**: 短時間に大量投稿すると制限される可能性があります。
3. **arXiv/Scirateへのアクセス**: 1日1-2回の実行を推奨します。

## トラブルシューティング

### ModuleNotFoundError

```bash
pip install requests beautifulsoup4 google-generativeai
```

### Discord投稿が失敗する

- Webhook URLが正しいか確認
- Webhookが削除されていないか確認

### 要約生成が失敗する

- Gemini API Keyが正しいか確認
- https://aistudio.google.com/ でAPI状況を確認

### 論文が取得できない

- インターネット接続を確認
- Scirate/arXivが稼働しているか確認

## ライセンス

MIT License
