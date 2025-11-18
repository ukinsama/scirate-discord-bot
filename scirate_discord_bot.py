#!/usr/bin/env python3
"""
Scirate Discord Bot (完全版)
Scirateのquant-phトップページから、scites数上位10件の論文をAI要約付きでDiscordに投稿

使い方:
1. 必要なパッケージをインストール: pip install requests beautifulsoup4
2. このスクリプトを実行: python scirate_discord_bot.py
"""

import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import List, Dict
import re
import os

# ===== 設定（ここを編集してください） =====
# 環境変数から取得（GitHub Actions用）、なければデフォルト値を使用
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', "https://discordapp.com/api/webhooks/1440300959053119538/uMebZxptK0QGMDrGnicpomGxeil_dSUofXY_H10bUdst1utNlPaAI1rHeTEfCXf1ki7s")
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', "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")
ARXIV_CATEGORY = "quant-ph"  # カテゴリ (quant-ph, cs.AI, cs.LG など)
TOP_N_PAPERS = 10  # 投稿する論文数
SUMMARY_LANGUAGE = "ja"  # 要約言語 (ja=日本語, en=英語)


# ===== Scirateトップページから論文を取得 =====
def get_top_papers_from_scirate(category: str, top_n: int = 10) -> List[Dict]:
    """
    Scirateのトップページから、scites順の論文を取得
    """
    print(f"📚 Scirate {category}カテゴリのトップページから論文を取得中...")
    
    url = f"https://scirate.com/arxiv/{category}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ エラー: Scirateからの取得に失敗 (status: {response.status_code})")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        papers = []
        
        # paperlist → ul.papers を探す
        paperlist = soup.find('div', class_='paperlist')
        
        if not paperlist:
            print("❌ エラー: paperlist要素が見つかりません")
            return []
        
        papers_ul = paperlist.find('ul', class_='papers')
        
        if not papers_ul:
            print("❌ エラー: ul.papers要素が見つかりません")
            return []
        
        # 各論文要素（div.row）を取得
        paper_rows = papers_ul.find_all('div', class_='row')
        
        print(f"🔍 {len(paper_rows)}件の論文を発見")
        
        for paper_row in paper_rows:
            try:
                # arXiv IDを取得（div.uid内）
                uid_elem = paper_row.find('div', class_='uid')
                if not uid_elem:
                    continue
                
                uid_text = uid_elem.get_text(strip=True)
                # arXiv IDを抽出（例：arXiv:2511.13560v1 → 2511.13560）
                arxiv_match = re.search(r'arXiv:(\d{4}\.\d{4,5})', uid_text)
                if not arxiv_match:
                    continue
                
                arxiv_id = arxiv_match.group(1)
                
                # タイトルを取得
                title_elem = paper_row.find('div', class_='title')
                if title_elem:
                    title_link = title_elem.find('a')
                    title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
                else:
                    title = "タイトル不明"
                
                # Scites数を取得
                scites = 0
                scites_count_div = paper_row.find('div', class_='scites-count')
                if scites_count_div:
                    # scites-count div内のbuttonを探す
                    count_button = scites_count_div.find('button', class_='count')
                    if count_button:
                        scites_text = count_button.get_text(strip=True)
                        try:
                            scites = int(scites_text)
                        except ValueError:
                            scites = 0
                
                # 著者を取得
                authors = []
                authors_elem = paper_row.find('div', class_='authors')
                if authors_elem:
                    # 著者リンクを取得
                    author_links = authors_elem.find_all('a')
                    for link in author_links:
                        author_name = link.get_text(strip=True).rstrip(',')
                        if author_name:
                            authors.append(author_name)
                
                papers.append({
                    'arxiv_id': arxiv_id,
                    'title': title,
                    'scites': scites,
                    'authors': authors,
                    'url': f"https://arxiv.org/abs/{arxiv_id}",
                    'scirate_url': f"https://scirate.com/arxiv/{arxiv_id}",
                    'abstract': None
                })
            
            except Exception as e:
                print(f"⚠️ 論文の解析エラー: {e}")
                continue
        
        # Scites順にソート（降順）
        papers.sort(key=lambda x: x['scites'], reverse=True)
        
        print(f"✅ {len(papers)}件の論文を取得しました")
        
        # 上位10件を表示
        if papers:
            print(f"\n📊 Scites数上位{min(10, len(papers))}件:")
            for i, paper in enumerate(papers[:10], 1):
                print(f"  {i}. [{paper['scites']:3d} scites] {paper['arxiv_id']} - {paper['title'][:50]}...")
        
        return papers[:top_n]
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return []


# ===== 論文の詳細情報を補完 =====
def enrich_papers_with_abstracts(papers: List[Dict]) -> List[Dict]:
    """
    各論文のAbstractをarXiv APIから取得
    """
    print(f"\n📖 各論文の詳細情報を取得中...")
    
    for i, paper in enumerate(papers, 1):
        print(f"   [{i}/{len(papers)}] {paper['arxiv_id']} の情報を取得中...")
        
        # arXiv APIから詳細情報を取得
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "id_list": paper['arxiv_id'],
            "max_results": 1
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ScirateBot/1.0)'
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                entry = root.find('atom:entry', ns)
                if entry:
                    # Abstract
                    abstract_elem = entry.find('atom:summary', ns)
                    if abstract_elem is not None:
                        paper['abstract'] = abstract_elem.text.strip().replace('\n', ' ')
                    
                    # タイトル（Scirateから正しく取れなかった場合）
                    if paper['title'] == "タイトル不明":
                        title_elem = entry.find('atom:title', ns)
                        if title_elem is not None:
                            paper['title'] = title_elem.text.strip().replace('\n', ' ')
                    
                    # 著者（Scirateから取れなかった場合）
                    if not paper['authors']:
                        authors = []
                        for author in entry.findall('atom:author', ns):
                            name = author.find('atom:name', ns)
                            if name is not None:
                                authors.append(name.text)
                        paper['authors'] = authors
        
        except Exception as e:
            print(f"⚠️ エラー: {e}")
        
        time.sleep(1)  # arXiv APIへの負荷を避ける
    
    print("✅ 詳細情報取得完了")
    return papers


