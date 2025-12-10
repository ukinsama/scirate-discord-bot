#!/usr/bin/env python3
"""
Scirate Discord Bot (Gemini API版) - 改善版
Scirateのquant-phトップページから、scites数上位10件の論文をAI要約付きでDiscordに投稿

改善点:
- モデル優先順位の最適化（gemini-2.5-flash-lite優先）
- インテリジェントなレート制限対策
- バッチ処理による効率化
- キャッシュ機能
- 詳細なログ機能

使い方:
1. 必要なパッケージをインストール: pip install requests beautifulsoup4 google-generativeai
2. このスクリプトを実行: python scirate_discord_bot_improved.py
"""

import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import List, Dict, Optional
import re
import os
import json
import hashlib
import logging
from pathlib import Path
import google.generativeai as genai

# ===== ログ設定 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scirate_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ===== 設定（ここを編集してください） =====
# 環境変数から取得（GitHub Actions用）、なければデフォルト値を使用
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', "")
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "")  # Gemini APIキーを設定(空じゃないとだめ）
ARXIV_CATEGORY = "quant-ph"  # カテゴリ (quant-ph, cs.AI, cs.LG など)
TOP_N_PAPERS = 8  # 投稿する論文数
SUMMARY_LANGUAGE = "ja"  # 要約言語 (ja=日本語, en=英語)

# キャッシュ設定
CACHE_DIR = Path("cache")
CACHE_EXPIRY_HOURS = 24  # キャッシュの有効期限（時間）

# モデル優先順位（RPM制限が緩い順）
MODEL_PRIORITY = [
    {
        'name': 'gemini-2.5-flash-lite',
        'rpm': 10,
        'description': 'Lite版 - RPM制限が緩い（推奨）'
    },
    {
        'name': 'gemini-2.5-flash',
        'rpm': 5,
        'description': '標準版 - 高品質だがRPM制限が厳しい'
    },
    {
        'name': 'gemma-3-27b',
        'rpm': 30,
        'description': 'Gemma - RPM制限が最も緩い（フォールバック用）'
    },
    {
        'name': 'gemini-2.0-flash',
        'rpm': 15,
        'description': '旧版Flash - フォールバック用'
    },
]

# Gemini APIを初期化
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# ===== レート制限管理クラス =====
class RateLimiter:
    """
    RPM（Requests Per Minute）制限を管理するクラス
    """
    def __init__(self, rpm_limit: int = 10):
        self.rpm_limit = rpm_limit
        self.interval = 60.0 / rpm_limit  # リクエスト間隔（秒）
        self.last_request_time = 0
        self.request_count = 0
        self.minute_start = time.time()

    def wait_if_needed(self):
        """必要に応じて待機"""
        current_time = time.time()

        # 1分経過したらカウンターをリセット
        if current_time - self.minute_start >= 60:
            self.request_count = 0
            self.minute_start = current_time

        # RPM制限に達している場合は待機
        if self.request_count >= self.rpm_limit:
            wait_time = 60 - (current_time - self.minute_start)
            if wait_time > 0:
                logger.info(f"RPM制限に達しました。{wait_time:.1f}秒待機します...")
                time.sleep(wait_time)
                self.request_count = 0
                self.minute_start = time.time()

        # 最小間隔を確保
        elapsed = current_time - self.last_request_time
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)

        self.last_request_time = time.time()
        self.request_count += 1

    def update_rpm(self, new_rpm: int):
        """RPM制限を更新"""
        self.rpm_limit = new_rpm
        self.interval = 60.0 / new_rpm


# グローバルレート制限インスタンス
rate_limiter = RateLimiter(rpm_limit=10)


