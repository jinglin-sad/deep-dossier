# -*- coding: utf-8 -*-
"""长报告铁律机器自查：感叹号 / 树状字符 / 代码块包表格 / 头部必填字段 / 字数统计。

用法:
    python scripts/selfcheck.py "分卷/*.md" "附件_*.md" "00_*.md"
    python scripts/selfcheck.py --no-header "附件_时间线大事记.md"
退出码: 0 = 全部合格; 1 = 有不合格文件（合格前不得交付）

说明：
- 本文件刻意不写 shebang：shebang 里那个感叹号会被本包的自查脚本判为违规，请用 `python scripts/selfcheck.py` 调用；
- 脚本自身用 chr() 构造要检查的字符，避免文件里出现被检查的字面量（本脚本自己也能通过同一套检查）；
- 第三项检查的是"代码块里包了表格"（真正会让渲染器崩掉的写法），不是所有代码块——
  正文里出现命令行、日志之类的代码块是允许的，只要里面没有表格行。
"""
import argparse
import glob
import sys
from pathlib import Path

BANG = chr(33) + chr(0xFF01)                       # 半角与全角感叹号
FENCE = chr(96) * 3                                # 代码块围栏
PIPE = chr(124)                                    # 表格分隔符
# 树状与连线字符（在多数 Markdown 渲染器、尤其 Obsidian 里易崩溃，一律禁用）
TREE_CODES = [0x251C, 0x2514, 0x2502, 0x250C, 0x2510, 0x2518,
              0x2500, 0x2533, 0x253B, 0x2523, 0x252B, 0x250F, 0x2513,
              0x2517, 0x251B, 0x252D, 0x253C]
TREE_CHARS = set(chr(c) for c in TREE_CODES)
HEADER_FIELDS = ["生成模型", "数据截至"]


def expand(patterns):
    files = []
    for pat in patterns:
        hits = sorted(glob.glob(pat, recursive=True))
        files.extend(hits if hits else [pat])
    return [Path(f) for f in files if Path(f).is_file()]


def table_rows_in_code_blocks(text):
    """统计"被代码块包裹的表格行"数量。"""
    inside = False
    rows = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(FENCE):
            inside = not inside
            continue
        if inside and stripped.startswith(PIPE):
            rows += 1
    return rows


def check(path, header=True):
    text = path.read_text(encoding="utf-8", errors="replace")
    issues = []

    n_excl = sum(text.count(c) for c in BANG)
    if n_excl:
        issues.append(f"感叹号 {n_excl} 处（铁律：0；引文也不得私自加）")

    bad_tree = sorted(TREE_CHARS.intersection(text))
    if bad_tree:
        issues.append("树状/连线字符：" + " ".join(bad_tree) + "（禁）")

    fenced_tables = table_rows_in_code_blocks(text)
    if fenced_tables:
        issues.append(f"代码块里包了表格 {fenced_tables} 行（禁；表格须用原生 Markdown）")

    if header:
        for field in HEADER_FIELDS:
            if field not in text:
                issues.append(f"头部缺少必填字段：{field}")

    return issues, len(text), text.count(PIPE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patterns", nargs="+", help="文件或通配符，如 分卷/*.md")
    ap.add_argument("--no-header", action="store_true", help="跳过头部字段检查（用于纯附件或技能文档）")
    args = ap.parse_args()

    total = 0
    bad = 0
    for path in expand(args.patterns):
        issues, chars, pipes = check(path, header=not args.no_header)
        total += chars
        if issues:
            bad += 1
            print(f"[FAIL] {path}  （{chars} 字）")
            for i in issues:
                print(f"        - {i}")
        else:
            print(f"[ OK ] {path}  （{chars} 字，表格符 {pipes}）")

    print(f"--- 合计 {total} 字；不合格文件 {bad} 个 ---")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
