#!/usr/bin/env python3
"""
PDF問題抽出＆難易度調整 類題生成ツール

PDFファイルから問題を抽出し、易しい/同レベル/難しい の3段階で類題を生成。
結果をWord文書(.docx)で出力する。

使い方:
    python generate.py 数学問題集.pdf --subject 数学
    python generate.py physics.pdf --subject 物理 --model gpt-4o --count 3
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from pdf_extractor import extract_text_from_pdf, split_into_problems
from problem_generator import generate_all_problems
from docx_writer import write_docx


def parse_args():
    parser = argparse.ArgumentParser(
        description="PDFから問題を抽出して難易度別の類題を生成するツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python generate.py 数学問題集.pdf --subject 数学
  python generate.py physics.pdf --subject 物理 --count 5
  python generate.py test.pdf --subject 化学 --model gpt-4o-mini

必要な環境変数:
  OPENAI_API_KEY  OpenAI APIキー
        """,
    )

    parser.add_argument(
        "pdf_path",
        help="入力PDFファイルのパス",
    )
    parser.add_argument(
        "--subject", "-s",
        required=True,
        help="科目名（数学、物理、化学、英語など）",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="出力ファイルパス（省略時: <入力ファイル名>_類題_<日付>.docx）",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=3,
        help="各難易度あたりの生成問題数（デフォルト: 3）",
    )
    parser.add_argument(
        "--model", "-m",
        default="gpt-4o",
        help="使用するOpenAIモデル（デフォルト: gpt-4o）",
    )
    parser.add_argument(
        "--max-problems",
        type=int,
        default=None,
        help="処理する最大問題数（省略時: 全問）",
    )

    return parser.parse_args()


def build_output_path(pdf_path: str, output: str | None) -> str:
    """出力ファイルパスを生成する"""
    if output:
        return output

    stem = Path(pdf_path).stem
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{stem}_類題_{date_str}.docx"


def main():
    args = parse_args()

    # --- 入力チェック ---
    if not os.path.isfile(args.pdf_path):
        print(f"エラー: ファイルが見つかりません: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    if not args.pdf_path.lower().endswith(".pdf"):
        print(f"警告: 拡張子が .pdf ではありません: {args.pdf_path}", file=sys.stderr)

    # --- API キーチェック ---
    if not os.environ.get("OPENAI_API_KEY"):
        print("エラー: 環境変数 OPENAI_API_KEY が設定されていません。", file=sys.stderr)
        print("  export OPENAI_API_KEY='sk-...'", file=sys.stderr)
        sys.exit(1)

    output_path = build_output_path(args.pdf_path, args.output)

    # --- Step 1: PDF読み取り ---
    print(f"📄 PDFを読み込み中: {args.pdf_path}")
    try:
        text = extract_text_from_pdf(args.pdf_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Step 2: 問題分割 ---
    problems = split_into_problems(text)
    if not problems:
        print("エラー: PDFから問題を検出できませんでした。", file=sys.stderr)
        sys.exit(1)

    if args.max_problems:
        problems = problems[:args.max_problems]

    print(f"📝 {len(problems)}問を検出しました")
    for p in problems:
        preview = p["text"][:60].replace("\n", " ")
        print(f"   問{p['number']}: {preview}...")

    # --- Step 3: 類題生成 ---
    print(f"\n🤖 類題を生成中（モデル: {args.model}）...")
    print(f"   各問題につき {args.count}問 × 3難易度 = {args.count * 3}問を生成")

    def on_progress(current, total):
        print(f"   [{current}/{total}] 問{problems[current-1]['number']} を処理中...")

    try:
        results = generate_all_problems(
            original_problems=problems,
            subject=args.subject,
            count_per_level=args.count,
            model=args.model,
            on_progress=on_progress,
        )
    except EnvironmentError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"API呼び出しエラー: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Step 4: DOCX出力 ---
    print(f"\n📊 Word文書を作成中: {output_path}")
    source_filename = Path(args.pdf_path).name

    try:
        write_docx(
            results=results,
            output_path=output_path,
            subject=args.subject,
            source_filename=source_filename,
        )
    except Exception as e:
        print(f"文書作成エラー: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 完了 ---
    total_generated = sum(len(r["generated"]) for r in results)
    print(f"\n✅ 完了！")
    print(f"   元の問題数: {len(problems)}")
    print(f"   生成した類題数: {total_generated}")
    print(f"   出力ファイル: {output_path}")


if __name__ == "__main__":
    main()
