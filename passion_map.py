#!/usr/bin/env python3
"""
偏愛マップ作成アプリ - Passion Map Creator
高校生向け探究学習支援ツール

自分の「好き」を深掘りして、視覚的なマップにまとめよう！
探究学習のテーマ発見をサポートします。
"""

import json
import os
import sys
import uuid
import textwrap
import random
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple

# ============================================================
#  グラフ可視化ライブラリ
# ============================================================
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import networkx as nx
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False

# ============================================================
#  定数
# ============================================================

APP_NAME = "偏愛マップ作成アプリ"
VERSION = "1.0.0"
DEFAULT_SAVE_DIR = os.path.join(os.path.expanduser("~"), "passion_map_data")
SEPARATOR = "=" * 56
THIN_SEP = "-" * 56

# ============================================================
#  カテゴリー定義
# ============================================================

CATEGORIES: Dict[str, dict] = {
    "趣味・娯楽": {
        "keywords": [
            "ゲーム", "音楽", "映画", "アニメ", "漫画", "読書", "料理",
            "旅行", "写真", "ダンス", "歌", "カラオケ", "推し", "動画",
            "ショッピング", "ファッション", "コスメ", "手芸", "絵",
            "イラスト", "小説", "ドラマ", "バラエティ", "お笑い",
            "ライブ", "フェス", "カフェ", "食べ歩き", "スイーツ",
            "ボードゲーム", "カードゲーム", "コレクション", "鉄道",
            "キャンプ", "釣り", "園芸", "DIY", "楽器", "ピアノ",
            "ギター", "ドラム", "バンド", "配信", "実況", "コスプレ",
            "聖地巡礼", "グッズ", "ぬいぐるみ", "フィギュア",
        ],
        "color": "#FF6B6B",
        "emoji": "🎮",
    },
    "学問・知識": {
        "keywords": [
            "数学", "科学", "物理", "化学", "生物", "歴史", "地理",
            "英語", "国語", "文学", "哲学", "心理学", "経済", "政治",
            "法律", "医学", "天文", "宇宙", "実験", "研究", "勉強",
            "言語", "考古学", "建築", "統計", "論理", "倫理",
            "社会学", "人類学", "教育", "学問",
        ],
        "color": "#4ECDC4",
        "emoji": "📚",
    },
    "スポーツ・運動": {
        "keywords": [
            "サッカー", "野球", "バスケ", "テニス", "バレー", "陸上",
            "水泳", "バドミントン", "卓球", "柔道", "剣道", "空手",
            "スキー", "スノボ", "サーフィン", "スケボー", "ヨガ",
            "筋トレ", "ランニング", "マラソン", "体操", "チア",
            "部活", "応援", "スポーツ", "運動", "登山", "ハイキング",
            "ボルダリング", "格闘技", "弓道", "合気道", "フットサル",
        ],
        "color": "#45B7D1",
        "emoji": "⚽",
    },
    "人間関係": {
        "keywords": [
            "友達", "家族", "恋愛", "先生", "先輩", "後輩", "仲間",
            "チーム", "コミュニティ", "ボランティア", "人助け", "会話",
            "コミュニケーション", "つながり", "出会い", "協力", "信頼",
            "絆", "思いやり", "共感",
        ],
        "color": "#96CEB4",
        "emoji": "👫",
    },
    "価値観・信念": {
        "keywords": [
            "自由", "平等", "正義", "平和", "幸せ", "成長", "挑戦",
            "努力", "感謝", "優しさ", "誠実", "創造", "多様性",
            "持続可能", "倫理", "道徳", "尊重", "美しさ", "真実",
            "個性", "自分らしさ", "公平", "責任",
        ],
        "color": "#FFEAA7",
        "emoji": "💎",
    },
    "将来・キャリア": {
        "keywords": [
            "夢", "目標", "将来", "仕事", "職業", "起業", "留学",
            "大学", "資格", "スキル", "キャリア", "独立", "海外",
            "グローバル", "リーダー", "社長", "医者", "弁護士",
            "教師", "エンジニア", "デザイナー", "クリエイター",
            "アーティスト", "稼ぐ", "就職", "進学", "受験",
        ],
        "color": "#DDA0DD",
        "emoji": "🚀",
    },
    "自然・環境": {
        "keywords": [
            "動物", "植物", "自然", "環境", "エコ", "海", "山", "森",
            "花", "天気", "季節", "星", "地球", "生態系", "保護",
            "農業", "食", "ペット", "猫", "犬", "鳥", "魚", "虫",
            "サステナブル", "気候", "リサイクル",
        ],
        "color": "#98D8C8",
        "emoji": "🌿",
    },
    "社会・文化": {
        "keywords": [
            "社会", "文化", "国際", "ニュース", "伝統", "祭り",
            "地域", "まちづくり", "福祉", "格差", "人権", "ジェンダー",
            "多文化", "異文化", "宗教", "民族", "メディア", "報道",
            "世界", "貧困", "難民", "防災", "復興",
        ],
        "color": "#F7DC6F",
        "emoji": "🌍",
    },
    "テクノロジー": {
        "keywords": [
            "IT", "AI", "プログラミング", "アプリ", "ロボット", "VR",
            "AR", "ゲーム開発", "Web", "データ", "サイバー", "IoT",
            "ドローン", "3D", "メタバース", "ブロックチェーン",
            "コンピュータ", "ハッキング", "セキュリティ", "機械学習",
            "コード", "開発", "テクノロジー", "技術",
        ],
        "color": "#BB8FCE",
        "emoji": "💻",
    },
    "芸術・表現": {
        "keywords": [
            "美術", "アート", "デザイン", "演劇", "書道", "陶芸",
            "彫刻", "クリエイティブ", "創作", "表現", "映像",
            "アニメーション", "CGI", "舞台", "ミュージカル", "詩",
            "俳句", "短歌", "作曲", "編曲", "動画編集",
        ],
        "color": "#F1948A",
        "emoji": "🎨",
    },
}

