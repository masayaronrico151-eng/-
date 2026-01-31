"""パッケージセットアップ"""

from setuptools import setup, find_packages

setup(
    name="pdf-problem-generator",
    version="1.0.0",
    description="PDF問題集から類題を自動生成するシステム",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "PyPDF2>=3.0.0",
        "python-docx>=1.1.0",
        "openai>=1.0.0",
        "anthropic>=0.30.0",
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pdf-gen=pdf_problem_generator.cli:main",
        ],
    },
)
