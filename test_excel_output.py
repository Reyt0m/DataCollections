import pandas as pd
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_excel_output():
    """
    Excel出力の形式と内容をテストする
    """
    print("=== Excel出力テスト ===")

    # テスト用のデータを作成
    test_data = {
        'total_researchers': 2,
        'processed_researchers': 2,
        'total_competitive_projects': 40,
        'researchers': [
            {
                'name': 'テスト研究者1',
                'english_name': 'Test Researcher 1',
                'affiliation': 'テスト企業株式会社',
                'position': '研究員',
                'researcher_id': 'test1',
                'researcher_url': 'https://researchmap.jp/test1',
                'competitive_project_count': 2,
                'competitive_projects': [
                    {
                        'title': '基盤研究(A) テスト研究1',
                        'project_url': 'https://researchmap.jp/test1/project1',
                        'project_id': '12345',
                        'is_competitive': True
                    },
                    {
                        'title': 'JST戦略的創造研究推進事業 テスト研究2',
                        'project_url': 'https://researchmap.jp/test1/project2',
                        'project_id': '67890',
                        'is_competitive': True
                    }
                ]
            },
            {
                'name': 'テスト研究者2',
                'english_name': 'Test Researcher 2',
                'affiliation': 'テスト企業株式会社',
                'position': '主任研究員',
                'researcher_id': 'test2',
                'researcher_url': 'https://researchmap.jp/test2',
                'competitive_project_count': 0,
                'competitive_projects': []
            }
        ],
        'scraped_at': '2025-08-03 16:00:00',
        'search_url': 'https://researchmap.jp/researchers?affiliation=test'
    }

    # スクレイパーのexport_to_excel関数をテスト
    from researchmap_researchers_scraper import ResearchMapResearchersScraper
    scraper = ResearchMapResearchersScraper()

    try:
        # Excelファイルを生成
        output_file = 'test_excel_output.xlsx'
        scraper.export_to_excel(test_data, output_file)

        print(f"Excelファイルが生成されました: {output_file}")

        # Excelファイルを読み込んで内容を確認
        with pd.ExcelFile(output_file) as xls:
            print(f"シート数: {len(xls.sheet_names)}")
            print(f"シート名: {xls.sheet_names}")

            # 競争的研究課題シートを確認
            df_projects = pd.read_excel(xls, '競争的研究課題')
            print(f"\n競争的研究課題シート:")
            print(f"行数: {len(df_projects)}")
            print(f"列数: {len(df_projects.columns)}")
            print(f"列名: {list(df_projects.columns)}")

            # 最初の数行を表示
            print("\n最初の3行:")
            print(df_projects.head(3).to_string())

            # サマリーシートを確認
            df_summary = pd.read_excel(xls, 'サマリー')
            print(f"\nサマリーシート:")
            print(f"行数: {len(df_summary)}")
            print(f"列数: {len(df_summary.columns)}")
            print("\nサマリー内容:")
            print(df_summary.to_string(index=False))

        # 実際のテスト結果ファイルも確認
        print(f"\n=== 実際のテスト結果ファイルの確認 ===")
        actual_file = 'researchmap_researchers_test_2_results.xlsx'

        if os.path.exists(actual_file):
            with pd.ExcelFile(actual_file) as xls:
                print(f"実際のファイル - シート数: {len(xls.sheet_names)}")
                print(f"実際のファイル - シート名: {xls.sheet_names}")

                # 競争的研究課題シートを確認
                df_actual = pd.read_excel(xls, '競争的研究課題')
                print(f"実際のファイル - 行数: {len(df_actual)}")
                print(f"実際のファイル - 列数: {len(df_actual.columns)}")

                # 統計情報
                print(f"\n統計情報:")
                print(f"研究者数: {df_actual['name'].nunique()}")
                print(f"研究課題数: {len(df_actual)}")
                print(f"競争的研究課題数: {len(df_actual[df_actual['project_title'].notna()])}")

                # 所属企業の分布
                print(f"\n所属企業の分布:")
                affiliation_counts = df_actual['affiliation'].value_counts()
                print(affiliation_counts)

        print(f"\n=== Excel出力テスト完了 ===")
        print("Excelファイルの形式と内容が正しく出力されていることを確認してください。")

    except Exception as e:
        print(f"Excel出力テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_output()
