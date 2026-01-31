"""AI を使って類題を生成するモジュール"""

import json
import os
from typing import Optional

from .models import Difficulty, GeneratedProblem, Problem

# --- プロンプトテンプレート ---

SYSTEM_PROMPT = """\
あなたは優秀な教育者です。与えられた問題を分析し、指定された難易度の類題を生成してください。

ルール：
- 元の問題と同じ分野・単元の類題を作成する
- 数値や条件を変えつつ、問われている本質は同じにする
- 解答と解説は丁寧で分かりやすくする
- 解説では途中の計算過程や考え方も示す

出力は必ず以下のJSON形式で返してください（余計なテキストは含めない）：
{
  "problem_text": "問題文",
  "answer": "解答",
  "explanation": "解説（途中過程を含む）"
}
"""


def _build_user_prompt(problem: Problem, difficulty: Difficulty) -> str:
    """ユーザープロンプトを構築"""
    difficulty_instructions = {
        Difficulty.EASY: (
            "【基本レベル】元の問題より簡単にしてください。\n"
            "- 数値を単純にする\n"
            "- 手順を少なくする\n"
            "- ヒントとなる情報を問題文に含める"
        ),
        Difficulty.NORMAL: (
            "【標準レベル】元の問題と同程度の難易度にしてください。\n"
            "- 数値や条件を変更する\n"
            "- 問われる内容の本質は同じにする\n"
            "- 同程度の手順数を維持する"
        ),
        Difficulty.HARD: (
            "【発展レベル】元の問題より難しくしてください。\n"
            "- 複数の概念を組み合わせる\n"
            "- 手順を増やす、応用力を問う\n"
            "- 条件を複雑にする"
        ),
    }

    return (
        f"以下の問題の類題を生成してください。\n\n"
        f"--- 元の問題 ---\n"
        f"{problem.text}\n"
        f"--- ここまで ---\n\n"
        f"{difficulty_instructions[difficulty]}\n\n"
        f"JSON形式で出力してください。"
    )


class ProblemGenerator:
    """AI APIを使って類題を生成するクラス

    OpenAI API または Anthropic API を使用可能。
    環境変数で切り替え：
      - OPENAI_API_KEY が設定されている → OpenAI を使用
      - ANTHROPIC_API_KEY が設定されている → Anthropic を使用
      - GENERATOR_PROVIDER=openai|anthropic で明示的に指定可能
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = self._resolve_provider(provider)
        self.model = model or self._default_model()
        self._client = None

    def _resolve_provider(self, provider: Optional[str]) -> str:
        """使用するAPIプロバイダを決定"""
        if provider:
            return provider.lower()

        env_provider = os.environ.get("GENERATOR_PROVIDER", "").lower()
        if env_provider in ("openai", "anthropic"):
            return env_provider

        if os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"

        raise EnvironmentError(
            "APIキーが設定されていません。\n"
            "以下のいずれかの環境変数を設定してください:\n"
            "  export OPENAI_API_KEY='your-key'\n"
            "  export ANTHROPIC_API_KEY='your-key'"
        )

    def _default_model(self) -> str:
        if self.provider == "anthropic":
            return "claude-sonnet-4-20250514"
        return "gpt-4o"

    def _get_openai_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        return self._client

    def _get_anthropic_client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic()
        return self._client

    def _call_openai(self, problem: Problem, difficulty: Difficulty) -> str:
        """OpenAI API を呼び出す"""
        client = self._get_openai_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(problem, difficulty)},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    def _call_anthropic(self, problem: Problem, difficulty: Difficulty) -> str:
        """Anthropic API を呼び出す"""
        client = self._get_anthropic_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_user_prompt(problem, difficulty)},
            ],
            temperature=0.7,
        )
        return response.content[0].text

    def generate(
        self, problem: Problem, difficulty: Difficulty
    ) -> GeneratedProblem:
        """1つの問題に対して指定難易度の類題を生成する"""
        if self.provider == "anthropic":
            raw = self._call_anthropic(problem, difficulty)
        else:
            raw = self._call_openai(problem, difficulty)

        # JSONブロックを抽出（```json ... ``` 形式にも対応）
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:])
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        data = json.loads(raw)

        return GeneratedProblem(
            original_number=problem.number,
            difficulty=difficulty,
            problem_text=data["problem_text"],
            answer=data["answer"],
            explanation=data["explanation"],
        )

    def generate_all_levels(self, problem: Problem) -> list[GeneratedProblem]:
        """1つの問題に対して全難易度の類題を生成する"""
        results = []
        for diff in Difficulty:
            generated = self.generate(problem, diff)
            results.append(generated)
        return results
