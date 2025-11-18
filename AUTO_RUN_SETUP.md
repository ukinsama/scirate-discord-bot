# 自動実行設定ガイド（毎朝9時）

## 📅 自動実行の設定方法

毎朝9時にbotを自動実行する設定を行います。

---

## ステップ1: 実行用シェルスクリプトを作成

以下の内容で `run_bot.sh` を作成します：

```bash
#!/bin/bash

# scirate_botディレクトリに移動
cd /home/ks/scirate_bot/files

# 仮想環境を有効化
source /home/ks/scirate_bot/new_venv/bin/activate

# botを実行
python scirate_discord_bot.py

# 仮想環境を無効化
deactivate
```

### コマンドで作成：

```bash
cd ~/scirate_bot/files

cat > run_bot.sh << 'EOF'
#!/bin/bash
cd /home/ks/scirate_bot/files
source /home/ks/scirate_bot/new_venv/bin/activate
python scirate_discord_bot.py
deactivate
EOF

chmod +x run_bot.sh
```

---

## ステップ2: cronに登録

```bash
# crontabを編集
crontab -e
```

エディタが開くので、以下を追加：

```bash
# 毎日午前9時にScirate Discord Botを実行
0 9 * * * /home/ks/scirate_bot/files/run_bot.sh >> /home/ks/scirate_bot/bot.log 2>&1
```

保存して終了（viの場合：`Esc`→`:wq`→`Enter`）

---

## ステップ3: 設定確認

crontabが正しく登録されたか確認：

```bash
crontab -l
```

以下のように表示されればOK：

```
0 9 * * * /home/ks/scirate_bot/files/run_bot.sh >> /home/ks/scirate_bot/bot.log 2>&1
```

---

## 📋 cronの時刻設定について

cronの書式：`分 時 日 月 曜日 コマンド`

**例**：

```bash
# 毎日午前9時
0 9 * * * /path/to/script.sh

# 毎日午前9時と午後6時
0 9,18 * * * /path/to/script.sh

# 月曜から金曜の午前9時（平日のみ）
0 9 * * 1-5 /path/to/script.sh

# 毎時0分（1時間ごと）
0 * * * * /path/to/script.sh
```

---

## 🔍 ログの確認

実行ログは `/home/ks/scirate_bot/bot.log` に保存されます。

```bash
# ログを確認
cat ~/scirate_bot/bot.log

# リアルタイムでログを監視
tail -f ~/scirate_bot/bot.log

# 最新の50行を表示
tail -50 ~/scirate_bot/bot.log
```

---

## 🧪 手動テスト

cronに登録する前に、スクリプトが正しく動作するかテスト：

```bash
cd ~/scirate_bot/files
./run_bot.sh
```

正常に実行されたら、cron設定を行います。

---

## ⚠️ トラブルシューティング

### 実行されない場合

1. **パスを絶対パスに変更**
   ```bash
   # 相対パス → 絶対パス
   which python  # Pythonのパスを確認
   ```

2. **実行権限を確認**
   ```bash
   chmod +x /home/ks/scirate_bot/files/run_bot.sh
   ```

3. **cronのログを確認**
   ```bash
   grep CRON /var/log/syslog
   ```

4. **手動実行でテスト**
   ```bash
   /home/ks/scirate_bot/files/run_bot.sh
   ```

### ログに何も出力されない場合

`run_bot.sh`に以下を追加してデバッグ：

```bash
#!/bin/bash
echo "Bot started at $(date)" >> /home/ks/scirate_bot/bot.log
cd /home/ks/scirate_bot/files
source /home/ks/scirate_bot/new_venv/bin/activate
python scirate_discord_bot.py
deactivate
echo "Bot finished at $(date)" >> /home/ks/scirate_bot/bot.log
```

---

## 📊 実行時間の目安

- Scirateからの取得: 約5秒
- arXiv API（10件）: 約15秒
- AI要約生成（10件）: 約60秒
- Discord投稿（10件）: 約30秒

**合計: 約2分**

---

## 🎯 完了！

設定が完了したら、明朝9時に自動実行されます。

初回は手動実行でテストすることをお勧めします：

```bash
cd ~/scirate_bot/files
./run_bot.sh
```

問題なければ、明日の朝9時に自動投稿されます！🎉
