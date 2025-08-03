import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from researchmap_researchers_scraper import ResearchMapResearchersScraper
import json

def test_updated_scraper():
    """
    更新されたスクレイパーのテスト
    """
    # スクレイパーを初期化
    scraper = ResearchMapResearchersScraper()

    # 検索URL
    search_url = "https://researchmap.jp/researchers?affiliation=%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE"

    try:
        # 最初のページのみをテスト
        print("最初のページの研究者を取得中...")
        researchers = scraper.get_researchers_from_all_pages(search_url)

        print(f"取得した研究者数: {len(researchers)}")

        if researchers:
            # 最初の研究者の詳細をテスト
            first_researcher = researchers[0]
            print(f"\n最初の研究者: {first_researcher.get('name', 'Unknown')}")
            print(f"URL: {first_researcher.get('researcher_url', 'Unknown')}")

            # 研究課題を取得
            print("\n研究課題を取得中...")
            projects = scraper.get_research_projects(first_researcher['researcher_url'])

            print(f"取得した研究課題数: {len(projects)}")

            # 競争的研究課題をフィルタリング
            competitive_projects = [p for p in projects if p.get('is_competitive', False)]
            print(f"競争的研究課題数: {len(competitive_projects)}")

            # 最初の3つの研究課題を表示
            for i, project in enumerate(projects[:3], 1):
                print(f"\n研究課題 {i}:")
                print(f"  タイトル: {project.get('title', 'Unknown')}")
                print(f"  競争的: {project.get('is_competitive', False)}")
                print(f"  URL: {project.get('project_url', 'Unknown')}")

            # 結果を保存
            test_result = {
                'researcher': first_researcher,
                'all_projects': projects,
                'competitive_projects': competitive_projects
            }

            with open('test_scraper_result.json', 'w', encoding='utf-8') as f:
                json.dump(test_result, f, ensure_ascii=False, indent=2)

            print(f"\nテスト結果を test_scraper_result.json に保存しました")

        else:
            print("研究者が見つかりませんでした")

    except Exception as e:
        print(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updated_scraper()
