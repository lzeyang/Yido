#!/usr/bin/env python3
"""极简命令行 Todo 工具（纯标准库，单文件）
用法示例：
    python todo.py add 面试 --tag 工作 --tag 紧急 --due 2026-08-20
    python todo.py edit 1 --content 复习面试题 --due "2026-08-20 18:00"
    python todo.py done 1
    python todo.py delete 2
    python todo.py list --filter undone --tag 工作 --sort due
    python todo.py list --overdue
"""

import argparse
import json
import os
import sys
from datetime import datetime

# 数据文件路径：当前工作目录下的 todo.json
DATA_FILE = os.path.join(os.getcwd(), "todo.json")

DUE_FORMAT = "%Y-%m-%d %H:%M"  # 截止时间统一存储格式


# ------------------------- 数据读写 -------------------------

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


def find_todo(todos, todo_id):
    """按编号查找待办，找不到返回 None"""
    return next((item for item in todos if item["id"] == todo_id), None)


# ------------------------- 辅助函数 -------------------------

def display_width(s):
    """粗略计算字符串显示宽度（中文/全角字符按 2 计算），用于对齐输出"""
    return sum(2 if ord(ch) > 127 else 1 for ch in s)


def pad(s, width):
    """按显示宽度对字符串进行右侧空格填充"""
    return s + " " * max(0, width - display_width(s))


def parse_due(text):
    """解析用户输入的截止时间。
    支持 'YYYY-MM-DD'（自动补齐为当天 23:59，表示"最晚今天完成"）
    和 'YYYY-MM-DD HH:MM' 两种格式，返回统一格式的字符串。
    """
    text = text.strip()
    print(text)
    for fmt, need_pad in (("%Y-%m-%d %H:%M", False), ("%Y-%m-%d", True)):
        try:
            dt = datetime.strptime(text, fmt)
            if need_pad:
                dt = dt.replace(hour=23, minute=59)
            return dt.strftime(DUE_FORMAT)
        except ValueError:
            continue
    raise ValueError(f"截止时间格式错误：{text}，请使用 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM'")


def normalize_tags(tag_list):
    """去除标签空白、去重（保留原始顺序）"""
    if not tag_list:
        return []
    cleaned = [t.strip() for t in tag_list if t.strip()]
    return list(dict.fromkeys(cleaned))


def is_overdue(item):
    """判断待办是否已过期（有截止时间、未完成、且已超过当前时间）"""
    if item["done"] or not item.get("due"):
        return False
    try:
        return datetime.strptime(item["due"], DUE_FORMAT) < datetime.now()
    except ValueError:
        return False


# ------------------------- 子命令实现 -------------------------

def cmd_add(args):
    """add 命令：添加一条待办，可选携带标签与截止时间"""
    content = " ".join(args.content).strip()
    if not content:
        print("错误：待办内容不能为空。", file=sys.stderr)
        sys.exit(1)

    due = None
    if args.due:
        try:
            due = parse_due(args.due)
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)

    todos = load_todos()
    item = {
        "id": next_id(todos),
        "content": content,
        "done": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tags": normalize_tags(args.tag),
        "due": due,
    }
    todos.append(item)
    save_todos(todos)
    extra = []
    if item["tags"]:
        extra.append("标签：" + "、".join(item["tags"]))
    if item["due"]:
        extra.append(f"截止：{item['due']}")
    suffix = f"（{'，'.join(extra)}）" if extra else ""
    print(f"已添加待办 #{item['id']}：{content}{suffix}")


def cmd_done(args):
    """done 命令：标记指定编号的待办为已完成"""
    todos = load_todos()
    target = find_todo(todos, args.id)

    if target is None:
        print(f"错误：未找到编号为 {args.id} 的待办。", file=sys.stderr)
        sys.exit(1)

    if target["done"]:
        print(f"提示：待办 #{args.id} 已经是完成状态，无需重复标记。")
        return

    target["done"] = True
    save_todos(todos)
    print(f"已将待办 #{args.id}（{target['content']}）标记为完成。")


def cmd_delete(args):
    """delete 命令：删除指定编号的待办"""
    todos = load_todos()
    target = find_todo(todos, args.id)

    if target is None:
        print(f"错误：未找到编号为 {args.id} 的待办。", file=sys.stderr)
        sys.exit(1)

    todos = [t for t in todos if t["id"] != args.id]
    save_todos(todos)
    print(f"已删除待办 #{args.id}（{target['content']}）。")


def cmd_edit(args):
    """edit 命令：修改待办的内容、标签或截止时间（只更新用户指定的字段）"""
    # 至少要提供一个要修改的字段，否则没有意义
    if (
        args.content is None
        and args.tag is None
        and not args.clear_tags
        and args.due is None
        and not args.clear_due
    ):
        print("错误：请至少指定一个要修改的字段（--content/--tag/--due/--clear-tags/--clear-due）。", file=sys.stderr)
        sys.exit(1)

    todos = load_todos()
    target = find_todo(todos, args.id)
    if target is None:
        print(f"错误：未找到编号为 {args.id} 的待办。", file=sys.stderr)
        sys.exit(1)

    if args.content is not None:
        new_content = " ".join(args.content).strip()
        if not new_content:
            print("错误：待办内容不能为空。", file=sys.stderr)
            sys.exit(1)
        target["content"] = new_content

    # 标签：--clear-tags 优先于 --tag（先清空、若同时给了 --tag 再设置新值）
    if args.clear_tags:
        target["tags"] = []
    if args.tag is not None:
        target["tags"] = normalize_tags(args.tag)

    # 截止时间：--clear-due 优先于 --due
    if args.clear_due:
        target["due"] = None
    if args.due is not None:
        try:
            target["due"] = parse_due(args.due)
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)

    save_todos(todos)
    print(f"已更新待办 #{args.id}。")


