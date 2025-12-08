#!/usr/bin/env python3
"""
Scirate Discord Bot - テスト用スクリプト
Discordに投稿せず、ターミナルで動作確認するためのスクリプト

使い方:
  GEMINI_API_KEY="あなたのAPIキー" python test_bot.py
"""

import os
import sys

# メインスクリプトから関数をインポート
from scirate_discord_bot import (
    get_top_papers_from_scirate,
    enrich_papers_with_abstracts,
    generate_summary,
    ARXIV_CATEGORY,
    SUMMARY_LANGUAGE,
)

# テスト用の論文数（少なめに）
TEST_PAPER_COUNT = 2


def main():
    print("=" * 60)
    print("🧪 Scirate Discord Bot - テストモード")
    print("=" * 60)

    # APIキー確認
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_key:
        print("❌ GEMINI_API_KEY が設定されていません")
        print("使い方: GEMINI_API_KEY=\"あなたのキー\" python test_bot.py")
        sys.exit(1)
    print(f"✅ GEMINI_API_KEY: 設定済み")

    # 1. 論文取得
    print(f"\n📚 論文を{TEST_PAPER_COUNT}件取得中...")
    papers = get_top_papers_from_scirate(ARXIV_CATEGORY, TEST_PAPER_COUNT)

    if not papers:
        print("❌ 論文が見つかりませんでした")
        sys.exit(1)

    # 2. Abstract取得
    print(f"\n📖 Abstract取得中...")
    papers = enrich_papers_with_abstracts(papers)

    # 3. 要約生成とターミナル出力
    print("\n" + "=" * 60)
    print("📝 要約生成結果")
    print("=" * 60)

    for i, paper in enumerate(papers, 1):
        print(f"\n{'─' * 60}")
        print(f"【{i}】{paper['title']}")
        print(f"{'─' * 60}")
        print(f"📎 arXiv: {paper['arxiv_id']}")
        print(f"⭐ Scites: {paper['scites']}")
        print(f"👥 著者: {', '.join(paper['authors'][:3])}" + (" et al." if len(paper['authors']) > 3 else ""))
        print(f"🔗 URL: {paper['url']}")

        # 要約生成
        print(f"\n🤖 要約生成中...")
        summary = generate_summary(paper['title'], paper.get('abstract', ''), SUMMARY_LANGUAGE)
        print(f"\n📝 要約:\n{summary}")

    print("\n" + "=" * 60)
    print("✅ テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
