#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简易命令行 Todo 工具
用法：
    python todo.py add <内容>       # 添加待办
    python todo.py done <编号>      # 标记编号对应的待办为已完成
    python todo.py list [--all]     # 列出待办（默认只显示未完成的，--all 显示全部）
数据保存在当前目录下的 todo.json 文件中。
"""

import json
import os
import sys
import datetime
import argparse
from typing import List, Dict, Any

# 数据文件路径
DATA_FILE = "todo.json"

# 默认编号起始值（若文件为空，从1开始）
INITIAL_ID = 1


def load_todos() -> List[Dict[str, Any]]:
    """从 JSON 文件加载待办列表，若文件不存在或格式错误则返回空列表。"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 确保是列表
            if isinstance(data, list):
                return data
            else:
                return []
    except (json.JSONDecodeError, IOError):
        # 文件损坏或无法读取，返回空列表（可考虑备份，但此处简单处理）
        return []


def save_todos(todos: List[Dict[str, Any]]) -> None:
    """将待办列表保存到 JSON 文件。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def generate_new_id(todos: List[Dict[str, Any]]) -> int:
    """根据现有记录生成一个新的自增编号（最大编号 + 1）。"""
    if not todos:
        return INITIAL_ID
    max_id = max(item.get("id", 0) for item in todos)
    return max_id + 1


def add_todo(content: str) -> None:
    """添加一条新的待办事项。"""
    if not content or content.strip() == "":
        print("错误：待办内容不能为空。")
        return

    todos = load_todos()
    new_id = generate_new_id(todos)
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    new_item = {
        "id": new_id,
        "content": content.strip(),
        "done": False,
        "created_at": now
    }
    todos.append(new_item)
    save_todos(todos)
    print(f"已添加待办 [#{new_id}] {content.strip()}")


def done_todo(todo_id: int) -> None:
    """标记指定编号的待办为已完成。"""
    todos = load_todos()
    # 查找匹配的待办
    for item in todos:
        if item.get("id") == todo_id:
            if item.get("done", False):
                print(f"待办 [#{todo_id}] 已经完成。")
                return
            item["done"] = True
            save_todos(todos)
            print(f"已标记待办 [#{todo_id}] 为完成。")
            return
    # 未找到
    print(f"错误：未找到编号为 {todo_id} 的待办。")


def list_todos(show_all: bool = False) -> None:
    """列出待办事项，默认只显示未完成的，show_all=True 显示全部。"""
    todos = load_todos()
    if not todos:
        print("暂无待办事项。")
        return

    # 筛选
    if show_all:
        filtered = todos
        title = "所有待办事项"
    else:
        filtered = [item for item in todos if not item.get("done", False)]
        title = "未完成的待办事项"

    if not filtered:
        print("没有符合条件的待办。")
        return

    # 按编号排序
    filtered_sorted = sorted(filtered, key=lambda x: x.get("id", 0))

    # 计算各列宽度（至少保证内容列有足够空间）
    id_width = max(4, max(len(str(item.get("id", ""))) for item in filtered_sorted))
    done_width = max(6, max(len("是" if item.get("done", False) else "否") for item in filtered_sorted))
    created_width = max(12, max(len(item.get("created_at", "")) for item in filtered_sorted))
    content_width = max(10, max(len(item.get("content", "")) for item in filtered_sorted))
    # 内容列至少20字符，太短不好看
    if content_width < 20:
        content_width = 20

    # 表头
    header = (f"{'编号':<{id_width}}  "
              f"{'内容':<{content_width}}  "
              f"{'完成':<{done_width}}  "
              f"{'创建时间':<{created_width}}")
    print(f"\n{title}:")
    print(header)
    print("-" * len(header))

    for item in filtered_sorted:
        done_str = "是" if item.get("done", False) else "否"
        created = item.get("created_at", "")
        # 截断过长的内容（保留完整显示，但可能破坏对齐，这里不截断）
        content = item.get("content", "")
        # 如果内容过长，可适当截断，但这里保持原样
        line = (f"{item.get('id', 0):<{id_width}}  "
                f"{content:<{content_width}}  "
                f"{done_str:<{done_width}}  "
                f"{created:<{created_width}}")
        print(line)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="简易命令行 Todo 工具",
        usage="python todo.py <command> [options]"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="子命令")

    # add 子命令
    parser_add = subparsers.add_parser("add", help="添加待办")
    parser_add.add_argument("content", type=str, help="待办内容")

    # done 子命令
    parser_done = subparsers.add_parser("done", help="标记完成")
    parser_done.add_argument("id", type=int, help="待办编号")

    # list 子命令
    parser_list = subparsers.add_parser("list", help="列出待办")
    parser_list.add_argument("--all", action="store_true", help="显示所有待办（包括已完成的）")

    args = parser.parse_args()

    try:
        if args.command == "add":
            add_todo(args.content)
        elif args.command == "done":
            done_todo(args.id)
        elif args.command == "list":
            list_todos(args.all)
    except Exception as e:
        print(f"发生错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()