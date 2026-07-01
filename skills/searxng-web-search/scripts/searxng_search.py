#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SearXNG 搜索脚本

提供两个能力：
  1. suggest  - 获取搜索建议（autocomplete）
  2. search   - 执行搜索

固定配置（已固化在脚本中，不需要通过参数传入）：
  - SearXNG 服务地址：http://localhost:8888
  - 搜索语言：auto（自动检测）

调用方式见同目录 SKILL.md。
完整 JSON 结果默认写入输出文件，stdout 仅打印摘要，避免命令行截断。
"""

import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Windows 下终端可能使用 GBK 编码，强制 stdout 输出 UTF-8，
# 避免 SearXNG 返回的非 ASCII 内容导致打印报错。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ==================== 固定配置（固化，不可通过参数覆盖） ====================
SEARXNG_BASE_URL = "http://localhost:8888"
SEARCH_LANGUAGE = "auto"  # 语言固定为 auto
REQUEST_TIMEOUT = 30  # HTTP 请求超时（秒）


def _http_get_json(url, timeout=REQUEST_TIMEOUT):
    """发起 GET 请求并返回解析后的 JSON。失败时抛异常。"""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "searxng-skill/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        raise RuntimeError("SearXNG 返回 HTTP %d: %s" % (e.code, e.reason)) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            "无法连接 SearXNG 服务（%s），请确认 localhost:8888 已启动: %s"
            % (SEARXNG_BASE_URL, e.reason)
        ) from e
    except json.JSONDecodeError as e:
        raise RuntimeError("SearXNG 响应不是合法 JSON: %s" % e) from e


def _default_output_file(prefix):
    """生成默认输出文件路径（放在系统临时目录）。"""
    tmp_dir = os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp"
    ts = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(tmp_dir, "searxng_%s_%s.json" % (prefix, ts))


def _write_output(data, output_path):
    """将完整 JSON 写入文件，返回绝对路径。"""
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_path


# ==================== 能力 1：获取搜索建议（直接输出到 stdout） ====================
def cmd_suggest(args):
    query = args.query
    if not query:
        sys.stderr.write("错误：query 不能为空\n")
        return 2

    encoded_q = urllib.parse.quote(query, safe="")
    url = "%s/autocompleter?q=%s" % (SEARXNG_BASE_URL, encoded_q)

    data = _http_get_json(url)

    # autocompleter 返回 [query, [suggestion1, suggestion2, ...]]
    suggestions = []
    if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
        suggestions = data[1]

    output = {
        "query": query,
        "suggestions": suggestions,
        "count": len(suggestions),
    }

    # 搜索建议数据量小，直接输出 JSON 到 stdout
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


# ==================== 能力 2：执行搜索 ====================
def cmd_search(args):
    query = args.query
    if not query:
        sys.stderr.write("错误：query 不能为空\n")
        return 2

    params = {
        "q": query,
        "format": "json",
        "language": SEARCH_LANGUAGE,  # 固定 auto
        "pageno": str(args.pageno),
    }
    if args.categories:
        params["categories"] = args.categories
    if args.engines:
        params["engines"] = args.engines
    if args.time_range and args.time_range != "none":
        params["time_range"] = args.time_range
    if args.safesearch is not None:
        params["safesearch"] = str(args.safesearch)

    url = "%s/search?%s" % (
        SEARXNG_BASE_URL,
        urllib.parse.urlencode(params),
    )

    data = _http_get_json(url)

    results = data.get("results", []) if isinstance(data, dict) else []

    # 截取前 N 条（仅用于摘要展示，完整结果仍写入文件）
    top_results = results[: args.top] if args.top and args.top > 0 else results

    output = {
        "query": data.get("query", query) if isinstance(data, dict) else query,
        "number_of_results": data.get("number_of_results")
        if isinstance(data, dict)
        else None,
        "results_count": len(results),
        "results": results,
        "answers": data.get("answers", []) if isinstance(data, dict) else [],
        "corrections": data.get("corrections", []) if isinstance(data, dict) else [],
        "infoboxes": data.get("infoboxes", []) if isinstance(data, dict) else [],
        "suggestions": data.get("suggestions", []) if isinstance(data, dict) else [],
        "unresponsive_engines": data.get("unresponsive_engines", [])
        if isinstance(data, dict)
        else [],
        "request_url": url,
    }

    output_path = _write_output(output, args.output)

    # stdout 仅打印摘要
    print("搜索结果已写入: %s" % output_path)
    print("查询: %s" % query)
    print("结果总数: %d" % len(results))
    if data.get("number_of_results"):
        print("引擎估算总数: %s" % data.get("number_of_results"))
    unresp = data.get("unresponsive_engines", []) if isinstance(data, dict) else []
    if unresp:
        print("无响应引擎: %s" % unresp)
    if top_results:
        print("前 %d 条结果:" % len(top_results))
        for i, r in enumerate(top_results, 1):
            title = r.get("title", "")
            url_ = r.get("url", "")
            content = (r.get("content", "") or "").replace("\n", " ")
            if len(content) > 120:
                content = content[:120] + "..."
            print("  %d. %s" % (i, title))
            print("     URL: %s" % url_)
            if content:
                print("     摘要: %s" % content)
    return 0


# ==================== 入口 ====================
def build_parser():
    parser = argparse.ArgumentParser(
        prog="searxng_search.py",
        description="SearXNG 搜索脚本（服务地址与语言已固化）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # suggest 子命令（搜索建议直接输出到 stdout，无需 -o）
    p_suggest = sub.add_parser(
        "suggest", help="获取搜索建议（直接输出 JSON 到 stdout）"
    )
    p_suggest.add_argument("query", help="搜索词")

    # search 子命令
    p_search = sub.add_parser("search", help="执行搜索")
    p_search.add_argument("query", help="搜索词")
    p_search.add_argument(
        "-o",
        "--output",
        help="输出 JSON 文件路径（默认写入系统临时目录）",
    )
    p_search.add_argument(
        "-p",
        "--pageno",
        type=int,
        default=1,
        help="页码，从 1 开始（默认 1）",
    )
    p_search.add_argument(
        "-c",
        "--categories",
        help="搜索分类，多个用逗号分隔，如 general,images,videos,news,it",
    )
    p_search.add_argument(
        "-e",
        "--engines",
        help="指定引擎，多个用逗号分隔，如 google,bing,duckduckgo,wikipedia",
    )
    p_search.add_argument(
        "-t",
        "--time_range",
        choices=["none", "day", "week", "month", "year"],
        default="none",
        help="时间范围过滤（默认 none 不过滤）",
    )
    p_search.add_argument(
        "-s",
        "--safesearch",
        type=int,
        choices=[0, 1, 2],
        help="安全搜索级别：0=关闭 1=中等 2=严格",
    )
    p_search.add_argument(
        "-n",
        "--top",
        type=int,
        default=10,
        help="stdout 摘要中展示前 N 条结果（默认 10；完整结果始终写入文件）",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # 仅 search 子命令需要默认输出文件路径
    if args.command == "search" and not getattr(args, "output", None):
        args.output = _default_output_file("search")

    try:
        if args.command == "suggest":
            return cmd_suggest(args)
        elif args.command == "search":
            return cmd_search(args)
        else:
            parser.print_help()
            return 2
    except RuntimeError as e:
        sys.stderr.write("错误: %s\n" % e)
        return 1
    except Exception as e:
        sys.stderr.write("未知错误: %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
