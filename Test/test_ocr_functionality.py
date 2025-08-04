#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR機能テストスクリプト
実際の画像URLを使用してOCR機能をテストします
"""

import os
import sys
from portfolio_scraper import PortfolioScraper
import logging

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_ocr_with_sample_images():
    """サンプル画像でOCR機能をテスト"""

    # テスト用の画像URL（実際の会社ロゴなど）
    test_images = [
        # ジェネシア・ベンチャーズの画像
        "https://www.genesiaventures.com/wp-content/uploads/2019/07/ogimage.jpg",

        # 一般的な会社ロゴの例（実際のURLに置き換えてください）
        # "https://example.com/company1-logo.png",
        # "https://example.com/company2-logo.jpg",
    ]

    # スクレイパーの初期化（OCR機能付き）
    scraper = PortfolioScraper(headless=True, timeout=15, use_ocr=True)

    if not scraper.use_ocr:
        logger.error("OCR機能が利用できません。")
        return

    logger.info("OCR機能テストを開始します...")

    results = []

    for img_url in test_images:
        try:
            logger.info(f"画像を処理中: {img_url}")

            # OCR実行
            extracted_text = scraper.extract_text_from_image(img_url)

            result = {
                'image_url': img_url,
                'extracted_text': extracted_text,
                'success': extracted_text is not None,
                'text_length': len(extracted_text) if extracted_text else 0
            }

            results.append(result)

            if extracted_text:
                logger.info(f"OCR成功: {extracted_text}")
            else:
                logger.warning("OCR失敗: テキストを抽出できませんでした")

        except Exception as e:
            logger.error(f"画像処理エラー: {img_url} - {e}")
            results.append({
                'image_url': img_url,
                'extracted_text': None,
                'success': False,
                'error': str(e)
            })

    # 結果の表示
    print("\n" + "="*80)
    print("OCR機能テスト結果")
    print("="*80)

    successful_count = 0
    total_count = len(results)

    for result in results:
        print(f"\n画像URL: {result['image_url']}")
        print(f"  成功: {result['success']}")
        if result['success']:
            print(f"  抽出テキスト: {result['extracted_text']}")
            print(f"  テキスト長: {result['text_length']}")
            successful_count += 1
        else:
            if 'error' in result:
                print(f"  エラー: {result['error']}")

    print(f"\n" + "="*80)
    print(f"総合結果:")
    print(f"  処理した画像数: {total_count}")
    print(f"  成功した画像数: {successful_count}")
    print(f"  成功率: {successful_count/total_count*100:.1f}%")
    print("="*80)

    return results

def test_ocr_with_local_images():
    """ローカルの画像ファイルでOCR機能をテスト"""

    # ローカルの画像ファイルパス（存在する場合）
    local_images = [
        # "test_images/logo1.png",
        # "test_images/logo2.jpg",
    ]

    if not local_images or not any(os.path.exists(img) for img in local_images):
        logger.info("ローカル画像ファイルが見つかりません。")
        return

    scraper = PortfolioScraper(headless=True, timeout=15, use_ocr=True)

    if not scraper.use_ocr:
        logger.error("OCR機能が利用できません。")
        return

    logger.info("ローカル画像でのOCR機能テストを開始します...")

    results = []

    for img_path in local_images:
        if not os.path.exists(img_path):
            continue

        try:
            logger.info(f"ローカル画像を処理中: {img_path}")

            # ファイルURLとして処理
            file_url = f"file://{os.path.abspath(img_path)}"
            extracted_text = scraper.extract_text_from_image(file_url)

            result = {
                'image_path': img_path,
                'extracted_text': extracted_text,
                'success': extracted_text is not None,
                'text_length': len(extracted_text) if extracted_text else 0
            }

            results.append(result)

            if extracted_text:
                logger.info(f"OCR成功: {extracted_text}")
            else:
                logger.warning("OCR失敗: テキストを抽出できませんでした")

        except Exception as e:
            logger.error(f"ローカル画像処理エラー: {img_path} - {e}")

    return results

def test_ocr_quality_checks():
    """OCR品質チェック機能のテスト"""

    logger.info("OCR品質チェック機能のテストを開始します...")

    scraper = PortfolioScraper(headless=True, timeout=15, use_ocr=True)

    # テスト用の画像URL（品質が悪い画像）
    low_quality_images = [
        "https://via.placeholder.com/10x10",  # 非常に小さい画像
        "https://via.placeholder.com/1000x50",  # 極端に細長い画像
    ]

    for img_url in low_quality_images:
        try:
            logger.info(f"低品質画像をテスト中: {img_url}")

            # 画像をダウンロードして品質チェック
            response = scraper.session.get(img_url, timeout=10)
            response.raise_for_status()

            from PIL import Image
            import io

            img = Image.open(io.BytesIO(response.content))

            # 品質チェック
            is_good = scraper._is_image_quality_good(img)

            logger.info(f"画像品質チェック結果: {is_good}")

            if not is_good:
                logger.info("低品質画像が正しく除外されました")

        except Exception as e:
            logger.error(f"品質チェックエラー: {img_url} - {e}")

def main():
    """メイン関数"""

    print("OCR機能テストを開始します...")
    print("="*80)

    # 1. サンプル画像でのOCRテスト
    print("\n1. サンプル画像でのOCRテスト")
    print("-" * 50)
    results1 = test_ocr_with_sample_images()

    # 2. ローカル画像でのOCRテスト
    print("\n2. ローカル画像でのOCRテスト")
    print("-" * 50)
    results2 = test_ocr_with_local_images()

    # 3. OCR品質チェックテスト
    print("\n3. OCR品質チェックテスト")
    print("-" * 50)
    test_ocr_quality_checks()

    print("\n" + "="*80)
    print("OCR機能テスト完了")
    print("="*80)

    # 結果の保存
    import json
    all_results = {
        'sample_images': results1,
        'local_images': results2
    }

    with open('ocr_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\nOCRテスト結果を ocr_test_results.json に保存しました。")

if __name__ == "__main__":
    main()