def cmd_list(args):
    """list 命令：按条件筛选、排序并对齐输出待办列表"""
    todos = load_todos()

    # ---- 筛选 ----
    if args.filter == "done":
        todos = [t for t in todos if t["done"]]
    elif args.filter == "undone":
        todos = [t for t in todos if not t["done"]]

    if args.tag:
        wanted = set(normalize_tags(args.tag))
        todos = [t for t in todos if wanted.issubset(set(t.get("tags") or []))]

    if args.overdue:
        todos = [t for t in todos if is_overdue(t)]

    if not todos:
        print("暂无符合条件的待办事项。")
        return

    # ---- 排序 ----
    reverse = args.order == "desc"
    if args.sort == "id":
        todos.sort(key=lambda t: t["id"], reverse=reverse)
    elif args.sort == "created":
        todos.sort(key=lambda t: t["created_at"], reverse=reverse)
    elif args.sort == "due":
        # 无截止时间的待办固定排在最后，避免和有截止时间的混排造成困惑
        with_due = [t for t in todos if t.get("due")]
        without_due = [t for t in todos if not t.get("due")]
        with_due.sort(key=lambda t: t["due"], reverse=reverse)
        todos = with_due + without_due

    # ---- 对齐输出 ----
    def tags_text(t):
        return "、".join(t.get("tags") or []) or "-"

    def due_text(t):
        return t.get("due") or "-"

    id_width = max(display_width("编号"), max(display_width(str(t["id"])) for t in todos))
    status_width = max(display_width("状态"), display_width("✔ 完成"), display_width("☐ 未完成"))
    content_width = max(display_width("内容"), max(display_width(t["content"]) for t in todos))
    tag_width = max(display_width("标签"), max(display_width(tags_text(t)) for t in todos))
    due_width = max(display_width("截止时间"), max(display_width(due_text(t)) for t in todos))

    header = (
        f"{pad('编号', id_width)}  {pad('状态', status_width)}  "
        f"{pad('内容', content_width)}  {pad('标签', tag_width)}  "
        f"{pad('截止时间', due_width)}  创建时间"
    )
    print(header)
    print("-" * display_width(header))

    for t in todos:
        status = "✔ 完成" if t["done"] else "☐ 未完成"
        due_str = due_text(t)
        if is_overdue(t):
            due_str = "⚠" + due_str  # 过期标记
        line = (
            f"{pad(str(t['id']), id_width)}  {pad(status, status_width)}  "
            f"{pad(t['content'], content_width)}  {pad(tags_text(t), tag_width)}  "
            f"{pad(due_str, due_width)}  {t['created_at']}"
        )
        print(line)


# ------------------------- 参数解析 -------------------------

def build_parser():
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(prog="todo.py", description="极简命令行 Todo 工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add 子命令
    p_add = subparsers.add_parser("add", help="添加一条待办")
    p_add.add_argument("content", nargs="+", help="待办内容，可包含空格")
    p_add.add_argument("--tag", "-t", action="append", help="为待办添加标签，可重复使用")
    p_add.add_argument("--due", "-d", help="截止时间，格式 YYYY-MM-DD 或 'YYYY-MM-DD HH:MM'")
    p_add.set_defaults(func=cmd_add)

    # done 子命令
    p_done = subparsers.add_parser("done", help="标记待办为已完成")
    p_done.add_argument("id", type=int, help="待办编号")
    p_done.set_defaults(func=cmd_done)

    # delete 子命令
    p_delete = subparsers.add_parser("delete", help="删除指定待办")
    p_delete.add_argument("id", type=int, help="待办编号")
    p_delete.set_defaults(func=cmd_delete)

    # edit 子命令
    p_edit = subparsers.add_parser("edit", help="修改待办内容/标签/截止时间")
    p_edit.add_argument("id", type=int, help="待办编号")
    p_edit.add_argument("--content", "-c", nargs="+", help="新的待办内容（整体替换）")
    p_edit.add_argument("--tag", "-t", action="append", help="设置新的标签列表（整体替换），可重复使用")
    p_edit.add_argument("--clear-tags", action="store_true", help="清空所有标签")
    p_edit.add_argument("--due", "-d", help="新的截止时间，格式 YYYY-MM-DD 或 'YYYY-MM-DD HH:MM'")
    p_edit.add_argument("--clear-due", action="store_true", help="清除截止时间")
    p_edit.set_defaults(func=cmd_edit)

    # list 子命令
    p_list = subparsers.add_parser("list", help="查看待办列表")
    p_list.add_argument(
        "--filter",
        choices=["all", "done", "undone"],
        default="all",
        help="筛选条件：all(全部，默认)/done(已完成)/undone(未完成)",
    )
    p_list.add_argument("--tag", "-t", action="append", help="按标签筛选，可重复使用（需同时包含所有给定标签）")
    p_list.add_argument("--overdue", action="store_true", help="只显示已过期且未完成的待办")
    p_list.add_argument(
        "--sort",
        choices=["id", "created", "due"],
        default="id",
        help="排序字段：id(默认)/created(创建时间)/due(截止时间)",
    )
    p_list.add_argument("--order", choices=["asc", "desc"], default="asc", help="排序方向，默认 asc（升序）")
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