# その他カテゴリー (マッチしない場合)
OTHER_CATEGORY = {
    "name": "その他",
    "color": "#BDC3C7",
    "emoji": "✨",
}

# ============================================================
#  インタビュー質問テンプレート
# ============================================================

INITIAL_QUESTIONS = [
    {
        "id": "likes",
        "question": "あなたが「好きなこと」「ハマっていること」を教えて！",
        "hint": (
            "例: 音楽を聴くこと、バスケ、料理、アニメ、数学...\n"
            "      1つずつ入力してね。何個でもOK！(終わったら Enter だけ押してね)"
        ),
        "min_items": 2,
    },
    {
        "id": "interests",
        "question": "最近「気になっていること」「もっと知りたいこと」は？",
        "hint": (
            "例: AIの未来、環境問題、心理学、異文化交流...\n"
            "      なんとなく気になる程度でも大丈夫！"
        ),
        "min_items": 2,
    },
    {
        "id": "future",
        "question": "「将来やってみたいこと」「なりたい自分」を教えて！",
        "hint": (
            "例: 海外に住みたい、起業したい、人の役に立ちたい...\n"
            "      夢は大きくても小さくてもOK！"
        ),
        "min_items": 1,
    },
]

DEEPDIVE_QUESTIONS = [
    "「{item}」が好き／気になるんだね！ なぜ？きっかけは何だった？",
    "「{item}」に関して、どんな時に一番ワクワクする？",
    "「{item}」について、もっと深く知りたいことはある？",
    "「{item}」を通じて、どんな自分になりたい？",
    "もし「{item}」で誰かを幸せにできるとしたら、何をする？",
    "「{item}」に関連して、他に好きなこと・興味があることは？",
    "「{item}」の魅力を友達に伝えるとしたら、なんて言う？",
]

# ============================================================
#  探究テーマ提案テンプレート
# ============================================================

THEME_TEMPLATES = [
    "「{a}」×「{b}」で新しい価値を生み出すには？",
    "「{a}」の視点から「{b}」の課題を解決するアイデア",
    "「{a}」と「{b}」の意外な共通点を探る",
    "「{a}」の技術／考え方を「{b}」に応用したら？",
    "高校生が「{a}」と「{b}」で地域に貢献する方法",
    "「{a}」×「{b}」で SDGs に取り組む",
    "「{a}」が好きな人が「{b}」を学ぶ意味とは？",
    "未来の「{a}」と「{b}」 ── 10年後はどうなっている？",
]


# ============================================================
#  データモデル
# ============================================================

@dataclass
class PassionItem:
    """偏愛マップの1つの項目"""
    id: str = ""
    name: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    depth: int = 0          # 0=トップ, 1=深掘り1段目, ...
    parent_id: Optional[str] = None
    details: Dict[str, str] = field(default_factory=dict)
    phase: str = ""         # likes / interests / future / deepdive
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Connection:
    """項目間のつながり"""
    item1_id: str = ""
    item2_id: str = ""
    reason: str = ""
    strength: float = 1.0


@dataclass
class PassionMapData:
    """偏愛マップ全体のデータ"""
    user_name: str = ""
    items: Dict[str, dict] = field(default_factory=dict)
    connections: List[dict] = field(default_factory=list)
    suggested_themes: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    interview_state: Dict = field(default_factory=dict)

    def __post_init__(self):
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now


# ============================================================
#  ユーティリティ
# ============================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str = ""):
    """ヘッダーを表示"""
    print()
    print(SEPARATOR)
    if title:
        print(f"  {title}")
    else:
        print(f"  {APP_NAME} v{VERSION}")
    print(SEPARATOR)
    print()


def print_section(title: str):
    print()
    print(f"  --- {title} ---")
    print()


def print_wrapped(text: str, indent: int = 2):
    prefix = " " * indent
    for line in text.split("\n"):
        wrapped = textwrap.fill(line, width=52, initial_indent=prefix,
                                subsequent_indent=prefix)
        print(wrapped)


