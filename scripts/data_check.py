#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""免费 A 股日线行情数据源连通性检查（AkShare）。

用法：
    python scripts/data_check.py
    python scripts/data_check.py --code 000001 --start-date 20250101
    python scripts/data_check.py --code 600519 --adjust qfq

默认测试贵州茅台（600519），下载前复权日线并保存到 data/cache/。
本脚本只验证数据拉取，不构成投资建议。
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    today = date.today()
    default_start = (today - timedelta(days=365)).strftime("%Y%m%d")
    parser = argparse.ArgumentParser(description="检查 AkShare 东方财富 A 股历史行情数据源")
    parser.add_argument("--code", default="600519", help="A 股代码，默认 600519")
    parser.add_argument("--start-date", default=default_start, help="开始日期 YYYYMMDD")
    parser.add_argument("--end-date", default=today.strftime("%Y%m%d"), help="结束日期 YYYYMMDD")
    parser.add_argument(
        "--adjust", choices=("", "qfq", "hfq"), default="qfq",
        help="复权方式：qfq 前复权（默认）、hfq 后复权、空字符串不复权",
    )
    parser.add_argument("--output-dir", default="data/cache", help="CSV 输出目录")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code = args.code.strip()

    if len(code) != 6 or not code.isdigit():
        print(f"[参数错误] 股票代码应为 6 位数字：{code}", file=sys.stderr)
        return 2
    if args.start_date > args.end_date:
        print("[参数错误] start-date 不能晚于 end-date", file=sys.stderr)
        return 2

    try:
        import akshare as ak
    except ImportError:
        print("[依赖缺失] 未安装 akshare。请执行：pip install 'akshare>=1.14,<2.0'", file=sys.stderr)
        return 3

    print(f"[开始] 数据源：AkShare；股票：{code}")
    print(f"[区间] {args.start_date} 至 {args.end_date}；复权：{args.adjust or '不复权'}")

    try:
        frame = ak.stock_zh_a_hist_em(
            symbol=code,
            period="daily",
            start_date=args.start_date,
            end_date=args.end_date,
            adjust=args.adjust,
        )
    except Exception as exc:  # 网络、上游接口或数据源异常
        print(f"[拉取失败] {type(exc).__name__}: {exc}", file=sys.stderr)
        print("请稍后重试，并检查网络连接及 AkShare 上游接口状态。", file=sys.stderr)
        return 1

    if frame is None or frame.empty:
        print("[无数据] 接口已返回，但指定区间没有行情记录。", file=sys.stderr)
        return 4

    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"data_check_{code}_{args.adjust or 'none'}.csv"
    frame.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"[成功] 获取 {len(frame)} 条日线记录")
    print(f"[字段] {', '.join(map(str, frame.columns))}")
    print(f"[最新] {frame.iloc[-1].to_dict()}")
    print(f"[保存] {output_file.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
