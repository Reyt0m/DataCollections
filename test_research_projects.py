import requests
from bs4 import BeautifulSoup

def test_research_projects_structure():
    """
    研究課題ページのHTML構造をテストする関数
    """
    base_url = "https://researchmap.jp"
    researcher_url = "https://researchmap.jp/hidekanematsu"

    # セッション設定
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    })

    try:
        # 研究者の詳細ページを取得
        print("研究者詳細ページを取得中...")
        response = session.get(researcher_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 研究課題ページへのリンクを探す
        print("\n=== 研究課題ページへのリンク ===")
        all_links = soup.find_all('a', href=True)
        research_project_links = [link for link in all_links if 'research_projects' in link['href']]

        if research_project_links:
            print(f"研究課題ページへのリンクが {len(research_project_links)} 個見つかりました")
            for link in research_project_links:
                print(f"リンクテキスト: {link.get_text().strip()}")
                print(f"リンクURL: {link['href']}")
        else:
            print("研究課題ページへのリンクが見つかりませんでした")

            # 研究課題ページを直接試行
            research_projects_url = researcher_url + "/research_projects"
            print(f"\n直接アクセスを試行: {research_projects_url}")

            projects_response = session.get(research_projects_url)
            if projects_response.status_code == 200:
                print("研究課題ページにアクセス成功")
                projects_soup = BeautifulSoup(projects_response.content, 'html.parser')

                # 研究課題の要素を探す
                print("\n=== 研究課題ページ構造 ===")

                # 様々なセレクターで研究課題を探す
                project_selectors = [
                    'div.research-project-item',
                    'div.project-item',
                    'li.project-item',
                    'div[class*="project"]',
                    'div[class*="research"]',
                    'table tr',
                    'div[class*="achievement"]',
                    'div[class*="publication"]'
                ]

                for selector in project_selectors:
                    elements = projects_soup.select(selector)
                    if elements:
                        print(f"セレクター '{selector}' で {len(elements)} 個の要素が見つかりました")
                        if len(elements) > 0:
                            print(f"最初の要素のHTML（最初の500文字）: {str(elements[0])[:500]}...")
                            break

                # HTML全体を保存
                with open('research_projects_structure_test.html', 'w', encoding='utf-8') as f:
                    f.write(str(projects_soup))
                print("\n研究課題ページのHTML構造を research_projects_structure_test.html に保存しました")

            else:
                print(f"研究課題ページの取得に失敗: {projects_response.status_code}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    test_research_projects_structure()
