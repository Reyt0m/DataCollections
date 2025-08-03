#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portfolio Scraper Tool (Improved Version)
URLリストからHTML構成要素を集め、portfolioタブを見つけ、そのページの中にある会社名をすべて集めるツール
画像ベースの会社名にも対応し、OCR機能も含む
"""

import requests
import time
import json
import csv
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import re
from typing import List, Dict, Optional, Set, Tuple
import logging
import os
from PIL import Image
import io
import base64
import cv2
import numpy as np

# OCR関連のインポート
try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: easyocr not available. Install with: pip install easyocr")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available. Install with: pip install pytesseract")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PortfolioScraper:
    def __init__(self, headless=True, timeout=10, use_ocr=False):
        """
        スクレイパーの初期化

        Args:
            headless: ヘッドレスモードで実行するかどうか
            timeout: タイムアウト時間（秒）
            use_ocr: OCR機能を使用するかどうか
        """
        self.headless = headless
        self.timeout = timeout
        self.use_ocr = use_ocr and (OCR_AVAILABLE or TESSERACT_AVAILABLE)
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # OCR機能の初期化
        self.ocr_reader = None
        if self.use_ocr:
            self._initialize_ocr()

        # Seleniumドライバーの初期化（エラーハンドリング付き）
        self._initialize_driver()

        # 拡張されたポートフォリオキーワード
        self.portfolio_keywords = [
            'portfolio', 'ポートフォリオ', '投資先', '企業', 'パートナー',
            'investments', 'companies', 'partners', 'clients',
            'investment', 'invest', '出資先', '投資企業', '投資実績',
            'portfolio companies', 'portfolio companies', '投資対象企業'
        ]

        # 会社名のパターン（改善版）
        self.company_patterns = [
            # 日本語の会社形態
            r'株式会社\s*([^\s]+)',
            r'有限会社\s*([^\s]+)',
            r'合同会社\s*([^\s]+)',
            r'([^\s]+)\s*株式会社',
            r'([^\s]+)\s*有限会社',
            r'([^\s]+)\s*合同会社',
            r'([^\s]+)\s*㈱',
            r'([^\s]+)\s*㈲',
            r'([^\s]+)\s*㈳',

            # 英語の会社形態
            r'([^\s]+)\s*Inc\.',
            r'([^\s]+)\s*Corp\.',
            r'([^\s]+)\s*LLC',
            r'([^\s]+)\s*Ltd\.',
            r'([^\s]+)\s*Co\.',
            r'([^\s]+)\s*Company',
            r'([^\s]+)\s*Technologies',
            r'([^\s]+)\s*Systems',
            r'([^\s]+)\s*Solutions',
            r'([^\s]+)\s*Group',
            r'([^\s]+)\s*Partners',
            r'([^\s]+)\s*Ventures',
            r'([^\s]+)\s*Capital',
            r'([^\s]+)\s*Fund',
            r'([^\s]+)\s*Studio',
            r'([^\s]+)\s*Labs',
            r'([^\s]+)\s*Works',
            r'([^\s]+)\s*Services',
            r'([^\s]+)\s*Platform',
            r'([^\s]+)\s*Network',
            r'([^\s]+)\s*Media',
            r'([^\s]+)\s*Digital',
            r'([^\s]+)\s*Tech',
            r'([^\s]+)\s*AI',
            r'([^\s]+)\s*Bio',
            r'([^\s]+)\s*Health',
            r'([^\s]+)\s*Care',
            r'([^\s]+)\s*Life',
            r'([^\s]+)\s*Food',
            r'([^\s]+)\s*Energy',
            r'([^\s]+)\s*Green',
            r'([^\s]+)\s*Eco',
            r'([^\s]+)\s*Smart',
            r'([^\s]+)\s*Next',
            r'([^\s]+)\s*Future',
            r'([^\s]+)\s*Global',
            r'([^\s]+)\s*World',
            r'([^\s]+)\s*International',
            r'([^\s]+)\s*Japan',
            r'([^\s]+)\s*Asia',
            r'([^\s]+)\s*Pacific',
            r'([^\s]+)\s*America',
            r'([^\s]+)\s*Europe',

            # 一般的な会社名パターン
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # キャピタライズされた単語
            r'([A-Z]{2,}(?:\s+[A-Z]{2,})*)',  # 大文字の略語
        ]

    def _initialize_ocr(self):
        """OCR機能の初期化"""
        try:
            if OCR_AVAILABLE:
                import easyocr
                self.ocr_reader = easyocr.Reader(['ja', 'en'])
                logger.info("EasyOCR initialized successfully")
            elif TESSERACT_AVAILABLE:
                logger.info("Tesseract available for OCR")
            else:
                logger.warning("No OCR engine available")
        except Exception as e:
            logger.error(f"OCR初期化エラー: {e}")
            self.ocr_reader = None

    def _initialize_driver(self):
        """Seleniumドライバーの初期化（改善版）"""
        try:
            # Chromeオプションの設定
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            # 追加の安定性オプション
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')

            # WebDriver Managerを使用してドライバーを取得
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_page_load_timeout(self.timeout)
                self.driver.implicitly_wait(10)
                logger.info("Seleniumドライバーの初期化に成功しました")
            except Exception as e:
                logger.warning(f"WebDriver Managerでの初期化に失敗: {e}")
                # フォールバック: システムのChromeDriverを使用
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.driver.set_page_load_timeout(self.timeout)
                    self.driver.implicitly_wait(10)
                    logger.info("システムのChromeDriverで初期化に成功しました")
                except Exception as e2:
                    logger.error(f"システムのChromeDriverでも初期化に失敗: {e2}")
                    self.driver = None

        except Exception as e:
            logger.error(f"Seleniumドライバーの初期化に失敗しました: {e}")
            self.driver = None

    def setup_ocr(self):
        """OCR機能の初期化"""
        self.ocr_reader = None
        if OCR_AVAILABLE:
            try:
                # 日本語と英語に対応
                self.ocr_reader = easyocr.Reader(['ja', 'en'], gpu=False)
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR: {e}")
                self.ocr_reader = None

    def setup_driver(self, headless: bool):
        """Seleniumドライバーの設定"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Seleniumドライバーの初期化が完了しました")
        except Exception as e:
            logger.error(f"Seleniumドライバーの初期化に失敗しました: {e}")
            self.driver = None

    def find_portfolio_tab(self, soup, base_url: str) -> Optional[str]:
        """
        ポートフォリオタブを探す（改善版）

        Args:
            soup: BeautifulSoupオブジェクト
            base_url: ベースURL

        Returns:
            ポートフォリオURL、見つからない場合はNone
        """
        # 1. リンク要素からポートフォリオタブを探す
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().lower()

            # 拡張されたキーワードマッチング
            for keyword in self.portfolio_keywords:
                if keyword in href or keyword in text:
                    portfolio_url = urljoin(base_url, link['href'])
                    logger.info(f"Portfolioタブを発見: {portfolio_url}")
                    return portfolio_url

            # 特殊なケース: ANRIのような企業
            if 'anri' in base_url.lower() and ('portfolio' in href or 'companies' in href):
                portfolio_url = urljoin(base_url, link['href'])
                logger.info(f"ANRI特殊ケース - Portfolioタブを発見: {portfolio_url}")
                return portfolio_url

        # 2. 現在のページがポートフォリオページかチェック
        current_url = base_url.lower()
        for keyword in self.portfolio_keywords:
            if keyword in current_url:
                logger.info(f"現在のページがポートフォリオページ: {base_url}")
                return base_url

        # 3. メタデータからポートフォリオ情報を探す
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            content = meta.get('content', '').lower()
            if any(keyword in content for keyword in self.portfolio_keywords):
                logger.info(f"メタデータからポートフォリオ情報を発見: {content}")
                return base_url

        logger.warning(f"ポートフォリオタブが見つかりません: {base_url}")
        return None

    def extract_text_from_image(self, img_url: str) -> Optional[str]:
        """
        画像からテキストを抽出（OCR）- 改善版

        Args:
            img_url: 画像のURL

        Returns:
            抽出されたテキスト、失敗時はNone
        """
        if not self.use_ocr:
            return None

        try:
            # 画像をダウンロード
            response = self.session.get(img_url, timeout=15)
            response.raise_for_status()

            # PILで画像を開く
            img = Image.open(io.BytesIO(response.content))

            # 画像の品質チェック
            if not self._is_image_quality_good(img):
                logger.debug(f"画像品質が低いためスキップ: {img_url}")
                return None

            # 画像の前処理
            processed_img = self._preprocess_image(img)

            # 複数のOCRエンジンで試行
            extracted_text = self._try_multiple_ocr(processed_img, img_url)

            if extracted_text:
                # テキストの後処理
                cleaned_text = self._postprocess_text(extracted_text)
                if cleaned_text:
                    logger.debug(f"OCR成功: {img_url} -> {cleaned_text}")
                    return cleaned_text

        except Exception as e:
            logger.warning(f"画像からのテキスト抽出に失敗: {img_url} - {e}")

        return None

    def _is_image_quality_good(self, img: Image.Image) -> bool:
        """
        画像の品質をチェック

        Args:
            img: PIL画像オブジェクト

        Returns:
            品質が良い場合はTrue
        """
        try:
            # 画像サイズチェック
            width, height = img.size
            if width < 50 or height < 50:
                return False

            # アスペクト比チェック（極端に細長い画像は除外）
            aspect_ratio = width / height
            if aspect_ratio > 10 or aspect_ratio < 0.1:
                return False

            # 画像モードチェック
            if img.mode not in ['RGB', 'RGBA', 'L', 'P']:
                return False

            return True

        except Exception:
            return False

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """
        画像の前処理

        Args:
            img: 元の画像

        Returns:
            前処理された画像
        """
        try:
            # RGBに変換
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 画像サイズの調整（大きすぎる場合は縮小）
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # コントラストと明度の調整
            from PIL import ImageEnhance

            # コントラストを少し上げる
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)

            # 明度を調整
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)

            return img

        except Exception as e:
            logger.debug(f"画像前処理に失敗: {e}")
            return img

    def _try_multiple_ocr(self, img: Image.Image, img_url: str) -> Optional[str]:
        """
        複数のOCRエンジンでテキスト抽出を試行

        Args:
            img: 前処理された画像
            img_url: 画像URL（ログ用）

        Returns:
            抽出されたテキスト
        """
        # 1. EasyOCRを試行
        if self.ocr_reader:
            try:
                results = self.ocr_reader.readtext(np.array(img))
                texts = []
                for result in results:
                    text, confidence = result[1], result[2]
                    # 信頼度が50%以上の場合のみ使用
                    if confidence > 0.5 and len(text.strip()) > 1:
                        texts.append(text.strip())

                if texts:
                    combined_text = ' '.join(texts)
                    logger.debug(f"EasyOCR成功: {img_url} -> {combined_text}")
                    return combined_text

            except Exception as e:
                logger.debug(f"EasyOCR失敗: {img_url} - {e}")

        # 2. Tesseractを試行
        if TESSERACT_AVAILABLE:
            try:
                # 日本語と英語の両方で試行
                text_jp = pytesseract.image_to_string(img, lang='jpn+eng')
                text_en = pytesseract.image_to_string(img, lang='eng')

                # より長いテキストを選択
                if len(text_jp.strip()) > len(text_en.strip()):
                    text = text_jp
                else:
                    text = text_en

                if text.strip():
                    logger.debug(f"Tesseract成功: {img_url} -> {text.strip()}")
                    return text.strip()

            except Exception as e:
                logger.debug(f"Tesseract失敗: {img_url} - {e}")

        # 3. 画像のalt属性やファイル名から推測
        return self._extract_text_from_filename(img_url)

    def _extract_text_from_filename(self, img_url: str) -> Optional[str]:
        """
        画像のファイル名やURLから会社名を推測

        Args:
            img_url: 画像URL

        Returns:
            推測されたテキスト
        """
        try:
            # URLからファイル名を抽出
            filename = img_url.split('/')[-1].split('?')[0]

            # 拡張子を除去
            name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename

            # アンダースコアやハイフンをスペースに変換
            name_cleaned = name_without_ext.replace('_', ' ').replace('-', ' ').replace('+', ' ')

            # 数字や特殊文字を除去
            import re
            name_cleaned = re.sub(r'[0-9]+', '', name_cleaned)
            name_cleaned = re.sub(r'[^\w\s]', '', name_cleaned)

            # 複数のスペースを単一スペースに
            name_cleaned = ' '.join(name_cleaned.split())

            if len(name_cleaned) > 2:
                logger.debug(f"ファイル名から推測: {img_url} -> {name_cleaned}")
                return name_cleaned

        except Exception as e:
            logger.debug(f"ファイル名解析失敗: {img_url} - {e}")

        return None

    def _postprocess_text(self, text: str) -> Optional[str]:
        """
        抽出されたテキストの後処理

        Args:
            text: 抽出されたテキスト

        Returns:
            後処理されたテキスト
        """
        try:
            # 基本的なクリーニング
            text = text.strip()

            # 改行やタブをスペースに変換
            text = re.sub(r'[\n\r\t]+', ' ', text)

            # 複数のスペースを単一スペースに
            text = re.sub(r'\s+', ' ', text)

            # 特殊文字の除去（ただし日本語と英語は保持）
            text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', text)

            # 短すぎるテキストは除外
            if len(text) < 2:
                return None

            # 明らかに会社名でないものを除外
            exclude_patterns = [
                r'^[0-9]+$',  # 数字のみ
                r'^[a-zA-Z]{1,2}$',  # 1-2文字のアルファベット
                r'^(click|read|more|view|learn|see|home|about|contact)$',  # 一般的なナビゲーション用語
                r'^(logo|image|photo|picture|icon)$',  # 画像関連用語
            ]

            for pattern in exclude_patterns:
                if re.match(pattern, text.lower()):
                    return None

            return text

        except Exception as e:
            logger.debug(f"テキスト後処理失敗: {e}")
            return None

    def click_image_and_extract_company(self, img_element, base_url: str) -> Optional[str]:
        """
        画像をクリックして詳細ページから会社名を抽出

        Args:
            img_element: 画像要素
            base_url: ベースURL

        Returns:
            会社名、失敗時はNone
        """
        if not self.driver:
            return None

        try:
            # 画像の親要素がリンクかチェック
            parent_link = img_element.find_parent('a')
            if not parent_link:
                return None

            href = parent_link.get('href')
            if not href:
                return None

            detail_url = urljoin(base_url, href)

            # 詳細ページを開く
            self.driver.get(detail_url)
            time.sleep(2)

            # 詳細ページから会社名を抽出
            detail_soup = BeautifulSoup(self.driver.page_source, 'lxml')
            companies = self.extract_companies_from_page(detail_soup)

            if companies:
                return list(companies)[0]  # 最初の会社名を返す

        except Exception as e:
            logger.warning(f"画像クリックによる詳細ページ取得に失敗: {e}")

        return None

    def extract_companies_from_page(self, soup: BeautifulSoup, base_url: str = "") -> Set[str]:
        """
        ページから会社名を抽出する（大幅改善版）

        Args:
            soup: BeautifulSoupオブジェクト
            base_url: ベースURL（画像クリック用）

        Returns:
            会社名のセット
        """
        companies = set()

        # 1. 特定のクラス名を持つ要素から会社名を抽出（優先度最高）
        portfolio_selectors = [
            '.fg-item-title',  # 15th Rock
            '.card_companyName__BWs6G',  # ANRI
            '.portfolioItem__title',  # サムライインキュベート
            '.portfolio__item',  # ジェネシア
            '[class*="company-name"]',
            '[class*="companyName"]',
            '[class*="fg-item-title"]',
            '[class*="card_companyName"]',
            '[class*="portfolio-item"]',
            '[class*="portfolioItem"]',
            'h2.fg-item-title',
            'h3.card_companyName__BWs6G',
            '.portfolio-item h2',
            '.portfolio-item h3',
            '.company-card h2',
            '.company-card h3',
            '.card h2',
            '.card h3',
            '.gallery-item h2',
            '.gallery-item h3',
            '.portfolio__item h3',
            '.portfolio__item h2'
        ]

        for selector in portfolio_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 1 and len(text) < 100:
                    clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', text).strip()
                    if clean_text:
                        companies.add(clean_text)

        # 2. 画像から会社名を抽出（OCR使用）
        if self.use_ocr:
            img_elements = soup.find_all('img')
            processed_images = 0
            successful_ocr = 0

            for img in img_elements:
                src = img.get('src', '')
                if src:
                    # 画像URLを完全なURLに変換
                    if src.startswith('//'):
                        img_url = 'https:' + src
                    elif src.startswith('/'):
                        img_url = urljoin(base_url, src)
                    elif not src.startswith('http'):
                        img_url = urljoin(base_url, src)
                    else:
                        img_url = src

                    # 画像からテキスト抽出
                    extracted_text = self.extract_text_from_image(img_url)
                    processed_images += 1

                    if extracted_text:
                        successful_ocr += 1
                        # 抽出されたテキストから会社名らしいものをフィルタリング
                        words = extracted_text.split()
                        for word in words:
                            if (len(word) >= 2 and len(word) <= 50 and
                                any(keyword in word.lower() for keyword in ['inc', 'corp', 'ltd', 'co', '株式会社', '有限会社', '合同会社'])):
                                companies.add(word)

                        # 抽出されたテキスト全体も追加（会社名の可能性がある場合）
                        if len(extracted_text) >= 3 and len(extracted_text) <= 50:
                            companies.add(extracted_text)

                    # 画像クリックによる詳細ページ取得（限定的に実行）
                    if base_url and processed_images <= 10:  # 最初の10枚のみ
                        detail_company = self.click_image_and_extract_company(img, base_url)
                        if detail_company:
                            companies.add(detail_company)

            logger.info(f"画像処理結果: {processed_images}枚処理, {successful_ocr}枚でOCR成功")

        # 3. リンク要素から会社名を抽出
        link_selectors = [
            'a[href*="http"]',  # 外部リンク
            '.card a',
            '.portfolio-item a',
            '.company-card a',
            '.gallery-item a',
            '.portfolio__item a'
        ]

        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                # リンクテキストから会社名を抽出
                text = element.get_text(strip=True)
                if text and len(text) > 1 and len(text) < 100:
                    clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', text).strip()
                    if clean_text:
                        companies.add(clean_text)

                # alt属性から会社名を抽出
                alt_text = element.get('alt', '')
                if alt_text and len(alt_text) > 1 and len(alt_text) < 100:
                    if any(keyword in alt_text.lower() for keyword in ['logo', 'company', 'corp', 'inc', 'ltd', '株式会社', '有限会社']):
                        clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', alt_text).strip()
                        if clean_text:
                            companies.add(clean_text)

        # 4. 画像のalt属性から会社名を抽出
        img_elements = soup.find_all('img')
        for img in img_elements:
            alt_text = img.get('alt', '')
            if alt_text and len(alt_text) > 1 and len(alt_text) < 100:
                if any(keyword in alt_text.lower() for keyword in ['logo', 'company', 'corp', 'inc', 'ltd', '株式会社', '有限会社']):
                    clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', alt_text).strip()
                    if clean_text:
                        companies.add(clean_text)

        # 5. 見出し要素から会社名を抽出
        heading_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        for selector in heading_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 1 and len(text) < 100:
                    if any(keyword in text.lower() for keyword in ['inc', 'corp', 'ltd', 'co', '株式会社', '有限会社', '合同会社']):
                        clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', text).strip()
                        if clean_text:
                            companies.add(clean_text)

        # 6. リスト要素から会社名を抽出
        list_elements = soup.find_all(['ul', 'ol'])
        for list_elem in list_elements:
            items = list_elem.find_all('li')
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 1 and len(text) < 100:
                    if any(keyword in text.lower() for keyword in ['inc', 'corp', 'ltd', 'co', '株式会社', '有限会社', '合同会社']):
                        clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', text).strip()
                        if clean_text:
                            companies.add(clean_text)

        # 7. 正規表現パターンマッチング（最後の手段）
        text_content = soup.get_text()
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                if match and len(match.strip()) > 1 and len(match.strip()) < 100:
                    clean_text = re.sub(r'[🇯🇵🇺🇸🇳🇱🇨🇦🇬🇧🇺🇸🇳🇱]', '', match.strip()).strip()
                    if clean_text:
                        companies.add(clean_text)

        # 最終的なフィルタリング
        companies = self._filter_company_names(companies)

        return companies

    def _filter_company_names(self, companies: Set[str]) -> Set[str]:
        """
        会社名をフィルタリングしてノイズを除去（改善版）

        Args:
            companies: 抽出された会社名のセット

        Returns:
            フィルタリングされた会社名のセット
        """
        filtered_companies = set()

        # 除外すべきパターン
        exclude_patterns = [
            # 一般的なナビゲーション要素
            r'^(top|home|about|contact|news|blog|careers|privacy|terms|login|signup|search)$',
            r'^(menu|navigation|header|footer|sidebar|main|content)$',
            r'^(next|previous|back|forward|close|open|expand|collapse)$',

            # 一般的な単語
            r'^(our|we|you|they|them|this|that|these|those)$',
            r'^(the|and|or|but|for|with|from|to|in|on|at|by)$',
            r'^(all|any|some|many|few|much|little|more|less)$',

            # 技術的なノイズ
            r'^[a-f0-9]{8,}$',  # 16進数文字列
            r'^[a-z]{1,2}$',  # 1-2文字のアルファベット
            r'^[0-9]+$',  # 数字のみ
            r'^[a-z]+[0-9]+[a-z]+$',  # アルファベット+数字+アルファベット

            # OCRノイズ
            r'^[a-z]{3,}[a-z]{3,}[a-z]{3,}$',  # 繰り返し文字
            r'^[a-z]+[a-z]+[a-z]+[a-z]+$',  # 4回以上の繰り返し

            # 画像・ファイル関連
            r'\.(png|jpg|jpeg|gif|svg|ico|webp)$',
            r'^(logo|image|photo|picture|icon|img)$',
            r'^(download|upload|file|document|pdf)$',
            r'.*logo.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',  # ロゴファイル
            r'.*_logo.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',  # _logoを含むファイル
            r'.*logo_.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',  # logo_を含むファイル
            r'.*_edited.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',  # _editedを含むファイル
            r'.*_2025.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',  # _2025を含むファイル
            r'.*_2024.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',  # _2024を含むファイル
            r'.*_2023.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',  # _2023を含むファイル

            # 言語・地域関連
            r'^(en|jp|ja|us|uk|eu|asia|pacific|global|world)$',
            r'^(english|japanese|chinese|korean|spanish|french|german)$',

            # 日付・時刻
            r'^\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'^\d{2}:\d{2}:\d{2}',  # HH:MM:SS
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO形式

            # 特殊文字のみ
            r'^[^\w\s]+$',

            # 短すぎるテキスト
            r'^.{1,2}$',

            # 長すぎるテキスト（説明文など）
            r'^.{100,}$',
        ]

        # 除外すべきキーワード（厳しさを調整）
        exclude_keywords = {
            'copyright', 'privacy', 'terms', 'policy', 'legal', 'disclaimer',
            'top', 'home', 'about', 'contact', 'news', 'blog', 'careers',
            'menu', 'navigation', 'header', 'footer', 'sidebar',
            'next', 'previous', 'back', 'forward', 'close', 'open',
            'our', 'we', 'you', 'they', 'them', 'this', 'that',
            'logo', 'image', 'photo', 'picture', 'icon', 'img',
            'download', 'upload', 'file', 'document',
            'en', 'jp', 'ja', 'us', 'uk', 'eu', 'asia', 'pacific',
            'english', 'japanese', 'chinese', 'korean',
            'all', 'any', 'some', 'many', 'few', 'much', 'little',
            'the', 'and', 'or', 'but', 'for', 'with', 'from', 'to', 'in', 'on', 'at', 'by',
            # UI要素（厳しさを調整）
            'website', 'location', 'chevron', 'right', 'left', 'up', 'down',
            'general', 'partner', 'lead', 'position', 'principal', 'associate',
            'founder', 'ceo', 'cto', 'cfo', 'coo', 'director', 'manager',
            'team', 'member', 'staff', 'employee', 'consultant', 'advisor',
            'board', 'committee', 'council', 'group', 'division', 'department',
            'section', 'unit', 'branch', 'office', 'location', 'address',
            'phone', 'email', 'contact', 'support', 'help', 'info', 'information',
            'service', 'services', 'product', 'products', 'solution', 'solutions',
            'technology', 'technologies', 'innovation', 'research', 'development',
            'investment', 'investments', 'portfolio', 'portfolios', 'company', 'companies',
            'corporation', 'corporations', 'limited', 'incorporated', 'partnership',
            'venture', 'ventures', 'capital', 'fund', 'funds', 'asset', 'assets',
            'management', 'consulting', 'advisory', 'financial', 'banking',
            'insurance', 'real estate', 'property', 'development', 'construction',
            'manufacturing', 'production', 'distribution', 'retail', 'wholesale',
            'trade', 'commerce', 'business', 'enterprise', 'startup', 'startups',
            'scaleup', 'scaleups', 'growth', 'expansion', 'acquisition', 'merger',
            'exit', 'exits', 'ipo', 'm&a', 'ma', 'deal', 'deals', 'transaction',
            'round', 'series', 'seed', 'angel', 'pre-seed', 'pre-seed', 'pre-seed',
            # 単一文字は除外
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
        }

        for company in companies:
            company_lower = company.lower().strip()

            # 基本的な長さチェック
            if len(company_lower) < 3 or len(company_lower) > 50:
                continue

            # 除外キーワードチェック
            if company_lower in exclude_keywords:
                continue

            # 除外パターンチェック
            should_exclude = False
            for pattern in exclude_patterns:
                if re.match(pattern, company_lower):
                    should_exclude = True
                    break

            if should_exclude:
                continue

            # 会社名らしいパターンチェック
            company_patterns = [
                r'.*株式会社.*',
                r'.*有限会社.*',
                r'.*合同会社.*',
                r'.*Inc\.?$',
                r'.*Corp\.?$',
                r'.*LLC$',
                r'.*Ltd\.?$',
                r'.*Co\.?$',
                r'.*Company$',
                r'.*Technologies$',
                r'.*Systems$',
                r'.*Solutions$',
                r'.*Group$',
                r'.*Partners$',
                r'.*Ventures$',
                r'.*Capital$',
                r'.*Fund$',
                r'.*Studio$',
                r'.*Labs$',
                r'.*Works$',
                r'.*Services$',
                r'.*Platform$',
                r'.*Network$',
                r'.*Media$',
                r'.*Digital$',
                r'.*Tech$',
                r'.*AI$',
                r'.*Bio$',
                r'.*Health$',
                r'.*Care$',
                r'.*Life$',
                r'.*Food$',
                r'.*Energy$',
                r'.*Green$',
                r'.*Eco$',
                r'.*Smart$',
                r'.*Next$',
                r'.*Future$',
                r'.*Global$',
                r'.*World$',
                r'.*International$',
                r'.*Japan$',
                r'.*Asia$',
                r'.*Pacific$',
                r'.*America$',
                r'.*Europe$',
            ]

            # 会社名らしいパターンにマッチするかチェック
            is_company_like = False
            for pattern in company_patterns:
                if re.match(pattern, company, re.IGNORECASE):
                    is_company_like = True
                    break

            # 会社名らしくない場合は、長さと内容で判断
            if not is_company_like:
                # 3-20文字で、大文字小文字が混在している場合は会社名の可能性
                if (3 <= len(company) <= 20 and
                    any(c.isupper() for c in company) and
                    any(c.islower() for c in company)):
                    # 追加チェック: 明らかなUI要素でないことを確認（厳しさを調整）
                    obvious_ui_elements = ['website', 'location', 'chevron', 'right', 'left', 'up', 'down',
                                          'general', 'partner', 'lead', 'position', 'principal', 'associate',
                                          'founder', 'ceo', 'cto', 'cfo', 'coo', 'director', 'manager',
                                          'team', 'member', 'staff', 'employee', 'consultant', 'advisor',
                                          'board', 'committee', 'council', 'group', 'division', 'department',
                                          'section', 'unit', 'branch', 'office', 'location', 'address',
                                          'phone', 'email', 'contact', 'support', 'help', 'info', 'information',
                                          'service', 'services', 'product', 'products', 'solution', 'solutions',
                                          'technology', 'technologies', 'innovation', 'research', 'development',
                                          'investment', 'investments', 'portfolio', 'portfolios', 'company', 'companies',
                                          'corporation', 'corporations', 'limited', 'incorporated', 'partnership',
                                          'venture', 'ventures', 'capital', 'fund', 'funds', 'asset', 'assets',
                                          'management', 'consulting', 'advisory', 'financial', 'banking',
                                          'insurance', 'real estate', 'property', 'development', 'construction',
                                          'manufacturing', 'production', 'distribution', 'retail', 'wholesale',
                                          'trade', 'commerce', 'business', 'enterprise', 'startup', 'startups',
                                          'scaleup', 'scaleups', 'growth', 'expansion', 'acquisition', 'merger',
                                          'exit', 'exits', 'ipo', 'm&a', 'ma', 'deal', 'deals', 'transaction',
                                          'round', 'series', 'seed', 'angel', 'pre-seed', 'pre-seed', 'pre-seed']

                    if not any(ui_element in company_lower for ui_element in obvious_ui_elements):
                        is_company_like = True

                # 追加: 日本語の会社名パターン
                elif (3 <= len(company) <= 30 and
                      any(ord(c) > 127 for c in company)):  # 非ASCII文字（日本語など）を含む
                    is_company_like = True

            if is_company_like:
                filtered_companies.add(company)

        return filtered_companies

    def scrape_with_requests(self, url: str) -> Optional[BeautifulSoup]:
        """
        requestsを使用してHTMLを取得

        Args:
            url: スクレイピング対象のURL

        Returns:
            BeautifulSoupオブジェクト、失敗時はNone
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            logger.error(f"requestsでHTML取得に失敗: {url} - {e}")
            return None

    def scrape_with_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """
        Seleniumを使用してHTMLを取得（JavaScriptが必要な場合）

        Args:
            url: スクレイピング対象のURL

        Returns:
            BeautifulSoupオブジェクト、失敗時はNone
        """
        if not self.driver:
            logger.error("Seleniumドライバーが利用できません")
            return None

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # ページの読み込みを待つ
            return BeautifulSoup(self.driver.page_source, 'lxml')
        except Exception as e:
            logger.error(f"SeleniumでHTML取得に失敗: {url} - {e}")
            return None

    def scrape_url(self, url: str) -> Dict[str, any]:
        """
        単一URLをスクレイピング（改善版）

        Args:
            url: スクレイピング対象のURL

        Returns:
            スクレイピング結果の辞書
        """
        logger.info(f"スクレイピング開始: {url}")

        result = {
            'url': url,
            'portfolio_url': None,
            'companies': [],
            'error': None,
            'method': None,
            'ocr_used': False
        }

        # まずrequestsで試行
        soup = self.scrape_with_requests(url)
        if soup:
            result['method'] = 'requests'
        else:
            # requestsが失敗した場合、Seleniumで試行
            soup = self.scrape_with_selenium(url)
            if soup:
                result['method'] = 'selenium'
            else:
                result['error'] = "HTMLの取得に失敗しました"
                return result

        # ポートフォリオタブを探す
        portfolio_url = self.find_portfolio_tab(soup, url)
        if portfolio_url:
            result['portfolio_url'] = portfolio_url

            # ポートフォリオページをスクレイピング
            portfolio_soup = self.scrape_with_requests(portfolio_url)
            if not portfolio_soup:
                portfolio_soup = self.scrape_with_selenium(portfolio_url)

            if portfolio_soup:
                companies = self.extract_companies_from_page(portfolio_soup, portfolio_url)
                result['companies'] = list(companies)
                result['ocr_used'] = self.use_ocr
                logger.info(f"Portfolioページから {len(companies)} 社の会社名を抽出: {portfolio_url}")
            else:
                result['error'] = "Portfolioページの取得に失敗しました"
        else:
            # ポートフォリオタブが見つからない場合、現在のページから会社名を抽出
            companies = self.extract_companies_from_page(soup, url)
            result['companies'] = list(companies)
            result['ocr_used'] = self.use_ocr
            logger.info(f"現在のページから {len(companies)} 社の会社名を抽出: {url}")

        return result

    def scrape_urls(self, urls: List[str]) -> List[Dict[str, any]]:
        """
        URLリストをスクレイピング

        Args:
            urls: スクレイピング対象のURLリスト

        Returns:
            スクレイピング結果のリスト
        """
        results = []

        for i, url in enumerate(urls, 1):
            logger.info(f"進捗: {i}/{len(urls)} - {url}")

            result = self.scrape_url(url)
            results.append(result)

            # サーバーに負荷をかけないよう少し待機
            time.sleep(2)

        return results

    def save_results(self, results: List[Dict[str, any]], output_file: str = 'portfolio_results.json'):
        """
        結果をJSONファイルに保存

        Args:
            results: スクレイピング結果のリスト
            output_file: 出力ファイル名
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"結果を保存しました: {output_file}")
        except Exception as e:
            logger.error(f"結果の保存に失敗しました: {e}")

    def save_results_csv(self, results: List[Dict[str, any]], output_file: str = 'portfolio_results.csv'):
        """
        結果をCSVファイルに保存

        Args:
            results: スクレイピング結果のリスト
            output_file: 出力ファイル名
        """
        try:
            # フラット化されたデータを作成
            flat_data = []
            for result in results:
                if result['companies']:
                    for company in result['companies']:
                        flat_data.append({
                            'url': result['url'],
                            'portfolio_url': result['portfolio_url'],
                            'company_name': company,
                            'method': result['method'],
                            'ocr_used': result['ocr_used'],
                            'error': result['error']
                        })
                else:
                    flat_data.append({
                        'url': result['url'],
                        'portfolio_url': result['portfolio_url'],
                        'company_name': '',
                        'method': result['method'],
                        'ocr_used': result['ocr_used'],
                        'error': result['error']
                    })

            df = pd.DataFrame(flat_data)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"結果をCSVに保存しました: {output_file}")
        except Exception as e:
            logger.error(f"CSV保存に失敗しました: {e}")

    def close(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()
        self.session.close()
        logger.info("リソースのクリーンアップが完了しました")

def load_urls_from_file(filename: str) -> List[str]:
    """
    ファイルからURLリストを読み込み

    Args:
        filename: URLリストファイル名

    Returns:
        URLリスト
    """
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
        logger.info(f"{len(urls)}個のURLを読み込みました: {filename}")
    except Exception as e:
        logger.error(f"URLファイルの読み込みに失敗しました: {e}")

    return urls

def main():
    """メイン関数"""
    # サンプルURLリスト（実際の使用時はファイルから読み込み）
    sample_urls = [
        "https://example.com",
        "https://example.org",
        # 実際のURLをここに追加
    ]

    # URLリストファイルが存在する場合は読み込み
    url_file = 'urls.txt'
    try:
        urls = load_urls_from_file(url_file)
        if not urls:
            logger.warning(f"URLファイルが空または見つかりません: {url_file}")
            logger.info("サンプルURLを使用します")
            urls = sample_urls
    except FileNotFoundError:
        logger.info(f"URLファイルが見つかりません: {url_file}")
        logger.info("サンプルURLを使用します")
        urls = sample_urls

    if not urls:
        logger.error("スクレイピング対象のURLがありません")
        return

    # スクレイパーの初期化（OCR機能付き）
    scraper = PortfolioScraper(headless=True, timeout=20, use_ocr=True)

    try:
        # スクレイピング実行
        results = scraper.scrape_urls(urls)

        # 結果の保存
        scraper.save_results(results, 'portfolio_results.json')
        scraper.save_results_csv(results, 'portfolio_results.csv')

        # 結果の表示
        total_companies = sum(len(result['companies']) for result in results)
        successful_scrapes = sum(1 for result in results if not result['error'])
        ocr_used_count = sum(1 for result in results if result['ocr_used'])

        logger.info(f"スクレイピング完了:")
        logger.info(f"  処理したURL数: {len(urls)}")
        logger.info(f"  成功したURL数: {successful_scrapes}")
        logger.info(f"  抽出された会社名数: {total_companies}")
        logger.info(f"  OCR使用回数: {ocr_used_count}")

    except KeyboardInterrupt:
        logger.info("ユーザーによって中断されました")
    except Exception as e:
        logger.error(f"スクレイピング中にエラーが発生しました: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