# ===== キャッシュ管理 =====
class SummaryCache:
    """
    論文要約のキャッシュを管理するクラス
    """
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "summaries.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """キャッシュを読み込み"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"キャッシュ読み込みエラー: {e}")
        return {}

    def _save_cache(self):
        """キャッシュを保存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"キャッシュ保存エラー: {e}")

    def _generate_key(self, arxiv_id: str, abstract: str) -> str:
        """キャッシュキーを生成"""
        content = f"{arxiv_id}:{abstract[:200]}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, arxiv_id: str, abstract: str) -> Optional[str]:
        """キャッシュから要約を取得"""
        key = self._generate_key(arxiv_id, abstract)
        if key in self.cache:
            entry = self.cache[key]
            # 有効期限チェック
            cached_time = datetime.fromisoformat(entry['timestamp'])
            if (datetime.now() - cached_time).total_seconds() < CACHE_EXPIRY_HOURS * 3600:
                logger.info(f"キャッシュヒット: {arxiv_id}")
                return entry['summary']
            else:
                logger.info(f"キャッシュ期限切れ: {arxiv_id}")
                del self.cache[key]
        return None

    def set(self, arxiv_id: str, abstract: str, summary: str):
        """要約をキャッシュに保存"""
        key = self._generate_key(arxiv_id, abstract)
        self.cache[key] = {
            'arxiv_id': arxiv_id,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
        logger.info(f"キャッシュ保存: {arxiv_id}")

    def get_stats(self) -> Dict:
        """キャッシュ統計を取得"""
        return {
            'total_entries': len(self.cache),
            'cache_file': str(self.cache_file)
        }


# グローバルキャッシュインスタンス
summary_cache = SummaryCache()


# ===== API使用量トラッキング =====
class APIUsageTracker:
    """
    API使用量を追跡するクラス
    """
    def __init__(self):
        self.usage_file = CACHE_DIR / "api_usage.json"
        self.usage = self._load_usage()

    def _load_usage(self) -> Dict:
        """使用量データを読み込み"""
        CACHE_DIR.mkdir(exist_ok=True)
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {'daily': {}, 'total': {'requests': 0, 'tokens': 0}}

    def _save_usage(self):
        """使用量データを保存"""
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"使用量保存エラー: {e}")

    def record(self, model: str, tokens: int = 0):
        """API使用を記録"""
        today = datetime.now().strftime('%Y-%m-%d')

        if today not in self.usage['daily']:
            self.usage['daily'][today] = {'requests': 0, 'tokens': 0, 'models': {}}

        self.usage['daily'][today]['requests'] += 1
        self.usage['daily'][today]['tokens'] += tokens

        if model not in self.usage['daily'][today]['models']:
            self.usage['daily'][today]['models'][model] = 0
        self.usage['daily'][today]['models'][model] += 1

        self.usage['total']['requests'] += 1
        self.usage['total']['tokens'] += tokens

        self._save_usage()

    def get_today_usage(self) -> Dict:
        """今日の使用量を取得"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.usage['daily'].get(today, {'requests': 0, 'tokens': 0, 'models': {}})

    def print_summary(self):
        """使用量サマリーを表示"""
        today_usage = self.get_today_usage()
        logger.info("=" * 40)
        logger.info("API使用量サマリー")
        logger.info(f"  今日のリクエスト数: {today_usage['requests']}")
        logger.info(f"  今日のモデル別使用:")
        for model, count in today_usage.get('models', {}).items():
            logger.info(f"    - {model}: {count}回")
        logger.info(f"  累計リクエスト数: {self.usage['total']['requests']}")
        logger.info("=" * 40)


# グローバル使用量トラッカー
usage_tracker = APIUsageTracker()


# ===== Scirateトップページから論文を取得 =====
def get_top_papers_from_scirate(category: str, top_n: int = 10) -> List[Dict]:
    """
    Scirateのトップページから、scites順の論文を取得
    """
    logger.info(f"Scirate {category}カテゴリのトップページから論文を取得中...")

    url = f"https://scirate.com/arxiv/{category}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            logger.error(f"Scirateからの取得に失敗 (status: {response.status_code})")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        papers = []

        # paperlist → ul.papers を探す
        paperlist = soup.find('div', class_='paperlist')

        if not paperlist:
            logger.error("paperlist要素が見つかりません")
            return []

        papers_ul = paperlist.find('ul', class_='papers')

        if not papers_ul:
            logger.error("ul.papers要素が見つかりません")
            return []

        # 各論文要素（div.row）を取得
        paper_rows = papers_ul.find_all('div', class_='row')

        logger.info(f"{len(paper_rows)}件の論文を発見")

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
                logger.warning(f"論文の解析エラー: {e}")
                continue

        # Scites順にソート（降順）
        papers.sort(key=lambda x: x['scites'], reverse=True)

        logger.info(f"{len(papers)}件の論文を取得しました")

        # 上位10件を表示
        if papers:
            logger.info(f"Scites数上位{min(10, len(papers))}件:")
            for i, paper in enumerate(papers[:10], 1):
                logger.info(f"  {i}. [{paper['scites']:3d} scites] {paper['arxiv_id']} - {paper['title'][:50]}...")

        return papers[:top_n]

    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return []


