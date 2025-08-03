import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from researchmap_researchers_scraper import ResearchMapResearchersScraper

def test_competitive_detection():
    """
    競争的研究課題の判定機能をテストする
    """
    # テスト用の研究課題タイトル
    test_titles = [
        "基盤研究(A) 鉄鋼材料の研究",
        "JST戦略的創造研究推進事業",
        "文部科学省科学研究費補助金",
        "厚生労働科学研究費補助金",
        "経済産業省の研究開発",
        "挑戦的萌芽研究",
        "新学術領域研究",
        "特別研究員奨励費",
        "若手研究(B)",
        "萌芽研究",
        "特別推進研究",
        "通常の企業研究",
        "民間企業の自主研究",
        "大学との共同研究",
        "AMST先端計測分析技術"
    ]

    # スクレイパーを初期化
    scraper = ResearchMapResearchersScraper()

    print("=== 競争的研究課題判定テスト ===")
    print()

    for title in test_titles:
        # 競争的研究資金かどうかを判定
        competitive_keywords = [
            '科研費', 'jst', 'amst', '文部科学省', '厚生労働省', '経済産業省',
            '競争的', '基盤研究', '挑戦的研究', '新学術領域', '特別研究員',
            '若手研究', '萌芽研究', '基盤研究(a)', '基盤研究(b)', '基盤研究(c)',
            '挑戦的萌芽研究', '新学術領域研究', '特別推進研究'
        ]

        is_competitive = any(keyword.lower() in title.lower() for keyword in competitive_keywords)

        status = "✓ 競争的" if is_competitive else "✗ 非競争的"
        print(f"{status}: {title}")

    print()
    print("=== 実際のデータでのテスト ===")

    # 実際のテスト結果ファイルを読み込み
    try:
        with open('researchmap_researchers_test_2_results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"テスト対象研究者数: {data['total_researchers']}")
        print(f"取得された競争的研究課題数: {data['total_competitive_projects']}")
        print()

        for i, researcher in enumerate(data['researchers'], 1):
            print(f"研究者 {i}: {researcher['name']} ({researcher['affiliation']})")
            print(f"  全研究課題数: {len(researcher['all_projects'])}")
            print(f"  競争的研究課題数: {len(researcher['competitive_projects'])}")

            # 最初の3つの研究課題を表示
            for j, project in enumerate(researcher['all_projects'][:3], 1):
                status = "✓" if project['is_competitive'] else "✗"
                print(f"    {j}. {status} {project['title'][:50]}...")
            print()

    except FileNotFoundError:
        print("テスト結果ファイルが見つかりません。先にテストを実行してください。")

    print("=== 判定精度の検証 ===")
    print("以下の点を確認してください：")
    print("1. 科研費関連の研究課題が正しく競争的として判定されているか")
    print("2. JST、文部科学省などの研究課題が正しく判定されているか")
    print("3. 通常の企業研究が非競争的として判定されているか")
    print("4. 判定されなかった研究課題がある場合は、キーワードリストを更新する必要があるか")

if __name__ == "__main__":
    test_competitive_detection()
