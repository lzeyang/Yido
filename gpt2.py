import sys
import json
import argparse
from datetime import datetime

FILE = "todo.json"


def load():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save(todos):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="命令行 Todo 工具")
    sub = parser.add_subparsers(dest="cmd")

    # 添加
    p = sub.add_parser("add", help="添加待办")
    p.add_argument("content", nargs="+", help="待办内容")
    p.add_argument("-t", "--tag", default="", help="标签，多个标签用逗号分隔")
    p.add_argument("-d", "--due", default="", help="最晚完成期限，如 2026-08-20")

    # 完成
    p = sub.add_parser("done", help="标记完成")
    p.add_argument("id", type=int, help="待办编号")

    # 删除
    p = sub.add_parser("delete", aliases=["del", "rm"], help="删除待办")
    p.add_argument("id", type=int, help="待办编号")

    # 修改
    p = sub.add_parser("edit", aliases=["modify"], help="修改待办")
    p.add_argument("id", type=int, help="待办编号")
    p.add_argument("content", nargs="*", help="新的待办内容")
    p.add_argument("-t", "--tag", help="新的标签，多个标签用逗号分隔")
    p.add_argument("-d", "--due", help="新的期限，如 2026-08-20")

    # 查看/筛选/排序
    p = sub.add_parser("list", aliases=["ls"], help="查看待办")
    p.add_argument("-s", "--status", choices=["all", "pending", "done"],
                   default="all", help="按完成状态筛选")
    p.add_argument("-t", "--tag", help="按标签筛选")
    p.add_argument("--sort", choices=["id", "created", "due"],
                   default="id", help="排序：id/created/due")

    args = parser.parse_args()
    todos = load()

    if not args.cmd:
        parser.print_help()
        return

    if args.cmd == "add":
        due = args.due
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print("错误：期限格式应为 YYYY-MM-DD")
                return

        todo = {
            "id": max((x["id"] for x in todos), default=0) + 1,
            "content": " ".join(args.content),
            "done": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tags": [x.strip() for x in args.tag.split(",") if x.strip()],
            "due": due
        }
        todos.append(todo)
        save(todos)
        print(f"已添加：[{todo['id']}] {todo['content']}")

    elif args.cmd == "done":
        todo = next((x for x in todos if x["id"] == args.id), None)
        if not todo:
            print("错误：找不到该待办")
            return
        todo["done"] = True
        save(todos)
        print(f"已完成：[{todo['id']}] {todo['content']}")

    elif args.cmd in ("delete", "del", "rm"):
        todo = next((x for x in todos if x["id"] == args.id), None)
        if not todo:
            print("错误：找不到该待办")
            return

        todos.remove(todo)

        # 删除后重新编号，保证编号连续、不留空号
        for i, item in enumerate(todos, 1):
            item["id"] = i

        save(todos)
        print(f"已删除：{todo['content']}")

    elif args.cmd in ("edit", "modify"):
        todo = next((x for x in todos if x["id"] == args.id), None)
        if not todo:
            print("错误：找不到该待办")
            return

        if args.content:
            todo["content"] = " ".join(args.content)

        if args.tag is not None:
            todo["tags"] = [x.strip() for x in args.tag.split(",") if x.strip()]

        if args.due is not None:
            if args.due:
                try:
                    datetime.strptime(args.due, "%Y-%m-%d")
                except ValueError:
                    print("错误：期限格式应为 YYYY-MM-DD")
                    return
            todo["due"] = args.due

        save(todos)
        print(f"已修改：[{todo['id']}] {todo['content']}")

    elif args.cmd in ("list", "ls"):
        result = [
            x for x in todos
            if args.status == "all"
            or (args.status == "done" and x["done"])
            or (args.status == "pending" and not x["done"])
        ]

        if args.tag:
            result = [x for x in result if args.tag in x.get("tags", [])]

        # 期限为空的待办排在最后
        if args.sort == "due":
            result.sort(key=lambda x: (not x.get("due"), x.get("due", "")))
        elif args.sort == "created":
            result.sort(key=lambda x: x.get("created_at", ""))
        else:
            result.sort(key=lambda x: x["id"])

        if not result:
            print("暂无符合条件的待办")
            return

        print(f"{'编号':<6}{'状态':<8}{'期限':<13}{'标签':<20}内容")
        print("-" * 75)

        for x in result:
            status = "已完成" if x["done"] else "待完成"
            due = x.get("due") or "-"
            tags = ",".join(x.get("tags", [])) or "-"
            print(f"{x['id']:<6}{status:<8}{due:<13}{tags:<20}{x['content']}")


if __name__ == "__main__":
    try:
        main()
    except OSError as e:
        print(f"文件操作失败：{e}")
    except Exception as e:
        print(f"程序运行出错：{e}")