# ===== 論文の詳細情報を補完 =====
def enrich_papers_with_abstracts(papers: List[Dict]) -> List[Dict]:
    """
    各論文のAbstractをarXiv APIから取得
    """
    logger.info(f"各論文の詳細情報を取得中...")

    for i, paper in enumerate(papers, 1):
        logger.info(f"   [{i}/{len(papers)}] {paper['arxiv_id']} の情報を取得中...")

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
                if entry is not None:
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
            logger.warning(f"エラー: {e}")

        time.sleep(1)  # arXiv APIへの負荷を避ける

    logger.info("詳細情報取得完了")
    return papers


# ===== Google Gemini APIで要約を生成（改善版） =====
def generate_summary(title: str, abstract: str, arxiv_id: str, language: str = "ja") -> str:
    """
    Google Gemini APIを使って論文を2-3文で要約（キャッシュ・レート制限対応）
    """
    logger.info(f"要約生成中: {title[:40]}...")

    if not abstract:
        return "Abstractが取得できませんでした。"

    if not GEMINI_API_KEY:
        return "Gemini APIキーが設定されていません。"

    # キャッシュをチェック
    cached_summary = summary_cache.get(arxiv_id, abstract)
    if cached_summary:
        return cached_summary

    if language == "ja":
        prompt = f"""以下の論文を2-3文の日本語で簡潔に要約してください。

【重要な指示】
- 専門用語は残しつつ、何を研究したかが分かるように説明してください
- 数式はLaTeXではなく、Discordで読める形式で表記してください
  例: μ_c², P_{{11→11}}(E), Δt(E), φ⁴, ⟨ψ|H|ψ⟩
- 具体的な数値（パラメータ値、精度、誤差など）があれば正確に含めてください
- ギリシャ文字はそのまま使用: α, β, γ, δ, ε, θ, λ, μ, ν, π, σ, φ, ψ, ω
- 上付き・下付き文字: ₀₁₂₃₄₅₆₇₈₉, ⁰¹²³⁴⁵⁶⁷⁸⁹

タイトル: {title}

要旨: {abstract}

要約:"""
    else:
        prompt = f"""Summarize the following paper in 2-3 sentences. Keep technical terms and explain what was studied.

Title: {title}

Abstract: {abstract}

Summary:"""

    # モデル優先順位に従って試行
    for model_info in MODEL_PRIORITY:
        model_name = model_info['name']

        try:
            # レート制限を適用
            rate_limiter.update_rpm(model_info['rpm'])
            rate_limiter.wait_if_needed()

            logger.info(f"   Using model: {model_name} (RPM: {model_info['rpm']})")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)

            # 使用量を記録
            usage_tracker.record(model_name)

            # 安全性フィルタでブロックされたかチェック
            if not response.candidates:
                logger.warning(f"   No candidates in response")
                if hasattr(response, 'prompt_feedback'):
                    logger.warning(f"   Prompt feedback: {response.prompt_feedback}")
                continue

            candidate = response.candidates[0]

            # finish_reasonをチェック
            if hasattr(candidate, 'finish_reason'):
                # SAFETY=3 でブロックされた場合
                if candidate.finish_reason == 3:
                    logger.warning(f"   Blocked by safety filter")
                    continue

            # テキストを取得
            if hasattr(response, 'text') and response.text:
                summary = response.text.strip()
                if summary:
                    # キャッシュに保存
                    summary_cache.set(arxiv_id, abstract, summary)
                    return summary
                else:
                    logger.warning(f"   Empty text in response")
                    continue
            else:
                logger.warning(f"   No text attribute in response")
                continue

        except Exception as e:
            error_str = str(e)
            # クォータ超過エラーの場合は次のモデルを試す
            if '429' in error_str or 'quota' in error_str.lower() or 'rate' in error_str.lower():
                logger.warning(f"   {model_name} クォータ/レート制限、次のモデルを試します...")
                # エクスポネンシャルバックオフ
                time.sleep(5)
                continue
            else:
                logger.error(f"要約生成エラー: {e}")
                import traceback
                traceback.print_exc()
                continue

    # すべてのモデルが失敗した場合
    logger.error("すべてのモデルで要約生成に失敗")
    return "要約の生成に失敗しました（全モデルで失敗）。"


