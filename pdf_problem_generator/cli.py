"""コマンドラインインターフェース"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .extractor import PDFExtractor
from .generator import ProblemGenerator
from .models import Difficulty, ProblemSet
from .word_exporter import WordExporter

console = Console()


def print_banner():
    """バナーを表示"""
    console.print(
        Panel(
            "[bold cyan]PDF 類題自動生成システム[/bold cyan]\n"
            "PDFの問題集から、難易度別の類題を自動生成します",
            border_style="cyan",
        )
    )


@click.group()
@click.version_option(version="1.0.0")
def main():
    """PDF問題集から類題を自動生成するツール"""
    pass


@main.command()
@click.argument("pdf_path", type=click.Path(exists=True, path_type=Path))
def extract(pdf_path: Path):
    """PDFから問題を抽出して一覧表示する"""
    print_banner()

    console.print(f"\n[bold]PDF読み込み中:[/bold] {pdf_path}")

    try:
        extractor = PDFExtractor(pdf_path)
        problems = extractor.extract_problems()
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        sys.exit(1)

    if not problems:
        console.print("[yellow]問題が見つかりませんでした。[/yellow]")
        sys.exit(0)

    table = Table(title=f"抽出された問題 ({len(problems)}件)")
    table.add_column("No.", style="bold", width=6)
    table.add_column("ページ", width=8)
    table.add_column("問題文（冒頭）", max_width=70)

    for p in problems:
        preview = p.text[:80].replace("\n", " ")
        if len(p.text) > 80:
            preview += "..."
        table.add_row(str(p.number), str(p.source_page), preview)

    console.print(table)
    console.print(f"\n[green]合計 {len(problems)} 問を抽出しました。[/green]")


@main.command()
@click.argument("pdf_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="出力先Wordファイルパス（デフォルト: 入力ファイル名_類題.docx）",
)
@click.option(
    "-d", "--difficulty",
    type=click.Choice(["all", "easy", "normal", "hard"]),
    default="all",
    help="生成する難易度（デフォルト: all = 全3レベル）",
)
@click.option(
    "-n", "--numbers",
    type=str,
    default=None,
    help="生成対象の問題番号（カンマ区切り, 例: 1,3,5）。省略時は全問題",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic"]),
    default=None,
    help="使用するAIプロバイダ（デフォルト: 環境変数から自動判定）",
)
@click.option(
    "--model",
    type=str,
    default=None,
    help="使用するモデル名（例: gpt-4o, claude-sonnet-4-20250514）",
)
@click.option(
    "--title",
    type=str,
    default="類題集",
    help="Word文書のタイトル",
)
@click.option(
    "--no-originals",
    is_flag=True,
    help="元問題を含めない",
)
def generate(
    pdf_path: Path,
    output: Path | None,
    difficulty: str,
    numbers: str | None,
    provider: str | None,
    model: str | None,
    title: str,
    no_originals: bool,
):
    """PDFから問題を抽出し、類題を生成してWord文書に出力する"""
    print_banner()

    # --- 1. PDF読み込み ---
    console.print(f"\n[bold]Step 1/3:[/bold] PDF読み込み中... [dim]{pdf_path}[/dim]")

    try:
        extractor = PDFExtractor(pdf_path)
        problems = extractor.extract_problems()
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        sys.exit(1)

    if not problems:
        console.print("[yellow]問題が見つかりませんでした。[/yellow]")
        sys.exit(0)

    console.print(f"  → [green]{len(problems)} 問を抽出しました[/green]")

    # 問題番号のフィルタリング
    if numbers:
        target_nums = set()
        for part in numbers.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                target_nums.update(range(int(start), int(end) + 1))
            else:
                target_nums.add(int(part))
        problems = [p for p in problems if p.number in target_nums]
        if not problems:
            console.print("[yellow]指定された番号の問題が見つかりませんでした。[/yellow]")
            sys.exit(0)
        console.print(f"  → 対象: {len(problems)} 問")

    # 難易度の決定
    if difficulty == "all":
        difficulties = list(Difficulty)
    else:
        difficulties = [Difficulty(difficulty)]

    total_tasks = len(problems) * len(difficulties)
    console.print(
        f"\n[bold]Step 2/3:[/bold] 類題生成中... "
        f"({len(problems)}問 × {len(difficulties)}レベル = {total_tasks}題)"
    )

    # --- 2. 類題生成 ---
    try:
        generator = ProblemGenerator(provider=provider, model=model)
    except EnvironmentError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    console.print(f"  [dim]プロバイダ: {generator.provider} / モデル: {generator.model}[/dim]")

    problem_sets: list[ProblemSet] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[bold green]{task.completed}/{task.total}[/bold green]"),
        console=console,
    ) as progress:
        task = progress.add_task("生成中", total=total_tasks)

        for prob in problems:
            ps = ProblemSet(original=prob)

            for diff in difficulties:
                progress.update(
                    task,
                    description=f"問{prob.number}【{diff.label_ja}】生成中",
                )
                try:
                    gen = generator.generate(prob, diff)
                    ps.variants.append(gen)
                except Exception as e:
                    console.print(
                        f"\n  [yellow]警告: 問{prob.number}【{diff.label_ja}】"
                        f"の生成に失敗: {e}[/yellow]"
                    )
                progress.advance(task)

            if ps.variants:
                problem_sets.append(ps)

    if not problem_sets:
        console.print("[red]類題を1つも生成できませんでした。[/red]")
        sys.exit(1)

    total_generated = sum(len(ps.variants) for ps in problem_sets)
    console.print(f"  → [green]{total_generated} 題を生成しました[/green]")

    # --- 3. Word出力 ---
    if output is None:
        output = pdf_path.with_name(f"{pdf_path.stem}_類題.docx")

    console.print(f"\n[bold]Step 3/3:[/bold] Word文書出力中... [dim]{output}[/dim]")

    try:
        exporter = WordExporter()
        out_path = exporter.export(
            problem_sets,
            output,
            title=title,
            include_originals=not no_originals,
        )
    except Exception as e:
        console.print(f"[red]出力エラー: {e}[/red]")
        sys.exit(1)

    console.print(f"  → [green]保存完了: {out_path}[/green]")

    # 完了サマリー
    console.print()
    summary = Table(title="生成サマリー", show_header=True)
    summary.add_column("項目", style="bold")
    summary.add_column("値")
    summary.add_row("入力PDF", str(pdf_path))
    summary.add_row("出力ファイル", str(out_path))
    summary.add_row("元問題数", str(len(problems)))
    summary.add_row("生成類題数", str(total_generated))
    summary.add_row(
        "難易度",
        ", ".join(d.label_ja for d in difficulties),
    )
    summary.add_row("AIプロバイダ", f"{generator.provider} ({generator.model})")
    console.print(summary)
    console.print("\n[bold green]完了しました！[/bold green]")


if __name__ == "__main__":
    main()
