"""PDFから問題を抽出するモジュール"""

import re
from pathlib import Path

from PyPDF2 import PdfReader

from .models import Problem


class PDFExtractor:
    """PDFファイルから問題を抽出するクラス"""

    # 問題番号を検出する正規表現パターン群
    PROBLEM_PATTERNS = [
        # 「問1」「問 1」「問１」形式
        re.compile(r"問\s*(\d+|[１-９][０-９]*)"),
        # 「第1問」「第 1 問」形式
        re.compile(r"第\s*(\d+|[１-９][０-９]*)\s*問"),
        # 「(1)」「（1）」形式
        re.compile(r"[（(]\s*(\d+|[１-９][０-９]*)\s*[）)]"),
        # 「1.」「1）」形式
        re.compile(r"^(\d+)\s*[.）)]", re.MULTILINE),
        # 「Q1」「Q.1」形式
        re.compile(r"Q\.?\s*(\d+)", re.IGNORECASE),
        # 「【問題1】」形式
        re.compile(r"【\s*問題?\s*(\d+|[１-９][０-９]*)\s*】"),
    ]

    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDFファイルが見つかりません: {self.pdf_path}")
        if not self.pdf_path.suffix.lower() == ".pdf":
            raise ValueError(f"PDFファイルではありません: {self.pdf_path}")

    def extract_text(self) -> list[tuple[int, str]]:
        """PDFから全ページのテキストを抽出する

        Returns:
            list of (page_number, text) tuples (1-indexed)
        """
        pages = []
        reader = PdfReader(self.pdf_path)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((i, text))
        return pages

    def extract_problems(self) -> list[Problem]:
        """PDFから問題を抽出する

        Returns:
            抽出された Problem のリスト
        """
        pages = self.extract_text()
        if not pages:
            raise ValueError("PDFからテキストを抽出できませんでした。スキャンPDFの場合はOCR処理が必要です。")

        full_text = "\n".join(text for _, text in pages)

        # ページ番号のマッピングを作成
        page_map = self._build_page_map(pages)

        # 問題を検出・分割
        problems = self._split_into_problems(full_text, page_map)

        if not problems:
            # パターンで分割できない場合、段落単位で分割
            problems = self._split_by_paragraphs(full_text, page_map)

        return problems

    def _build_page_map(self, pages: list[tuple[int, str]]) -> dict[int, int]:
        """文字位置からページ番号へのマッピングを構築"""
        page_map = {}
        offset = 0
        for page_num, text in pages:
            for i in range(len(text)):
                page_map[offset + i] = page_num
            offset += len(text) + 1  # +1 for \n
        return page_map

    def _find_problem_boundaries(self, text: str) -> list[tuple[int, int, int]]:
        """問題の開始位置を検出する

        Returns:
            list of (position, problem_number, pattern_priority)
        """
        boundaries = []

        for priority, pattern in enumerate(self.PROBLEM_PATTERNS):
            for match in pattern.finditer(text):
                num_str = match.group(1)
                # 全角数字を半角に変換
                num_str = self._zen_to_han(num_str)
                try:
                    num = int(num_str)
                except ValueError:
                    continue
                boundaries.append((match.start(), num, priority))

        if not boundaries:
            return []

        # 最も多く出現するパターンを優先的に使用
        pattern_counts: dict[int, int] = {}
        for _, _, priority in boundaries:
            pattern_counts[priority] = pattern_counts.get(priority, 0) + 1

        best_priority = max(pattern_counts, key=lambda p: pattern_counts[p])

        # 同じパターンの境界だけをフィルタし、位置順にソート
        filtered = sorted(
            [(pos, num) for pos, num, pri in boundaries if pri == best_priority],
            key=lambda x: x[0],
        )

        # 重複する問題番号は最初の出現のみ保持
        seen: set[int] = set()
        unique = []
        for pos, num in filtered:
            if num not in seen:
                seen.add(num)
                unique.append((pos, num))

        return [(pos, num, best_priority) for pos, num in unique]

    def _split_into_problems(
        self, text: str, page_map: dict[int, int]
    ) -> list[Problem]:
        """パターンベースで問題を分割"""
        boundaries = self._find_problem_boundaries(text)
        if len(boundaries) < 1:
            return []

        problems = []
        for i, (pos, num, _) in enumerate(boundaries):
            # 次の問題の開始位置またはテキスト末尾まで
            end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
            problem_text = text[pos:end].strip()

            # 問題テキストをクリーニング
            problem_text = self._clean_problem_text(problem_text)

            if len(problem_text) < 5:
                continue

            page = page_map.get(pos, 1)
            problems.append(
                Problem(number=num, text=problem_text, source_page=page)
            )

        return problems

    def _split_by_paragraphs(
        self, text: str, page_map: dict[int, int]
    ) -> list[Problem]:
        """段落単位でフォールバック分割"""
        paragraphs = re.split(r"\n\s*\n", text)
        problems = []

        for i, para in enumerate(paragraphs, start=1):
            para = para.strip()
            if len(para) < 10:
                continue
            # 疑問文や命令文を含む段落を問題として扱う
            if any(kw in para for kw in ["？", "?", "求め", "答え", "計算", "解け", "述べ", "説明"]):
                problems.append(
                    Problem(number=i, text=self._clean_problem_text(para), source_page=1)
                )

        # 問題が見つからない場合は全段落を問題とみなす
        if not problems:
            for i, para in enumerate(paragraphs, start=1):
                para = para.strip()
                if len(para) >= 10:
                    problems.append(
                        Problem(number=i, text=self._clean_problem_text(para), source_page=1)
                    )

        return problems

    @staticmethod
    def _clean_problem_text(text: str) -> str:
        """問題テキストのクリーニング"""
        # 連続する空白行を1行に
        text = re.sub(r"\n{3,}", "\n\n", text)
        # 行頭・行末の空白を整理
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        return text.strip()

    @staticmethod
    def _zen_to_han(s: str) -> str:
        """全角数字を半角に変換"""
        zen = "０１２３４５６７８９"
        han = "0123456789"
        table = str.maketrans(zen, han)
        return s.translate(table)
