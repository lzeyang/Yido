#!/usr/bin/env python3
"""极简命令行 Todo 工具（纯标准库，单文件）
用法示例：
    python todo.py add 面试
    python todo.py done 1
    python todo.py list
    python todo.py list --filter undone
"""

import argparse
import json
import os
import sys
from datetime import datetime

# 数据文件路径：当前工作目录下的 todo.json
DATA_FILE = os.path.join(os.getcwd(), "todo.json")


def load_todos():
    """从 todo.json 加载待办列表；文件不存在则返回空列表"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            text = f.read().strip()
            if not text:
                return []
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("数据格式错误：根节点应为列表")
            return data
    except (json.JSONDecodeError, ValueError) as e:
        print(f"错误：todo.json 内容损坏（{e}），请检查或删除该文件。", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"错误：读取 todo.json 失败（{e}）。", file=sys.stderr)
        sys.exit(1)


def save_todos(todos):
    """将待办列表保存到 todo.json"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"错误：写入 todo.json 失败（{e}）。", file=sys.stderr)
        sys.exit(1)


def next_id(todos):
    """计算下一个可用编号（当前最大编号 + 1，空列表则从 1 开始）"""
    if not todos:
        return 1
    return max(item["id"] for item in todos) + 1


def display_width(s):
    """粗略计算字符串显示宽度（中文/全角字符按 2 计算），用于对齐输出"""
    return sum(2 if ord(ch) > 127 else 1 for ch in s)


def pad(s, width):
    """按显示宽度对字符串进行右侧空格填充"""
    return s + " " * max(0, width - display_width(s))


def cmd_add(args):
    """add 命令：添加一条待办"""
    content = " ".join(args.content).strip()
    if not content:
        print("错误：待办内容不能为空。", file=sys.stderr)
        sys.exit(1)

    todos = load_todos()
    item = {
        "id": next_id(todos),
        "content": content,
        "done": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    todos.append(item)
    save_todos(todos)
    print(f"已添加待办 #{item['id']}：{content}")


def cmd_done(args):
    """done 命令：标记指定编号的待办为已完成"""
    todos = load_todos()
    target = next((item for item in todos if item["id"] == args.id), None)

    if target is None:
        print(f"错误：未找到编号为 {args.id} 的待办。", file=sys.stderr)
        sys.exit(1)

    if target["done"]:
        print(f"提示：待办 #{args.id} 已经是完成状态，无需重复标记。")
        return

    target["done"] = True
    save_todos(todos)
    print(f"已将待办 #{args.id}（{target['content']}）标记为完成。")


def cmd_list(args):
    """list 命令：按条件筛选并对齐输出待办列表"""
    todos = load_todos()

    if args.filter == "done":
        todos = [t for t in todos if t["done"]]
    elif args.filter == "undone":
        todos = [t for t in todos if not t["done"]]
    # filter == "all" 时不过滤

    if not todos:
        print("暂无符合条件的待办事项。")
        return

    # 按显示宽度计算各列宽度，保证中英文混排也能对齐
    id_width = max(display_width("编号"), max(display_width(str(t["id"])) for t in todos))
    status_width = max(display_width("状态"), display_width("✔ 完成"), display_width("☐ 未完成"))
    content_width = max(display_width("内容"), max(display_width(t["content"]) for t in todos))

    header = f"{pad('编号', id_width)}  {pad('状态', status_width)}  {pad('内容', content_width)}  创建时间"
    print(header)
    print("-" * display_width(header))

    for t in todos:
        status = "✔ 完成" if t["done"] else "☐ 未完成"
        line = (
            f"{pad(str(t['id']), id_width)}  "
            f"{pad(status, status_width)}  "
            f"{pad(t['content'], content_width)}  "
            f"{t['created_at']}"
        )
        print(line)


def build_parser():
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(prog="todo.py", description="极简命令行 Todo 工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add 子命令
    p_add = subparsers.add_parser("add", help="添加一条待办")
    p_add.add_argument("content", nargs="+", help="待办内容，可包含空格")
    p_add.set_defaults(func=cmd_add)

    # done 子命令
    p_done = subparsers.add_parser("done", help="标记待办为已完成")
    p_done.add_argument("id", type=int, help="待办编号")
    p_done.set_defaults(func=cmd_done)

    # list 子命令
    p_list = subparsers.add_parser("list", help="查看待办列表")
    p_list.add_argument(
        "--filter",
        choices=["all", "done", "undone"],
        default="all",
        help="筛选条件：all(全部，默认)/done(已完成)/undone(未完成)",
    )
    p_list.set_defaults(func=cmd_list)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n已取消操作。")
        sys.exit(130)


if __name__ == "__main__":
    main()