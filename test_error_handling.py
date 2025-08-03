import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from researchmap_researchers_scraper import ResearchMapResearchersScraper

def test_error_handling():
    """
    エラーハンドリングとログ機能をテストする
    """
    print("=== エラーハンドリングテスト ===")

    # スクレイパーを初期化
    scraper = ResearchMapResearchersScraper()

    # 1. 無効なURLでのテスト
    print("\n1. 無効なURLでのテスト")
    try:
        result = scraper.get_total_pages("https://invalid-url-test.com")
        print(f"結果: {result}")
    except Exception as e:
        print(f"期待されるエラー: {e}")

    # 2. 存在しない研究者URLでのテスト
    print("\n2. 存在しない研究者URLでのテスト")
    try:
        projects = scraper.get_research_projects("https://researchmap.jp/nonexistent-researcher")
        print(f"取得された研究課題数: {len(projects)}")
    except Exception as e:
        print(f"期待されるエラー: {e}")

    # 3. 空のHTMLでのテスト
    print("\n3. 空のHTMLでのテスト")
    try:
        researchers = scraper.extract_researchers_from_page("")
        print(f"取得された研究者数: {len(researchers)}")
    except Exception as e:
        print(f"期待されるエラー: {e}")

    # 4. ログファイルの確認
    print("\n4. ログファイルの確認")
    try:
        with open('researchmap_scraper.log', 'r', encoding='utf-8') as f:
            log_content = f.read()
            log_lines = log_content.split('\n')
            print(f"ログファイルの行数: {len(log_lines)}")
            print("最新のログエントリ（最後の5行）:")
            for line in log_lines[-5:]:
                if line.strip():
                    print(f"  {line}")
    except FileNotFoundError:
        print("ログファイルが見つかりません")
    except Exception as e:
        print(f"ログファイル読み込みエラー: {e}")

    print("\n=== テスト完了 ===")
    print("エラーハンドリングが正常に動作していることを確認してください。")

def test_performance():
    """
    パフォーマンステスト
    """
    print("\n=== パフォーマンステスト ===")

    import time
    scraper = ResearchMapResearchersScraper()

    # 単一研究者の処理時間を測定
    start_time = time.time()

    try:
        projects = scraper.get_research_projects("https://researchmap.jp/hidekanematsu")
        end_time = time.time()

        processing_time = end_time - start_time
        print(f"単一研究者の処理時間: {processing_time:.2f}秒")
        print(f"取得された研究課題数: {len(projects)}")
        print(f"1研究課題あたりの処理時間: {processing_time/len(projects):.3f}秒")

        # 推定総処理時間
        total_researchers = 540  # 推定値
        estimated_total_time = processing_time * total_researchers
        estimated_hours = estimated_total_time / 3600

        print(f"全研究者処理の推定時間: {estimated_hours:.1f}時間")

    except Exception as e:
        print(f"パフォーマンステストエラー: {e}")

if __name__ == "__main__":
    test_error_handling()
    test_performance()
