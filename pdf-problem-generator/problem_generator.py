"""OpenAI APIを使って類題を生成するモジュール"""

import json
import os
from openai import OpenAI


DIFFICULTY_LABELS = {
    "easy": "基礎",
    "standard": "標準",
    "hard": "応用",
}

SYSTEM_PROMPT = """あなたは優秀な{subject}の教師です。
与えられた問題を分析し、指定された難易度で類題を生成してください。

# ルール
- 元の問題と同じ分野・トピックの類題を生成すること
- 各問題には必ず「解答」と「解説」を付けること
- 解説は生徒が理解しやすいように丁寧に書くこと
- 数式はプレーンテキストで表現すること（例: x^2 + 2x + 1 = 0）
- 必ず指定されたJSON形式で回答すること"""

GENERATION_PROMPT = """以下の問題の類題を生成してください。

【元の問題】
{problem_text}

【指示】
以下の3つの難易度でそれぞれ{count}問ずつ、合計{total}問を生成してください:
- 基礎（easy）: 元の問題より易しい。基本概念の確認レベル。
- 標準（standard）: 元の問題と同程度の難易度。
- 応用（hard）: 元の問題より難しい。発展的な思考力を要する。

必ず以下のJSON形式で回答してください。JSON以外は含めないでください:
{{
  "problems": [
    {{
      "difficulty": "easy",
      "problem": "問題文",
      "answer": "解答",
      "explanation": "解説"
    }},
    ...
  ]
}}"""


def get_client() -> OpenAI:
    """OpenAIクライアントを初期化する"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "環境変数 OPENAI_API_KEY が設定されていません。\n"
            "export OPENAI_API_KEY='your-api-key' を実行してください。"
        )
    return OpenAI(api_key=api_key)


def generate_similar_problems(
    problem_text: str,
    subject: str,
    count_per_level: int = 3,
    model: str = "gpt-4o",
) -> list[dict]:
    """1つの問題に対して難易度別の類題を生成する

    Args:
        problem_text: 元の問題テキスト
        subject: 科目名（数学、物理など）
        count_per_level: 各難易度あたりの生成数
        model: 使用するOpenAIモデル

    Returns:
        生成された問題のリスト。各要素は:
        {"difficulty": str, "problem": str, "answer": str, "explanation": str}
    """
    client = get_client()

    total = count_per_level * 3
    user_message = GENERATION_PROMPT.format(
        problem_text=problem_text,
        count=count_per_level,
        total=total,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(subject=subject)},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    problems = data.get("problems", [])
    if not problems:
        raise ValueError("APIから問題が返されませんでした。")

    # 難易度でソート: easy -> standard -> hard
    order = {"easy": 0, "standard": 1, "hard": 2}
    problems.sort(key=lambda p: order.get(p.get("difficulty", "standard"), 1))

    return problems


def generate_all_problems(
    original_problems: list[dict],
    subject: str,
    count_per_level: int = 3,
    model: str = "gpt-4o",
    on_progress=None,
) -> list[dict]:
    """全ての問題に対して類題を生成する

    Args:
        original_problems: 元の問題リスト [{"number": int, "text": str}, ...]
        subject: 科目名
        count_per_level: 各難易度あたりの生成数
        model: 使用するOpenAIモデル
        on_progress: 進捗コールバック fn(current, total)

    Returns:
        [{"original": dict, "generated": list[dict]}, ...]
    """
    results = []
    total = len(original_problems)

    for i, problem in enumerate(original_problems):
        if on_progress:
            on_progress(i + 1, total)

        generated = generate_similar_problems(
            problem_text=problem["text"],
            subject=subject,
            count_per_level=count_per_level,
            model=model,
        )

        results.append({
            "original": problem,
            "generated": generated,
        })

    return results
