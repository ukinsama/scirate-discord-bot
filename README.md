# Scirate Discord Bot 📊

quant-phカテゴリの**scites数上位10件の論文**をAI要約付きでDiscordに自動投稿するbotです。

## 🎯 機能

- **arXiv最新論文取得**: quant-phカテゴリから最新論文を取得
- **Scites数取得**: Scirateトップページから直接scites数順の論文を取得
- **自動ソート**: scites数順に並んだ上位10件を選択
- **AI要約生成**: Claude APIで各論文を2-3文で簡潔に要約
- **Discord投稿**: 綺麗なEmbed形式でDiscordに自動投稿
- **🔗 SciRateリンク**: 投稿の最上部にSciRateの直リンク（https://scirate.com/?range=1）を表示
- **⏰ 自動実行**: 毎朝9時に自動実行（cron設定）

## 📋 必要なもの

1. **Python 3.8以上**
2. **Discord Webhook URL**（設定済み✅）
3. **Anthropic API Key**（設定済み✅）

## 🚀 セットアップ

### 1. Python環境の確認

```bash
python --version
# または
python3 --version
```

Python 3.8以上がインストールされていることを確認してください。

### 2. 必要なパッケージのインストール

```bash
pip install requests beautifulsoup4
# または
pip3 install requests beautifulsoup4
```

または、requirements.txtを使用：
```bash
pip install -r requirements.txt
# または
pip3 install -r requirements.txt
```

### 3. スクリプトの実行

```bash
python scirate_discord_bot.py
# または
python3 scirate_discord_bot.py
```

## ⚙️ カスタマイズ

スクリプトの冒頭部分で設定を変更できます：

```python
# ===== 設定（ここを編集してください） =====
ARXIV_CATEGORY = "quant-ph"  # 変更可能: cs.AI, cs.LG など
TOP_N_PAPERS = 10  # 投稿する論文数
SUMMARY_LANGUAGE = "ja"  # 要約言語 (ja=日本語, en=英語)
```

### 利用可能なarXivカテゴリ例

- `quant-ph`: 量子物理
- `cs.AI`: 人工知能
- `cs.LG`: 機械学習
- `cs.CL`: 計算言語学
- `math.CO`: 組合せ論
- `hep-th`: 高エネルギー物理理論

## ⏰ 自動実行の設定（毎朝9時）

### 🚀 簡単セットアップ（推奨）

1. すべてのファイルを同じフォルダに配置
2. 以下のコマンドを実行：

```bash
chmod +x setup_auto_run.sh
./setup_auto_run.sh
```

対話形式で自動設定が完了します！

### 📝 手動セットアップ（Linux/Ubuntu）

詳しくは [AUTO_RUN_SETUP.md](AUTO_RUN_SETUP.md) を参照してください。

**基本手順**：

```bash
# 1. 実行スクリプトに権限を付与
chmod +x run_bot.sh

# 2. cronに登録
crontab -e

# 3. 以下を追加（パスは適宜変更）
0 9 * * * /home/ks/scirate_bot/files/run_bot.sh >> /home/ks/scirate_bot/bot.log 2>&1
```

保存すれば、**毎朝9時に自動実行**されます。

### Windows（タスクスケジューラ）

1. タスクスケジューラを開く
2. 「基本タスクの作成」を選択
3. トリガー：毎日、午前9時を設定
4. 操作：プログラムの開始
5. プログラム：`python` または `python3`
6. 引数：`C:\path\to\scirate_discord_bot.py`

### ログの確認

```bash
# ログを確認
tail -f ~/scirate_bot/bot.log

# 最新の50行を表示
tail -50 ~/scirate_bot/bot.log
```

## 📝 実行例

```
============================================================
🚀 Scirate Discord Bot 起動 (最終版)
============================================================
📚 Scirate quant-phカテゴリのトップページから論文を取得中...
🔍 50件の論文を発見
✅ 50件の論文を取得しました

📊 Scites数上位10件:
  1. [ 45 scites] 2511.13560 - Sequences of Bivariate Bicycle Codes...
  2. [ 38 scites] 2511.xxxxx - Novel Approach to Quantum State Tomography...
  3. [ 32 scites] 2511.xxxxx - Entanglement Dynamics in Many-Body Systems...
  4. [ 28 scites] 2511.xxxxx - Quantum Algorithms for Machine Learning...
  5. [ 25 scites] 2511.xxxxx - Topological Phases in Quantum Systems...
  6. [ 22 scites] 2511.xxxxx - ...
  7. [ 19 scites] 2511.xxxxx - ...
  8. [ 16 scites] 2511.xxxxx - ...
  9. [ 14 scites] 2511.xxxxx - ...
  10. [ 12 scites] 2511.xxxxx - ...

📋 投稿する論文（Top 10）:
  1. [45 scites] 2511.13560 - ...
  ...

📖 各論文の詳細情報を取得中...
   [1/10] 2511.13560 の情報を取得中...
   ...
✅ 詳細情報取得完了

📤 Discordに投稿中...
🤖 要約生成中: Sequences of Bivariate Bicycle Codes...
✅ 1件目を投稿しました: Sequences of Bivariate Bicycle Codes...
...

🎉 完了！10件の論文をDiscordに投稿しました
```

**Discordでの表示例**：

```
## 📊 2025年11月19日 の quant-ph 人気論文 Top 10

🔗 **SciRate**: https://scirate.com/?range=1

1. Sequences of Bivariate Bicycle Codes from Covering Graphs
   📝 要約: この研究では...
   👥 著者: Benjamin C. B. Symons, Abhishek Rajput, Dan E. Browne
   ⭐ Scites: 45
   🔗 リンク: arXiv | SciRate

2. [2番目の論文]
...
```

============================================================
✨ すべての処理が完了しました！
============================================================
```

## ⚠️ 注意事項

1. **API制限**: Anthropic APIには無料枠があります。大量実行する場合は料金に注意してください。
2. **Discordレート制限**: 短時間に大量投稿すると制限される可能性があります。
3. **arXivのマナー**: 頻繁にアクセスしすぎないようにしてください（1日数回程度推奨）。
4. **Scirateへのアクセス**: このbotはscirateから情報を取得します。過度な実行（1日に何度も実行など）は避けてください。スクリプトは自動的に3秒間隔でアクセスするよう設定されていますが、**1日1-2回の実行を推奨**します。

## 🐛 トラブルシューティング

### `ModuleNotFoundError: No module named 'requests'` または `'bs4'`

```bash
pip install requests beautifulsoup4
# または仮想環境内で
source venv/bin/activate
pip install -r requirements.txt
```

### Discord投稿が失敗する

- Webhook URLが正しいか確認
- Webhookが削除されていないか確認

### 要約生成が失敗する

- Anthropic API Keyが正しいか確認
- APIクレジットが残っているか確認（https://console.anthropic.com/）

### 論文が取得できない

- インターネット接続を確認
- arXiv APIが稼働しているか確認（https://arxiv.org/）

### scites数が全て0になる

- scirateのHTML構造が変更された可能性があります
- 実際にscirateで論文を確認して、scites数が表示されているか確認
- それでも問題がある場合は、scirateのページ構造が変わった可能性があります

## 📧 サポート

問題が発生した場合は、エラーメッセージを確認して対処してください。

## 📄 ライセンス

MIT License - 自由に使用・改変できます

---

**作成日**: 2025年11月18日
**バージョン**: 1.0
