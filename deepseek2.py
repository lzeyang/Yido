#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强型命令行 Todo 工具
支持添加、完成、删除、修改、列表（筛选与排序）
数据保存在 todo.json
每条记录：编号、内容、是否完成、创建时间、标签列表、最晚期限
用法：
    python todo.py add <内容> [--due YYYY-MM-DD] [--tag 标签1,标签2,...]
    python todo.py done <编号>
    python todo.py delete <编号>
    python todo.py update <编号> [--content 新内容] [--due 日期] [--tag 新标签]
    python todo.py list [--all] [--done|--undone] [--tag 标签] [--sort 字段] [--desc]
"""

import json
import os
import sys
import datetime
import argparse
from typing import List, Dict, Any, Optional

DATA_FILE = "todo.json"
INITIAL_ID = 1
# 支持的排序字段
SORT_FIELDS = {"id", "due", "created_at", "content"}


def load_todos() -> List[Dict[str, Any]]:
    """从 JSON 文件加载待办列表，若文件不存在或格式错误则返回空列表。"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                # 兼容旧数据：缺失字段补默认值
                for item in data:
                    if "tags" not in item:
                        item["tags"] = []
                    if "due" not in item:
                        item["due"] = None
                return data
            else:
                return []
    except (json.JSONDecodeError, IOError):
        return []


