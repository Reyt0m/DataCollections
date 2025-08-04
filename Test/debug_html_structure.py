#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML構造の詳細デバッグスクリプト
"""

import sys
import os
from pathlib import Path
from bs4 import BeautifulSoup

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_html_structure():
    """HTML構造の詳細デバッグ"""

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

        # 研究課題アイテムを検索
        research_items = soup.find_all('li', class_=lambda x: x and 'list-group-item' in x and 'rm-cv-disclosed' in x)
        print(f"研究課題アイテム数: {len(research_items)}")

        if research_items:
            # 最初の研究課題アイテムの構造を詳しく確認
            first_item = research_items[0]
            print(f"\n=== 最初の研究課題アイテムの構造 ===")
            print(f"HTML: {first_item}")

            # すべてのdiv要素を確認
            divs = first_item.find_all('div')
            print(f"\n=== div要素の詳細 ===")
            print(f"div要素数: {len(divs)}")

            for i, div in enumerate(divs):
                print(f"\ndiv[{i}]:")
                print(f"  クラス: {div.get('class', 'N/A')}")
                print(f"  テキスト: {div.get_text().strip()}")
                print(f"  HTML: {div}")

                # div内のa要素を確認
                a_elements = div.find_all('a')
                if a_elements:
                    print(f"  a要素数: {len(a_elements)}")
                    for j, a in enumerate(a_elements):
                        print(f"    a[{j}]: {a.get('class', 'N/A')} - {a.get_text().strip()}")

            # 2番目のdiv（助成金情報）を詳しく確認
            if len(divs) > 1:
                funding_div = divs[1]
                print(f"\n=== 助成金情報divの詳細 ===")
                print(f"HTML: {funding_div}")
                print(f"テキスト: '{funding_div.get_text().strip()}'")

                # テキストノードを詳しく確認
                for content in funding_div.contents:
                    if hasattr(content, 'name'):
                        print(f"要素: {content.name} - {content.get_text().strip()}")
                    else:
                        print(f"テキスト: '{content.strip()}'")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_html_structure()
