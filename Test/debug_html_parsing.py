#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML解析のデバッグスクリプト
"""

import sys
import os
from pathlib import Path
from bs4 import BeautifulSoup

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_html_parsing():
    """HTML解析のデバッグ"""

    # テスト用HTMLファイルのパス
    html_file_path = Path("../samples/兼松 秀行 (Hideyuki Kanematsu) - 共同研究・競争的資金等の研究課題 - researchmap.html")

    if not html_file_path.exists():
        print(f"HTMLファイルが見つかりません: {html_file_path}")
        return

    try:
        # HTMLファイルを読み込み
        print(f"HTMLファイルを読み込み中: {html_file_path}")
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        print(f"HTMLファイル読み込み完了: {len(html_content)} 文字")

        # BeautifulSoupで解析
        soup = BeautifulSoup(html_content, 'html.parser')
        print(f"BeautifulSoup解析完了")

        # 様々なセレクタで試行
        selectors = [
            'li.list-group-item.rm-cv-disclosed',
            'li[class*="list-group-item"]',
            'li[class*="rm-cv-disclosed"]',
            '.list-group-item.rm-cv-disclosed',
            '.rm-cv-disclosed',
            'li'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            print(f"\nセレクタ '{selector}': {len(elements)} 要素")

            if len(elements) > 0:
                print(f"  最初の要素のクラス: {elements[0].get('class', 'N/A')}")
                print(f"  最初の要素のHTML: {str(elements[0])[:200]}...")

                # 研究課題タイトルを探す
                title_elements = elements[0].find_all('a', class_='rm-cv-list-title')
                if title_elements:
                    print(f"  タイトル要素数: {len(title_elements)}")
                    print(f"  最初のタイトル: {title_elements[0].get_text().strip()}")
                else:
                    print(f"  タイトル要素が見つかりません")

        # 直接的な検索
        print(f"\n=== 直接的な検索 ===")

        # すべてのli要素を検索
        all_li = soup.find_all('li')
        print(f"すべてのli要素数: {len(all_li)}")

        # クラス名に'list-group-item'を含む要素を検索
        list_group_items = []
        for li in all_li:
            classes = li.get('class', [])
            if 'list-group-item' in classes:
                list_group_items.append(li)

        print(f"list-group-itemクラスを含むli要素数: {len(list_group_items)}")

        if list_group_items:
            print(f"最初の要素のクラス: {list_group_items[0].get('class', 'N/A')}")

            # タイトル要素を探す
            title_element = list_group_items[0].find('a', class_='rm-cv-list-title')
            if title_element:
                print(f"タイトル: {title_element.get_text().strip()}")
                print(f"URL: {title_element.get('href', 'N/A')}")
            else:
                print("タイトル要素が見つかりません")

                # すべてのa要素を確認
                all_a = list_group_items[0].find_all('a')
                print(f"a要素数: {len(all_a)}")
                for i, a in enumerate(all_a):
                    print(f"  a[{i}]: {a.get('class', 'N/A')} - {a.get_text().strip()[:50]}...")

        # HTMLの一部を確認
        print(f"\n=== HTMLの一部を確認 ===")
        html_sample = html_content[10000:11000]  # 10,000文字目から1,000文字
        print(f"HTMLサンプル (10,000-11,000文字目):")
        print(html_sample)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_html_parsing()
