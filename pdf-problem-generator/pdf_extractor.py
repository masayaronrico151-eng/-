"""PDFファイルから問題テキストを抽出するモジュール"""

import re
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDFファイルから全テキストを抽出する"""
    try:
        reader = PdfReader(pdf_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"PDFファイルが見つかりません: {pdf_path}")
    except Exception as e:
        if "password" in str(e).lower() or "encrypt" in str(e).lower():
            raise ValueError(f"PDFがパスワードで保護されています: {pdf_path}")
        raise

    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text)

    if not pages:
        raise ValueError("PDFからテキストを抽出できませんでした。画像ベースのPDFの可能性があります。")

    return "\n\n".join(pages)


def split_into_problems(text: str) -> list[dict]:
    """抽出したテキストを個別の問題に分割する

    以下のパターンで問題を検出:
    - 「問1」「問題1」「Q1」「第1問」「(1)」「1.」「1)」など
    """
    patterns = [
        r'(?:^|\n)\s*(?:問題?\s*(\d+)|第\s*(\d+)\s*問|Q\.?\s*(\d+)|【問題?\s*(\d+)】)',
        r'(?:^|\n)\s*(?:(\d+)\s*[\.\)）]\s)',
        r'(?:^|\n)\s*(?:\((\d+)\)\s)',
    ]

    problems = []

    # まず最も構造化されたパターンで試す
    for pattern in patterns:
        matches = list(re.finditer(pattern, text, re.MULTILINE))
        if len(matches) >= 2:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                problem_text = text[start:end].strip()
                # 問題番号を取得
                groups = match.groups()
                num = next((g for g in groups if g is not None), str(i + 1))
                problems.append({
                    "number": int(num),
                    "text": problem_text,
                })
            break

    # パターンにマッチしない場合、段落ごとに分割
    if not problems:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and len(p.strip()) > 10]
        for i, para in enumerate(paragraphs, 1):
            problems.append({
                "number": i,
                "text": para,
            })

    return problems