# ===== Claude APIで要約を生成 =====
def generate_summary(title: str, abstract: str, language: str = "ja") -> str:
    """
    Claude APIを使って論文を2-3文で要約
    """
    print(f"🤖 要約生成中: {title[:40]}...")
    
    if not abstract:
        return "Abstractが取得できませんでした。"
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    if language == "ja":
        prompt = f"""以下の論文を2-3文の日本語で簡潔に要約してください。専門用語は残しつつ、何を研究したかが分かるように説明してください。

タイトル: {title}

要旨: {abstract}

要約:"""
    else:
        prompt = f"""Summarize the following paper in 2-3 sentences. Keep technical terms and explain what was studied.

Title: {title}

Abstract: {abstract}

Summary:"""
    
    data = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 300,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            summary = result['content'][0]['text'].strip()
            return summary
        else:
            print(f"⚠️ 要約生成エラー (status: {response.status_code})")
            return "要約の生成に失敗しました。"
    
    except Exception as e:
        print(f"⚠️ 要約生成エラー: {e}")
        return "要約の生成に失敗しました。"


# ===== Discordに投稿 =====
def post_to_discord(papers: List[Dict], language: str = "ja"):
    """
    論文リストをDiscordに投稿
    """
    print(f"\n📤 Discordに投稿中...")
    
    # ヘッダーメッセージ（SciRateのURLを含む）
    today_str = datetime.now().strftime("%Y年%m月%d日")
    if language == "ja":
        header = f"## 📊 {today_str} の quant-ph 人気論文 Top {len(papers)}\n\n🔗 **SciRate**: https://scirate.com/?range=1\n"
    else:
        header = f"## 📊 Top {len(papers)} quant-ph Papers - {datetime.now().strftime('%Y-%m-%d')}\n\n🔗 **SciRate**: https://scirate.com/?range=1\n"
    
    message = {
        "content": header
    }
    
    # ヘッダーを投稿
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=10)
        if response.status_code != 204:
            print(f"❌ Discord投稿エラー (status: {response.status_code})")
            return
    except Exception as e:
        print(f"❌ Discord投稿エラー: {e}")
        return
    
    time.sleep(1)
    
    # 各論文を投稿
    for i, paper in enumerate(papers, 1):
        # 要約を生成
        summary = generate_summary(paper['title'], paper.get('abstract', ''), language)
        
        # 著者リスト
        if paper['authors']:
            authors_str = ", ".join(paper['authors'][:3])
            if len(paper['authors']) > 3:
                authors_str += " et al."
        else:
            authors_str = "著者情報なし"
        
        # Discordメッセージを作成
        embed = {
            "embeds": [{
                "title": f"{i}. {paper['title']}",
                "url": paper['url'],
                "description": f"**📝 要約**\n{summary}\n\n**👥 著者:** {authors_str}\n**⭐ Scites:** {paper['scites']}",
                "color": 5814783,
                "footer": {
                    "text": f"arXiv: {paper['arxiv_id']}"
                },
                "fields": [
                    {
                        "name": "🔗 リンク",
                        "value": f"[arXiv]({paper['url']}) | [SciRate]({paper['scirate_url']})",
                        "inline": False
                    }
                ]
            }]
        }
        
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=embed, timeout=10)
            
            if response.status_code == 204:
                print(f"✅ {i}件目を投稿しました: {paper['title'][:50]}...")
            else:
                print(f"⚠️ {i}件目の投稿に失敗 (status: {response.status_code})")
        except Exception as e:
            print(f"⚠️ {i}件目の投稿エラー: {e}")
        
        time.sleep(2)
    
    print(f"\n🎉 完了！{len(papers)}件の論文をDiscordに投稿しました")


# ===== メイン処理 =====
def main():
    print("=" * 60)
    print("🚀 Scirate Discord Bot 起動")
    print("=" * 60)
    
    # 1. Scirateトップページから論文を取得
    papers = get_top_papers_from_scirate(ARXIV_CATEGORY, TOP_N_PAPERS)
    
    if not papers:
        print("❌ 論文が見つかりませんでした")
        return
    
    print(f"\n📋 投稿する論文（Top {len(papers)}）:")
    for i, paper in enumerate(papers, 1):
        print(f"  {i}. [{paper['scites']} scites] {paper['arxiv_id']} - {paper['title'][:60]}...")
    
    # 2. 各論文のAbstractを取得
    papers = enrich_papers_with_abstracts(papers)
    
    # 3. Discordに投稿
    post_to_discord(papers, SUMMARY_LANGUAGE)
    
    print("\n" + "=" * 60)
    print("✨ すべての処理が完了しました！")
    print("=" * 60)


if __name__ == "__main__":
    main()
