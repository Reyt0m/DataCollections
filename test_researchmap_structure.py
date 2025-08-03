import requests
from bs4 import BeautifulSoup
import json

def test_researchmap_structure():
    """
    Research MapのHTML構造をテストする関数
    """
    base_url = "https://researchmap.jp"
    search_url = "https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE"

    # セッション設定
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    })

    try:
        # 検索ページを取得
        print("検索ページを取得中...")
        response = session.get(search_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 総件数を確認
        print("\n=== 総件数情報 ===")
        total_count_elements = soup.find_all(text=lambda text: text and '総件数' in text)
        for element in total_count_elements:
            print(f"総件数要素: {element}")

        # 研究者リストの構造を確認
        print("\n=== 研究者リスト構造 ===")

        # 様々なクラス名で研究者要素を探す
        possible_selectors = [
            'div.researcher-item',
            'div.researcher',
            'li.researcher',
            'div.search-result-item',
            'li.search-result-item',
            'div.result-item',
            'li.result-item',
            'div[class*="researcher"]',
            'div[class*="search"]',
            'div[class*="result"]'
        ]

        for selector in possible_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"セレクター '{selector}' で {len(elements)} 個の要素が見つかりました")
                if len(elements) > 0:
                    print(f"最初の要素のクラス: {elements[0].get('class', [])}")
                    print(f"最初の要素のHTML（最初の200文字）: {str(elements[0])[:200]}...")
                    break

        # 研究者名の要素を探す
        print("\n=== 研究者名要素 ===")
        name_selectors = [
            'h3.researcher-name',
            'h3.name',
            'div.name',
            'span.name',
            'a[href*="/researchers/"]',
            'h3',
            'div[class*="name"]'
        ]

        for selector in name_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"名前セレクター '{selector}' で {len(elements)} 個の要素が見つかりました")
                if len(elements) > 0:
                    print(f"最初の要素のテキスト: {elements[0].get_text().strip()}")
                    print(f"最初の要素のHTML: {str(elements[0])}")
                    break

        # ページネーション構造を確認
        print("\n=== ページネーション構造 ===")
        pagination_selectors = [
            'div.pagination',
            'nav.pagination',
            'ul.pagination',
            'div[class*="pagination"]',
            'nav[class*="pagination"]'
        ]

        for selector in pagination_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"ページネーションセレクター '{selector}' で要素が見つかりました")
                print(f"ページネーションHTML: {str(elements[0])}")
                break

        # 実際の研究者URLを確認
        print("\n=== 研究者URL確認 ===")
        researcher_links = soup.find_all('a', href=True)
        researcher_urls = [link['href'] for link in researcher_links if '/researchers/' in link['href']]

        if researcher_urls:
            print(f"研究者URLが {len(researcher_urls)} 個見つかりました")
            print(f"最初の5個のURL: {researcher_urls[:5]}")

            # 最初の研究者の詳細ページを確認
            if researcher_urls:
                first_researcher_url = researcher_urls[0]
                if not first_researcher_url.startswith('http'):
                    first_researcher_url = base_url + first_researcher_url

                print(f"\n最初の研究者URL: {first_researcher_url}")

                # 研究者の詳細ページを取得
                researcher_response = session.get(first_researcher_url)
                if researcher_response.status_code == 200:
                    researcher_soup = BeautifulSoup(researcher_response.content, 'html.parser')

                    # 研究課題ページへのリンクを探す
                    project_links = researcher_soup.find_all('a', href=True)
                    project_urls = [link['href'] for link in project_links if 'research_projects' in link['href']]

                    if project_urls:
                        print(f"研究課題ページURL: {project_urls[0]}")

                        # 研究課題ページを取得
                        project_url = project_urls[0]
                        if not project_url.startswith('http'):
                            project_url = base_url + project_url

                        project_response = session.get(project_url)
                        if project_response.status_code == 200:
                            project_soup = BeautifulSoup(project_response.content, 'html.parser')

                            print("\n=== 研究課題ページ構造 ===")

                            # 研究課題の要素を探す
                            project_selectors = [
                                'div.research-project-item',
                                'div.project-item',
                                'li.project-item',
                                'div[class*="project"]',
                                'div[class*="research"]'
                            ]

                            for selector in project_selectors:
                                elements = project_soup.select(selector)
                                if elements:
                                    print(f"研究課題セレクター '{selector}' で {len(elements)} 個の要素が見つかりました")
                                    if len(elements) > 0:
                                        print(f"最初の研究課題要素のHTML: {str(elements[0])}")
                                        break
                        else:
                            print(f"研究課題ページの取得に失敗: {project_response.status_code}")
                    else:
                        print("研究課題ページへのリンクが見つかりませんでした")
                else:
                    print(f"研究者詳細ページの取得に失敗: {researcher_response.status_code}")

        # HTML全体の構造を保存
        with open('researchmap_structure_test.html', 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print("\nHTML構造を researchmap_structure_test.html に保存しました")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    test_researchmap_structure()