def save_todos(todos: List[Dict[str, Any]]) -> None:
    """保存待办列表到 JSON 文件。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def generate_new_id(todos: List[Dict[str, Any]]) -> int:
    """生成新的自增编号。"""
    if not todos:
        return INITIAL_ID
    max_id = max(item.get("id", 0) for item in todos)
    return max_id + 1


def parse_date(date_str: str) -> Optional[str]:
    """解析日期字符串，返回 ISO 日期 (YYYY-MM-DD)，若格式错误则抛出 ValueError。"""
    if not date_str:
        return None
    # 尝试解析多种格式，只取日期部分
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"无效的日期格式：'{date_str}'，请使用 YYYY-MM-DD 格式")


def parse_tags(tag_str: Optional[str]) -> List[str]:
    """解析标签字符串（逗号分隔），返回去重后的非空标签列表。"""
    if not tag_str:
        return []
    tags = [t.strip() for t in tag_str.split(",") if t.strip()]
    # 去重，保持顺序
    seen = set()
    unique = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def add_todo(content: str, due: Optional[str] = None, tags: Optional[List[str]] = None) -> None:
    """添加待办，支持期限和标签。"""
    if not content or not content.strip():
        print("错误：待办内容不能为空。")
        return

    todos = load_todos()
    new_id = generate_new_id(todos)
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    new_item = {
        "id": new_id,
        "content": content.strip(),
        "done": False,
        "created_at": now,
        "due": due,          # 可能为 None
        "tags": tags if tags is not None else []
    }
    todos.append(new_item)
    save_todos(todos)
    print(f"已添加待办 [#{new_id}] {content.strip()}")


def done_todo(todo_id: int) -> None:
    """标记指定编号的待办为已完成。"""
    todos = load_todos()
    for item in todos:
        if item.get("id") == todo_id:
            if item.get("done", False):
                print(f"待办 [#{todo_id}] 已经完成。")
                return
            item["done"] = True
            save_todos(todos)
            print(f"已标记待办 [#{todo_id}] 为完成。")
            return
    print(f"错误：未找到编号为 {todo_id} 的待办。")


def delete_todo(todo_id: int) -> None:
    """删除指定编号的待办。"""
    todos = load_todos()
    for idx, item in enumerate(todos):
        if item.get("id") == todo_id:
            del todos[idx]
            save_todos(todos)
            print(f"已删除待办 [#{todo_id}]。")
            return
    print(f"错误：未找到编号为 {todo_id} 的待办。")


def update_todo(todo_id: int, new_content: Optional[str] = None,
                new_due: Optional[str] = None, new_tags: Optional[List[str]] = None) -> None:
    """更新待办的内容、期限、标签，只更新提供的字段。"""
    todos = load_todos()
    target = None
    for item in todos:
        if item.get("id") == todo_id:
            target = item
            break
    if target is None:
        print(f"错误：未找到编号为 {todo_id} 的待办。")
        return

    updated = False
    if new_content is not None:
        if not new_content.strip():
            print("错误：新内容不能为空。")
            return
        target["content"] = new_content.strip()
        updated = True

    if new_due is not None:
        # 若 new_due 为空字符串，表示清除期限
        if new_due == "":
            target["due"] = None
        else:
            try:
                parsed = parse_date(new_due)
                target["due"] = parsed
            except ValueError as e:
                print(f"错误：{e}")
                return
        updated = True

    if new_tags is not None:
        target["tags"] = new_tags
        updated = True

    if updated:
        save_todos(todos)
        print(f"已更新待办 [#{todo_id}]。")
    else:
        print("没有提供任何更新信息。")


def list_todos(show_all: bool = False, status_filter: Optional[bool] = None,
               tag_filter: Optional[str] = None, sort_by: str = "id",
               descending: bool = False) -> None:
    """
    列出待办，支持筛选和排序。
    status_filter: True 只显示已完成，False 只显示未完成，None 不过滤状态
    tag_filter: 指定标签（字符串），只显示包含该标签的待办
    sort_by: 排序字段，默认为 'id'
    descending: 是否降序
    """
    todos = load_todos()
    if not todos:
        print("暂无待办事项。")
        return

    # 状态筛选
    filtered = todos
    if not show_all and status_filter is not None:
        filtered = [item for item in filtered if item.get("done", False) == status_filter]
    elif show_all:
        # --all 忽略状态筛选，显示所有
        pass
    else:
        # 默认显示未完成
        filtered = [item for item in filtered if not item.get("done", False)]

    # 标签筛选
    if tag_filter:
        tag_filter = tag_filter.strip()
        filtered = [item for item in filtered if tag_filter in item.get("tags", [])]

    if not filtered:
        print("没有符合条件的待办。")
        return

    # 排序
    if sort_by not in SORT_FIELDS:
        print(f"警告：不支持的排序字段 '{sort_by}'，将按 id 排序。")
        sort_by = "id"

    # 处理 None 值排序（due 可能为 None）
    def sort_key(item):
        val = item.get(sort_by)
        # 如果值为 None，放到末尾（升序）或开头（降序）？
        # 这里统一将 None 视为最末端（或最小），我们将其转换为一个特殊值
        if val is None:
            # 升序时 None 排最前？通常希望 None 排最后，所以用 9999-12-31 之类，但类型可能不同
            # 简单处理：将 None 转为空字符串或一个极大值，根据类型
            if sort_by == "due":
                # 日期 None 视为无穷远
                return "9999-12-31" if not descending else "0000-01-01"
            else:
                return ""  # 其他字段 None 几乎不可能
        return val

    filtered_sorted = sorted(filtered, key=sort_key, reverse=descending)

    # 计算列宽
    id_width = max(4, max(len(str(item.get("id", ""))) for item in filtered_sorted))
    done_width = max(6, max(len("是" if item.get("done", False) else "否") for item in filtered_sorted))
    created_width = max(12, max(len(item.get("created_at", "")) for item in filtered_sorted))
    due_width = max(6, max(len(item.get("due") or "无") for item in filtered_sorted))
    tags_width = max(8, max(len(", ".join(item.get("tags", []))) for item in filtered_sorted))
    content_width = max(10, max(len(item.get("content", "")) for item in filtered_sorted))
    if content_width < 20:
        content_width = 20

    # 表头
    header = (f"{'编号':<{id_width}}  "
              f"{'内容':<{content_width}}  "
              f"{'完成':<{done_width}}  "
              f"{'创建时间':<{created_width}}  "
              f"{'期限':<{due_width}}  "
              f"{'标签':<{tags_width}}")
    print(f"\n{'所有' if show_all else '未完成' if status_filter is None else '已完成' if status_filter else '未完成'}待办事项:")
    print(header)
    print("-" * len(header))

    for item in filtered_sorted:
        done_str = "是" if item.get("done", False) else "否"
        created = item.get("created_at", "")
        due = item.get("due") or "无"
        tags = ", ".join(item.get("tags", []))
        content = item.get("content", "")
        line = (f"{item.get('id', 0):<{id_width}}  "
                f"{content:<{content_width}}  "
                f"{done_str:<{done_width}}  "
                f"{created:<{created_width}}  "
                f"{due:<{due_width}}  "
                f"{tags:<{tags_width}}")
        print(line)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="增强型命令行 Todo 工具",
        usage="python todo.py <command> [options]"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="子命令")

    # add 子命令
    parser_add = subparsers.add_parser("add", help="添加待办")
    parser_add.add_argument("content", type=str, help="待办内容")
    parser_add.add_argument("--due", type=str, help="最晚完成期限，格式 YYYY-MM-DD")
    parser_add.add_argument("--tag", "--tags", type=str, help="标签，多个用逗号分隔", dest="tag")

    # done 子命令
    parser_done = subparsers.add_parser("done", help="标记完成")
    parser_done.add_argument("id", type=int, help="待办编号")

    # delete 子命令
    parser_delete = subparsers.add_parser("delete", help="删除待办")
    parser_delete.add_argument("id", type=int, help="待办编号")

    # update 子命令
    parser_update = subparsers.add_parser("update", help="更新待办")
    parser_update.add_argument("id", type=int, help="待办编号")
    parser_update.add_argument("--content", type=str, help="新的内容")
    parser_update.add_argument("--due", type=str, help="新的期限 (YYYY-MM-DD)，空字符串表示清除")
    parser_update.add_argument("--tag", type=str, help="新标签（覆盖原有标签），多个用逗号分隔")

    # list 子命令
    parser_list = subparsers.add_parser("list", help="列出待办")
    parser_list.add_argument("--all", action="store_true", help="显示所有待办（包括已完成的）")
    status_group = parser_list.add_mutually_exclusive_group()
    status_group.add_argument("--done", action="store_true", help="只显示已完成的")
    status_group.add_argument("--undone", action="store_true", help="只显示未完成的（默认）")
    parser_list.add_argument("--tag", type=str, help="按标签筛选（包含该标签）")
    parser_list.add_argument("--sort", type=str, default="id", choices=SORT_FIELDS,
                             help=f"排序字段，可选: {', '.join(SORT_FIELDS)}")
    parser_list.add_argument("--desc", action="store_true", help="降序排列")

    args = parser.parse_args()

    try:
        if args.command == "add":
            # 处理 due
            due = None
            if hasattr(args, "due") and args.due:
                try:
                    due = parse_date(args.due)
                except ValueError as e:
                    print(f"错误：{e}")
                    sys.exit(1)
            tags = parse_tags(args.tag) if hasattr(args, "tag") and args.tag else []
            add_todo(args.content, due, tags)

        elif args.command == "done":
            done_todo(args.id)

        elif args.command == "delete":
            delete_todo(args.id)

        elif args.command == "update":
            # 解析新内容
            new_content = args.content if hasattr(args, "content") and args.content is not None else None
            # 解析新期限
            new_due = None
            if hasattr(args, "due") and args.due is not None:
                if args.due == "":
                    new_due = ""  # 表示清除
                else:
                    try:
                        new_due = parse_date(args.due)
                    except ValueError as e:
                        print(f"错误：{e}")
                        sys.exit(1)
            # 解析新标签
            new_tags = None
            if hasattr(args, "tag") and args.tag is not None:
                new_tags = parse_tags(args.tag)
            update_todo(args.id, new_content, new_due, new_tags)

        elif args.command == "list":
            # 状态筛选
            status_filter = None
            if args.all:
                status_filter = None  # 全部
            elif args.done:
                status_filter = True
            elif args.undone:
                status_filter = False
            else:
                status_filter = False  # 默认未完成

            # 因为 --all 覆盖状态筛选，若指定 --all 则忽略 --done/--undone
            if args.all:
                # 将 status_filter 设为 None 表示不过滤状态，且 show_all=True 表示全部显示
                show_all = True
                status_filter = None
            else:
                show_all = False

            # 若指定了 --done 或 --undone，但未指定 --all，则按状态筛选
            # 若都没有，则 status_filter = False (未完成) 已在上面设置
            list_todos(
                show_all=show_all,
                status_filter=status_filter,
                tag_filter=args.tag,
                sort_by=args.sort,
                descending=args.desc
            )

    except Exception as e:
        print(f"发生错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()