def ask_input(prompt: str, allow_empty: bool = False) -> str:
    """ユーザー入力を取得"""
    while True:
        try:
            value = input(f"  > {prompt}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return ""
        if value or allow_empty:
            return value
        print("  (何か入力してね！)")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        ans = input(f"  > {prompt}{suffix}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not ans:
        return default
    return ans in ("y", "yes", "はい", "うん")


def ask_choice(prompt: str, choices: List[str]) -> int:
    """番号で選択肢を選ばせる。戻り値は 0-indexed。"""
    for i, c in enumerate(choices, 1):
        print(f"    {i}. {c}")
    print()
    while True:
        try:
            raw = input(f"  > {prompt} (番号): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return -1
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return idx
        print(f"  (1〜{len(choices)} の番号を入力してね！)")


# ============================================================
#  カテゴリー分類
# ============================================================

class Categorizer:
    """テキストからカテゴリーとタグを推定する"""

    @staticmethod
    def categorize(text: str) -> str:
        scores: Dict[str, int] = {}
        for cat_name, cat_info in CATEGORIES.items():
            score = sum(1 for kw in cat_info["keywords"] if kw in text)
            if score > 0:
                scores[cat_name] = score
        if scores:
            return max(scores, key=scores.get)
        return OTHER_CATEGORY["name"]

    @staticmethod
    def get_tags(text: str) -> List[str]:
        tags = []
        for cat_info in CATEGORIES.values():
            for kw in cat_info["keywords"]:
                if kw in text and kw not in tags:
                    tags.append(kw)
        return tags

    @staticmethod
    def get_color(category: str) -> str:
        if category in CATEGORIES:
            return CATEGORIES[category]["color"]
        return OTHER_CATEGORY["color"]

    @staticmethod
    def get_emoji(category: str) -> str:
        if category in CATEGORIES:
            return CATEGORIES[category]["emoji"]
        return OTHER_CATEGORY["emoji"]


# ============================================================
#  つながり分析
# ============================================================

class ConnectionAnalyzer:
    """項目間のつながりを分析し、探究テーマを提案する"""

    @staticmethod
    def find_connections(items: Dict[str, dict]) -> List[Connection]:
        connections: List[Connection] = []
        item_list = list(items.values())

        for i in range(len(item_list)):
            for j in range(i + 1, len(item_list)):
                a = item_list[i]
                b = item_list[j]

                a_name = a.get("name", "")
                b_name = b.get("name", "")
                a_cat = a.get("category", "")
                b_cat = b.get("category", "")
                a_tags = set(a.get("tags", []))
                b_tags = set(b.get("tags", []))
                a_id = a.get("id", "")
                b_id = b.get("id", "")
                a_parent = a.get("parent_id")
                b_parent = b.get("parent_id")

                # 親子関係
                if a_parent == b_id or b_parent == a_id:
                    connections.append(Connection(
                        item1_id=a_id, item2_id=b_id,
                        reason="深掘りのつながり", strength=1.0,
                    ))
                    continue

                # 同カテゴリー
                if (a_cat and a_cat == b_cat
                        and a_cat != OTHER_CATEGORY["name"]
                        and a_parent != b_id and b_parent != a_id):
                    connections.append(Connection(
                        item1_id=a_id, item2_id=b_id,
                        reason=f"同じ分野「{a_cat}」", strength=0.7,
                    ))

                # 共通タグ
                shared = a_tags & b_tags
                if shared:
                    connections.append(Connection(
                        item1_id=a_id, item2_id=b_id,
                        reason=f"共通ワード: {', '.join(list(shared)[:3])}",
                        strength=min(1.0, len(shared) * 0.3),
                    ))

                # 名前に共通部分文字列 (3文字以上)
                common_sub = ConnectionAnalyzer._common_substring(
                    a_name, b_name, min_len=3
                )
                if common_sub:
                    connections.append(Connection(
                        item1_id=a_id, item2_id=b_id,
                        reason=f"共通キーワード「{common_sub}」",
                        strength=0.5,
                    ))

        # 重複除去
        seen = set()
        unique = []
        for c in connections:
            key = tuple(sorted([c.item1_id, c.item2_id]))
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    @staticmethod
    def _common_substring(a: str, b: str, min_len: int = 3) -> str:
        """2 つの文字列の最長共通部分文字列を返す (min_len 未満なら空)"""
        best = ""
        for i in range(len(a)):
            for j in range(i + min_len, len(a) + 1):
                sub = a[i:j]
                if sub in b and len(sub) > len(best):
                    best = sub
        return best

    @staticmethod
    def suggest_themes(items: Dict[str, dict]) -> List[str]:
        """項目を組み合わせて探究テーマを提案する"""
        themes: List[str] = []
        top_items = [
            it for it in items.values() if it.get("depth", 0) == 0
        ]
        if len(top_items) < 2:
            return themes

        # カテゴリーごとにグループ化
        by_cat: Dict[str, List[dict]] = {}
        for it in top_items:
            cat = it.get("category", OTHER_CATEGORY["name"])
            by_cat.setdefault(cat, []).append(it)

        # 異なるカテゴリーの組み合わせからテーマ生成
        cats = list(by_cat.keys())
        pairs_used = set()
        for i in range(len(cats)):
            for j in range(i + 1, len(cats)):
                a_items = by_cat[cats[i]]
                b_items = by_cat[cats[j]]
                a = random.choice(a_items)
                b = random.choice(b_items)
                pair_key = tuple(sorted([a["name"], b["name"]]))
                if pair_key in pairs_used:
                    continue
                pairs_used.add(pair_key)
                tmpl = random.choice(THEME_TEMPLATES)
                themes.append(tmpl.format(a=a["name"], b=b["name"]))
                if len(themes) >= 8:
                    break
            if len(themes) >= 8:
                break

        # 同カテゴリー内でもテーマ生成
        for cat, cat_items in by_cat.items():
            if len(cat_items) >= 2 and len(themes) < 12:
                pair = random.sample(cat_items, 2)
                pair_key = tuple(sorted([pair[0]["name"], pair[1]["name"]]))
                if pair_key not in pairs_used:
                    pairs_used.add(pair_key)
                    tmpl = random.choice(THEME_TEMPLATES)
                    themes.append(tmpl.format(
                        a=pair[0]["name"], b=pair[1]["name"]
                    ))

        return themes


# ============================================================
#  データ管理 (JSON 永続化)
# ============================================================

class DataManager:
    """JSON ファイルでの保存・読み込みを管理"""

    def __init__(self, save_dir: str = DEFAULT_SAVE_DIR):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def _filepath(self, user_name: str) -> str:
        safe = "".join(
            c if c.isalnum() or c in ("_", "-") else "_"
            for c in user_name
        )
        return os.path.join(self.save_dir, f"passion_map_{safe}.json")

    def save(self, data: PassionMapData) -> str:
        data.updated_at = datetime.now().isoformat()
        path = self._filepath(data.user_name)
        payload = {
            "user_name": data.user_name,
            "items": data.items,
            "connections": [asdict(c) if isinstance(c, Connection)
                           else c for c in data.connections],
            "suggested_themes": data.suggested_themes,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
            "interview_state": data.interview_state,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path

    def load(self, user_name: str) -> Optional[PassionMapData]:
        path = self._filepath(user_name)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return PassionMapData(**raw)

    def list_saves(self) -> List[str]:
        saves = []
        if not os.path.isdir(self.save_dir):
            return saves
        for fname in sorted(os.listdir(self.save_dir)):
            if fname.startswith("passion_map_") and fname.endswith(".json"):
                try:
                    fpath = os.path.join(self.save_dir, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    name = d.get("user_name", fname)
                    updated = d.get("updated_at", "")[:16].replace("T", " ")
                    n_items = len(d.get("items", {}))
                    saves.append(f"{name}  ({n_items}項目, {updated})")
                except Exception:
                    pass
        return saves

    def list_save_names(self) -> List[str]:
        names = []
        if not os.path.isdir(self.save_dir):
            return names
        for fname in sorted(os.listdir(self.save_dir)):
            if fname.startswith("passion_map_") and fname.endswith(".json"):
                try:
                    fpath = os.path.join(self.save_dir, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    names.append(d.get("user_name", ""))
                except Exception:
                    pass
        return names


# ============================================================
#  可視化 (matplotlib + networkx)
# ============================================================

class Visualizer:
    """偏愛マップをネットワークグラフとして描画する"""

    @staticmethod
    def _setup_font():
        """日本語フォントを探して設定する"""
        japanese_fonts = [
            "IPAGothic", "IPAPGothic", "IPAexGothic",
            "Noto Sans CJK JP", "Noto Sans JP",
            "TakaoPGothic", "TakaoGothic",
            "VL PGothic", "VL Gothic",
            "M+ 1p", "Meiryo", "MS Gothic", "Yu Gothic",
            "Hiragino Sans", "Hiragino Kaku Gothic Pro",
        ]
        available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
        for font_name in japanese_fonts:
            if font_name in available:
                plt.rcParams["font.family"] = font_name
                return font_name

        # フォールバック: sans-serif に日本語フォントを追加
        for font_name in japanese_fonts:
            if font_name in available:
                plt.rcParams["font.sans-serif"] = [font_name] + \
                    plt.rcParams.get("font.sans-serif", [])
                return font_name

        return None

    @staticmethod
    def generate(
        items: Dict[str, dict],
        connections: List[Connection],
        user_name: str = "",
        output_path: str = "passion_map.png",
    ) -> str:
        if not HAS_VISUALIZATION:
            return ""

        font_name = Visualizer._setup_font()

        G = nx.Graph()

        # ノードの追加
        for item_id, item in items.items():
            G.add_node(
                item_id,
                label=item.get("name", "?"),
                category=item.get("category", OTHER_CATEGORY["name"]),
                depth=item.get("depth", 0),
            )

        # エッジの追加
        for conn in connections:
            c = conn if isinstance(conn, Connection) else Connection(**conn)
            if c.item1_id in G.nodes and c.item2_id in G.nodes:
                G.add_edge(
                    c.item1_id, c.item2_id,
                    reason=c.reason,
                    weight=c.strength,
                )

        if len(G.nodes) == 0:
            return ""

        # レイアウト
        if len(G.nodes) <= 3:
            pos = nx.spring_layout(G, k=3.0, seed=42)
        else:
            try:
                pos = nx.kamada_kawai_layout(G)
            except ImportError:
                pos = nx.spring_layout(G, k=2.0, iterations=100, seed=42)

        # 図の作成
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")

        # エッジ描画
        edge_colors = []
        edge_widths = []
        for u, v, data in G.edges(data=True):
            edge_colors.append("#ffffff30")
            edge_widths.append(data.get("weight", 1.0) * 1.5)

        if G.edges():
            nx.draw_networkx_edges(
                G, pos, ax=ax,
                edge_color=edge_colors,
                width=edge_widths,
                alpha=0.4,
                style="dashed",
            )

        # ノード描画
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            cat = G.nodes[node].get("category", OTHER_CATEGORY["name"])
            color = Categorizer.get_color(cat)
            node_colors.append(color)
            depth = G.nodes[node].get("depth", 0)
            degree = G.degree(node) if G.degree(node) > 0 else 1
            base_size = 2000 if depth == 0 else 1200
            node_sizes.append(base_size + degree * 300)

        nx.draw_networkx_nodes(
            G, pos, ax=ax,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.9,
            edgecolors="white",
            linewidths=2,
        )

        # ラベル描画
        labels = {n: G.nodes[n]["label"] for n in G.nodes()}
        nx.draw_networkx_labels(
            G, pos, labels, ax=ax,
            font_size=10,
            font_color="white",
            font_weight="bold",
            **({"font_family": font_name} if font_name else {}),
        )

        # 凡例
        legend_handles = []
        cats_used = set(
            G.nodes[n].get("category", "") for n in G.nodes()
        )
        for cat_name in cats_used:
            if cat_name in CATEGORIES:
                emoji = CATEGORIES[cat_name]["emoji"]
                color = CATEGORIES[cat_name]["color"]
            elif cat_name == OTHER_CATEGORY["name"]:
                emoji = OTHER_CATEGORY["emoji"]
                color = OTHER_CATEGORY["color"]
            else:
                continue
            # 画像ではemoji非対応フォントが多いためテキストのみ
            legend_handles.append(
                mpatches.Patch(
                    color=color,
                    label=f"■ {cat_name}",
                )
            )
        if legend_handles:
            legend = ax.legend(
                handles=legend_handles,
                loc="upper left",
                framealpha=0.7,
                facecolor="#16213e",
                edgecolor="white",
                fontsize=9,
                **({"prop": {"family": font_name}} if font_name else {}),
            )
            for text in legend.get_texts():
                text.set_color("white")

        title_text = f"{user_name} の偏愛マップ" if user_name else "偏愛マップ"
        ax.set_title(
            title_text,
            fontsize=18,
            color="white",
            fontweight="bold",
            pad=20,
            **({"fontfamily": font_name} if font_name else {}),
        )
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        return output_path


# ============================================================
#  インタビューエンジン
# ============================================================

class InterviewEngine:
    """対話形式で質問を行い、偏愛項目を引き出す"""

    def __init__(self, data: PassionMapData, data_mgr: DataManager):
        self.data = data
        self.data_mgr = data_mgr
        self.categorizer = Categorizer()

    def _add_item(
        self,
        name: str,
        phase: str,
        depth: int = 0,
        parent_id: Optional[str] = None,
        details: Optional[Dict[str, str]] = None,
    ) -> dict:
        item = PassionItem(
            name=name,
            category=self.categorizer.categorize(name),
            tags=self.categorizer.get_tags(name),
            depth=depth,
            parent_id=parent_id,
            phase=phase,
            details=details or {},
        )
        item_dict = asdict(item)
        self.data.items[item.id] = item_dict
        return item_dict

    def run_initial_questions(self):
        """初回質問フェーズ"""
        state = self.data.interview_state
        start_idx = state.get("initial_q_idx", 0)

        for idx in range(start_idx, len(INITIAL_QUESTIONS)):
            q = INITIAL_QUESTIONS[idx]
            print_section(f"質問 {idx + 1}/{len(INITIAL_QUESTIONS)}")
            print_wrapped(q["question"])
            print()
            print_wrapped(q["hint"])
            print()
            print_wrapped(
                "(1つずつ入力 → Enter。終わったら空 Enter。"
                "「戻る」で前の質問へ)"
            )
            print()

            items_this_q: List[dict] = []
            while True:
                ans = ask_input("", allow_empty=True)
                if ans == "":
                    if len(items_this_q) < q.get("min_items", 1):
                        print(
                            f"  (あと {q['min_items'] - len(items_this_q)}"
                            f" 個くらい教えてほしいな！)"
                        )
                        continue
                    break
                if ans in ("戻る", "もどる", "back"):
                    if idx > 0:
                        state["initial_q_idx"] = idx - 1
                        self._autosave()
                        # 前の質問をやり直す (再帰ではなくループ制御)
                        print("  << 前の質問に戻るね！")
                        return self.run_initial_questions()
                    else:
                        print("  (最初の質問だよ！)")
                        continue
                if ans in ("保存", "save"):
                    self._autosave()
                    print("  >> 保存したよ！続きをどうぞ")
                    continue

                item = self._add_item(ans, phase=q["id"], depth=0)
                items_this_q.append(item)
                cat = item["category"]
                emoji = self.categorizer.get_emoji(cat)
                print(f"  {emoji} 「{ans}」を追加！ [{cat}]")

            state["initial_q_idx"] = idx + 1
            self._autosave()

        state["initial_done"] = True
        self._autosave()

    def run_deepdive(self):
        """深掘り質問フェーズ"""
        top_items = [
            it for it in self.data.items.values()
            if it.get("depth", 0) == 0
        ]
        if not top_items:
            print_wrapped("深掘りする項目がないよ。先に質問に答えてね！")
            return

        state = self.data.interview_state
        done_ids = set(state.get("deepdive_done", []))

        targets = [it for it in top_items if it["id"] not in done_ids]
        if not targets:
            print_wrapped("すべての項目の深掘りが完了しているよ！")
            return

        print_section("深掘りタイム！")
        print_wrapped(
            "さっき教えてくれた「好き」について、もう少し聞かせて！\n"
            "(スキップしたい場合は空 Enter、全部終わりたい場合は「終了」)"
        )
        print()

        for item in targets:
            name = item["name"]
            item_id = item["id"]
            emoji = self.categorizer.get_emoji(item.get("category", ""))

            print(f"\n  {emoji} 「{name}」について...\n")

            # 2-3 問ランダムに選ぶ
            qs = random.sample(
                DEEPDIVE_QUESTIONS,
                min(3, len(DEEPDIVE_QUESTIONS)),
            )
            for q_template in qs:
                q_text = q_template.format(item=name)
                print_wrapped(q_text)
                ans = ask_input("", allow_empty=True)
                if ans in ("終了", "おわり", "end"):
                    done_ids.add(item_id)
                    state["deepdive_done"] = list(done_ids)
                    self._autosave()
                    return
                if ans == "":
                    print("  (スキップ！)")
                    continue
                if ans in ("戻る", "もどる", "back"):
                    print("  (深掘りフェーズでは「戻る」は使えないよ。"
                          "スキップなら空 Enter！)")
                    continue
                # 深掘り回答を新しい項目として追加
                child = self._add_item(
                    ans, phase="deepdive", depth=1, parent_id=item_id,
                    details={"question": q_text},
                )
                cat = child["category"]
                tag_emoji = self.categorizer.get_emoji(cat)
                print(f"  {tag_emoji} 追加！ [{cat}]")

            done_ids.add(item_id)
            state["deepdive_done"] = list(done_ids)
            self._autosave()

        print()
        print_wrapped("深掘り完了！ たくさん教えてくれてありがとう！")

    def _autosave(self):
        try:
            self.data_mgr.save(self.data)
        except Exception:
            pass


# ============================================================
#  メインアプリケーション
# ============================================================

class PassionMapApp:
    """偏愛マップ作成アプリのメインクラス"""

    def __init__(self):
        self.data_mgr = DataManager()
        self.data: Optional[PassionMapData] = None
        self.engine: Optional[InterviewEngine] = None

    # ---------- 起動画面 ----------

    def start(self):
        clear_screen()
        print_header()
        print_wrapped(
            "ようこそ！ このアプリは、あなたの「好き」を\n"
            "深掘りして、偏愛マップを作るツールだよ。\n"
            "\n"
            "自分の興味や関心を整理して、\n"
            "探究学習のテーマ発見に役立てよう！"
        )
        print()

        choices = ["新しく始める", "続きから始める (データ読み込み)", "終了"]
        idx = ask_choice("何をする？", choices)

        if idx == 0:
            self._new_session()
        elif idx == 1:
            self._load_session()
        else:
            self._exit()

    # ---------- 新規セッション ----------

    def _new_session(self):
        print()
        name = ask_input("まずは名前を教えて（ニックネームでOK）")
        if not name:
            name = "ゲスト"
        self.data = PassionMapData(user_name=name)
        self.engine = InterviewEngine(self.data, self.data_mgr)

        print()
        print_wrapped(f"{name} さん、よろしく！ さっそく始めよう！")
        print()

        self._run_interview()
        self._main_menu()

    # ---------- データ読み込み ----------

    def _load_session(self):
        saves = self.data_mgr.list_saves()
        if not saves:
            print()
            print_wrapped("保存データが見つからないよ。新しく始めよう！")
            self._new_session()
            return

        print_section("保存データ一覧")
        names = self.data_mgr.list_save_names()
        idx = ask_choice("どのデータを読み込む？", saves)
        if idx < 0 or idx >= len(names):
            self.start()
            return

        self.data = self.data_mgr.load(names[idx])
        if self.data is None:
            print_wrapped("読み込みに失敗したよ。新しく始めよう！")
            self._new_session()
            return

        self.engine = InterviewEngine(self.data, self.data_mgr)
        n = len(self.data.items)
        print()
        print_wrapped(
            f"{self.data.user_name} さんのデータを読み込んだよ！"
            f" ({n}個の項目)"
        )
        self._main_menu()

    # ---------- インタビュー ----------

    def _run_interview(self):
        state = self.data.interview_state
        if not state.get("initial_done"):
            self.engine.run_initial_questions()

        if len(self.data.items) > 0:
            print()
            if ask_yes_no("深掘り質問もやってみる？"):
                self.engine.run_deepdive()

    # ---------- メインメニュー ----------

    def _main_menu(self):
        while True:
            n_items = len(self.data.items)
            print()
            print_header(
                f"{self.data.user_name} の偏愛マップ ({n_items}項目)"
            )
            choices = [
                "偏愛マップを見る (可視化)",
                "項目一覧を表示",
                "つながりを発見 & 探究テーマ提案",
                "項目を追加する",
                "項目を編集・削除する",
                "深掘り質問をもう一度",
                "データを保存する",
                "終了",
            ]
            idx = ask_choice("何をする？", choices)

            if idx == 0:
                self._visualize()
            elif idx == 1:
                self._list_items()
            elif idx == 2:
                self._discover_connections()
            elif idx == 3:
                self._add_items()
            elif idx == 4:
                self._edit_items()
            elif idx == 5:
                self._run_deepdive_again()
            elif idx == 6:
                self._save()
            elif idx == 7:
                self._save_and_exit()
                break
            else:
                self._save_and_exit()
                break

    # ---------- 可視化 ----------

    def _visualize(self):
        if not HAS_VISUALIZATION:
            print()
            print_wrapped(
                "可視化に必要なライブラリがインストールされていないよ。\n"
                "以下のコマンドでインストールしてね:\n"
                "  pip install matplotlib networkx"
            )
            return

        if not self.data.items:
            print_wrapped("まだ項目がないよ。先にインタビューをやろう！")
            return

        # つながりを計算
        connections = ConnectionAnalyzer.find_connections(self.data.items)
        self.data.connections = [asdict(c) for c in connections]

        # 保存先
        safe_name = "".join(
            c if c.isalnum() or c in ("_", "-") else "_"
            for c in self.data.user_name
        )
        output_path = os.path.join(
            self.data_mgr.save_dir,
            f"passion_map_{safe_name}.png",
        )

        print()
        print_wrapped("偏愛マップを生成中...")

        path = Visualizer.generate(
            items=self.data.items,
            connections=connections,
            user_name=self.data.user_name,
            output_path=output_path,
        )

        if path:
            print_wrapped(f"偏愛マップを保存したよ！")
            print_wrapped(f"ファイル: {path}")
            print()
            print_wrapped("画像ビューアで開いて確認してね！")
        else:
            print_wrapped("マップの生成に失敗しちゃった...")

    # ---------- 項目一覧 ----------

    def _list_items(self):
        if not self.data.items:
            print_wrapped("まだ項目がないよ！")
            return

        print_section("あなたの偏愛リスト")

        # カテゴリーごとにグループ化
        by_cat: Dict[str, List[dict]] = {}
        for item in self.data.items.values():
            cat = item.get("category", OTHER_CATEGORY["name"])
            by_cat.setdefault(cat, []).append(item)

        for cat, items in sorted(by_cat.items()):
            emoji = Categorizer.get_emoji(cat)
            color_code = Categorizer.get_color(cat)
            print(f"\n  {emoji} [{cat}] ({len(items)}個)")
            print(f"  {THIN_SEP}")
            for item in items:
                depth_mark = "  " * item.get("depth", 0)
                name = item.get("name", "?")
                tags = item.get("tags", [])
                tag_str = (
                    f"  #{' #'.join(tags[:3])}" if tags else ""
                )
                parent = item.get("parent_id", "")
                arrow = " └─ " if item.get("depth", 0) > 0 else "    "
                print(f"  {arrow}{depth_mark}{name}{tag_str}")

        print(f"\n  合計: {len(self.data.items)} 項目")

    # ---------- つながり発見 ----------

    def _discover_connections(self):
        if len(self.data.items) < 2:
            print_wrapped("2つ以上の項目が必要だよ！")
            return

        print_section("つながり発見")
        print_wrapped("あなたの「好き」の共通点を分析中...")
        print()

        connections = ConnectionAnalyzer.find_connections(self.data.items)
        self.data.connections = [asdict(c) for c in connections]

        if connections:
            print_wrapped(
                f"{len(connections)}個のつながりが見つかったよ！\n"
            )
            for i, conn in enumerate(connections[:15], 1):
                id1, id2 = conn.item1_id, conn.item2_id
                name1 = self.data.items.get(id1, {}).get("name", "?")
                name2 = self.data.items.get(id2, {}).get("name", "?")
                print(
                    f"    {i}. 「{name1}」 ←→ 「{name2}」"
                )
                print(f"       理由: {conn.reason}")
        else:
            print_wrapped("明確なつながりは見つからなかったけど、大丈夫！")

        # 探究テーマ提案
        print_section("探究テーマの候補")
        themes = ConnectionAnalyzer.suggest_themes(self.data.items)
        self.data.suggested_themes = themes

        if themes:
            print_wrapped(
                "あなたの「好き」を組み合わせたテーマ候補だよ：\n"
            )
            for i, theme in enumerate(themes, 1):
                print(f"    {i}. {theme}")
            print()
            print_wrapped(
                "気になるテーマはあった？\n"
                "これをヒントに、自分だけの探究テーマを見つけよう！"
            )
        else:
            print_wrapped(
                "テーマ提案にはもう少し項目が必要だよ。\n"
                "項目を追加してみてね！"
            )

        self.data_mgr.save(self.data)

    # ---------- 項目追加 ----------

    def _add_items(self):
        print_section("項目を追加")
        print_wrapped(
            "新しい「好き」「気になること」を追加しよう！\n"
            "(終わったら空 Enter)"
        )
        print()

        while True:
            ans = ask_input("追加する項目", allow_empty=True)
            if not ans:
                break
            cat = Categorizer.categorize(ans)
            tags = Categorizer.get_tags(ans)
            emoji = Categorizer.get_emoji(cat)

            item = PassionItem(
                name=ans,
                category=cat,
                tags=tags,
                depth=0,
                phase="manual",
            )
            self.data.items[item.id] = asdict(item)
            print(f"  {emoji} 「{ans}」を追加！ [{cat}]")

        self.data_mgr.save(self.data)

    # ---------- 項目編集・削除 ----------

    def _edit_items(self):
        if not self.data.items:
            print_wrapped("まだ項目がないよ！")
            return

        print_section("項目を編集・削除")
        items_list = list(self.data.items.values())
        display = [
            f"{it.get('name', '?')} [{it.get('category', '?')}]"
            for it in items_list
        ]
        display.append("キャンセル")

        idx = ask_choice("どの項目？", display)
        if idx < 0 or idx >= len(items_list):
            return

        item = items_list[idx]
        item_id = item["id"]
        print()
        print_wrapped(f"「{item['name']}」を選んだね")

        action_choices = [
            "名前を変更",
            "カテゴリーを変更",
            "タグを追加",
            "削除する",
            "キャンセル",
        ]
        action_idx = ask_choice("何をする？", action_choices)

        if action_idx == 0:
            new_name = ask_input("新しい名前")
            if new_name:
                self.data.items[item_id]["name"] = new_name
                self.data.items[item_id]["category"] = \
                    Categorizer.categorize(new_name)
                self.data.items[item_id]["tags"] = \
                    Categorizer.get_tags(new_name)
                print_wrapped(f"「{new_name}」に変更したよ！")
        elif action_idx == 1:
            cat_names = list(CATEGORIES.keys()) + [OTHER_CATEGORY["name"]]
            cat_display = [
                f"{Categorizer.get_emoji(c)} {c}" for c in cat_names
            ]
            cat_idx = ask_choice("どのカテゴリー？", cat_display)
            if 0 <= cat_idx < len(cat_names):
                self.data.items[item_id]["category"] = cat_names[cat_idx]
                print_wrapped(f"カテゴリーを変更したよ！")
        elif action_idx == 2:
            tag = ask_input("追加するタグ")
            if tag:
                if tag not in self.data.items[item_id].get("tags", []):
                    self.data.items[item_id].setdefault("tags", []).append(tag)
                    print_wrapped(f"タグ「{tag}」を追加したよ！")
                else:
                    print_wrapped("そのタグは既にあるよ！")
        elif action_idx == 3:
            if ask_yes_no(f"本当に「{item['name']}」を削除する？", False):
                del self.data.items[item_id]
                # 子項目も削除
                children = [
                    k for k, v in self.data.items.items()
                    if v.get("parent_id") == item_id
                ]
                for cid in children:
                    del self.data.items[cid]
                print_wrapped("削除したよ！")

        self.data_mgr.save(self.data)

    # ---------- 深掘り再実行 ----------

    def _run_deepdive_again(self):
        if not self.data.items:
            print_wrapped("まだ項目がないよ！")
            return
        # 深掘り済みをリセット
        self.data.interview_state["deepdive_done"] = []
        self.engine.run_deepdive()
        self.data_mgr.save(self.data)

    # ---------- 保存 ----------

    def _save(self):
        path = self.data_mgr.save(self.data)
        print()
        print_wrapped(f"保存完了！")
        print_wrapped(f"ファイル: {path}")

    # ---------- 終了 ----------

    def _save_and_exit(self):
        if self.data and self.data.items:
            path = self.data_mgr.save(self.data)
            print()
            print_wrapped(f"データを保存したよ！")
            print_wrapped(f"ファイル: {path}")
        self._exit()

    @staticmethod
    def _exit():
        print()
        print_wrapped(
            "お疲れさま！ あなたの「好き」はきっと\n"
            "素敵な探究につながるよ。またね！"
        )
        print()


# ============================================================
#  エントリーポイント
# ============================================================

def main():
    try:
        app = PassionMapApp()
        app.start()
    except KeyboardInterrupt:
        print("\n")
        print_wrapped("中断されたよ。データは自動保存済み！")
        print()


if __name__ == "__main__":
    main()