# ===== バッチ要約生成（オプション機能） =====
def generate_batch_summaries(papers: List[Dict], language: str = "ja") -> Dict[str, str]:
    """
    複数論文を1回のAPI呼び出しで要約（RPD節約用）
    注意: 1回のリクエストで処理するため、長いコンテキストが必要
    """
    logger.info(f"バッチ要約生成中 ({len(papers)}件)...")

    if not GEMINI_API_KEY:
        return {p['arxiv_id']: "Gemini APIキーが設定されていません。" for p in papers}

    # キャッシュ済みの論文を除外
    uncached_papers = []
    cached_summaries = {}

    for paper in papers:
        cached = summary_cache.get(paper['arxiv_id'], paper.get('abstract', ''))
        if cached:
            cached_summaries[paper['arxiv_id']] = cached
        elif paper.get('abstract'):
            uncached_papers.append(paper)

    if not uncached_papers:
        logger.info("すべての論文がキャッシュ済みです")
        return cached_summaries

    logger.info(f"キャッシュヒット: {len(cached_summaries)}件, 新規生成: {len(uncached_papers)}件")

    # バッチプロンプトを構築
    if language == "ja":
        prompt = """以下の複数の論文を、各2-3文の日本語で簡潔に要約してください。

【重要な指示】
- 各論文の要約を「[論文番号] 要約内容」の形式で出力してください
- 専門用語は残しつつ、何を研究したかが分かるように説明してください
- 数式はDiscordで読める形式で表記してください

"""
    else:
        prompt = """Summarize each of the following papers in 2-3 sentences.

Format: [Paper number] Summary content

"""

    for i, paper in enumerate(uncached_papers, 1):
        prompt += f"\n[{i}] タイトル: {paper['title']}\n要旨: {paper.get('abstract', 'N/A')[:500]}\n"

    prompt += "\n要約:"

    # APIを呼び出し
    for model_info in MODEL_PRIORITY:
        model_name = model_info['name']

        try:
            rate_limiter.update_rpm(model_info['rpm'])
            rate_limiter.wait_if_needed()

            logger.info(f"   バッチ処理に {model_name} を使用")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)

            usage_tracker.record(model_name)

            if hasattr(response, 'text') and response.text:
                # レスポンスをパース
                result_text = response.text.strip()
                summaries = {}

                # [番号] 形式で分割
                pattern = r'\[(\d+)\]\s*(.+?)(?=\[\d+\]|$)'
                matches = re.findall(pattern, result_text, re.DOTALL)

                for num_str, summary in matches:
                    num = int(num_str) - 1
                    if 0 <= num < len(uncached_papers):
                        paper = uncached_papers[num]
                        clean_summary = summary.strip()
                        summaries[paper['arxiv_id']] = clean_summary
                        summary_cache.set(paper['arxiv_id'], paper.get('abstract', ''), clean_summary)

                # キャッシュ済みと結合
                summaries.update(cached_summaries)
                return summaries

        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'quota' in error_str.lower():
                logger.warning(f"   {model_name} クォータ超過、次のモデルを試します...")
                time.sleep(5)
                continue
            else:
                logger.error(f"バッチ要約生成エラー: {e}")
                continue

    # フォールバック: 個別に生成
    logger.warning("バッチ処理失敗、個別生成にフォールバック")
    for paper in uncached_papers:
        summary = generate_summary(paper['title'], paper.get('abstract', ''), paper['arxiv_id'], language)
        cached_summaries[paper['arxiv_id']] = summary

    return cached_summaries


# ===== Discordに投稿 =====
def post_to_discord(papers: List[Dict], language: str = "ja", use_batch: bool = False):
    """
    論文リストをDiscordに投稿
    """
    logger.info(f"Discordに投稿中...")

    # バッチモードの場合は事前に全要約を生成
    summaries = {}
    if use_batch:
        summaries = generate_batch_summaries(papers, language)

    # ヘッダーメッセージ（SciRateのURLを含む）
    today_str = datetime.now().strftime("%Y年%m月%d日")
    if language == "ja":
        header = f"## {today_str} の quant-ph 人気論文 Top {len(papers)}\n\n**SciRate**: https://scirate.com/?range=1\n"
    else:
        header = f"## Top {len(papers)} quant-ph Papers - {datetime.now().strftime('%Y-%m-%d')}\n\n**SciRate**: https://scirate.com/?range=1\n"

    message = {
        "content": header
    }

    # ヘッダーを投稿
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=10)
        if response.status_code != 204:
            logger.error(f"Discord投稿エラー (status: {response.status_code})")
            return
    except Exception as e:
        logger.error(f"Discord投稿エラー: {e}")
        return

    time.sleep(1)

    # 各論文を投稿
    for i, paper in enumerate(papers, 1):
        # 要約を取得（バッチモードか個別生成か）
        if use_batch and paper['arxiv_id'] in summaries:
            summary = summaries[paper['arxiv_id']]
        else:
            summary = generate_summary(paper['title'], paper.get('abstract', ''), paper['arxiv_id'], language)

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
                "description": f"**要約**\n{summary}\n\n**著者:** {authors_str}\n**Scites:** {paper['scites']}",
                "color": 5814783,
                "footer": {
                    "text": f"arXiv: {paper['arxiv_id']}"
                },
                "fields": [
                    {
                        "name": "リンク",
                        "value": f"[arXiv]({paper['url']}) | [SciRate]({paper['scirate_url']})",
                        "inline": False
                    }
                ]
            }]
        }

        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=embed, timeout=10)

            if response.status_code == 204:
                logger.info(f"{i}件目を投稿しました: {paper['title'][:50]}...")
            else:
                logger.warning(f"{i}件目の投稿に失敗 (status: {response.status_code})")
        except Exception as e:
            logger.warning(f"{i}件目の投稿エラー: {e}")

        time.sleep(2)

    logger.info(f"完了！{len(papers)}件の論文をDiscordに投稿しました")


# ===== メイン処理 =====
def main():
    logger.info("=" * 60)
    logger.info("Scirate Discord Bot 起動 (Gemini API 改善版)")
    logger.info("=" * 60)

    # キャッシュ統計を表示
    cache_stats = summary_cache.get_stats()
    logger.info(f"キャッシュ: {cache_stats['total_entries']}件のエントリ")

    # 1. Scirateトップページから論文を取得
    papers = get_top_papers_from_scirate(ARXIV_CATEGORY, TOP_N_PAPERS)

    if not papers:
        logger.error("論文が見つかりませんでした")
        return

    logger.info(f"投稿する論文（Top {len(papers)}）:")
    for i, paper in enumerate(papers, 1):
        logger.info(f"  {i}. [{paper['scites']} scites] {paper['arxiv_id']} - {paper['title'][:60]}...")

    # 2. 各論文のAbstractを取得
    papers = enrich_papers_with_abstracts(papers)

    # 3. Discordに投稿（バッチモードを使用してRPD節約）
    post_to_discord(papers, SUMMARY_LANGUAGE, use_batch=True)

    # API使用量サマリーを表示
    usage_tracker.print_summary()

    logger.info("=" * 60)
    logger.info("すべての処理が完了しました！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
