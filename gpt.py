import sys
import json
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
    if len(sys.argv) < 2:
        print("用法：python todo.py [add|done|list] ...")
        return

    todos = load()
    cmd = sys.argv[1]

    if cmd == "add":
        if len(sys.argv) < 3:
            print("错误：请输入待办内容")
            return
        todo = {
            "id": max([x["id"] for x in todos], default=0) + 1,
            "content": " ".join(sys.argv[2:]),
            "done": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        todos.append(todo)
        save(todos)
        print(f"已添加：[{todo['id']}] {todo['content']}")

    elif cmd == "done":
        if len(sys.argv) != 3 or not sys.argv[2].isdigit():
            print("用法：python todo.py done 编号")
            return
        todo_id = int(sys.argv[2])
        todo = next((x for x in todos if x["id"] == todo_id), None)
        if not todo:
            print("错误：找不到该待办")
            return
        todo["done"] = True
        save(todos)
        print(f"已完成：[{todo_id}] {todo['content']}")

    elif cmd == "list":
        # 默认显示全部；可用 pending/done 筛选
        status = sys.argv[2] if len(sys.argv) > 2 else "all"
        if status not in ("all", "pending", "done"):
            print("用法：python todo.py list [all|pending|done]")
            return

        result = [
            x for x in todos
            if status == "all"
            or (status == "done" and x["done"])
            or (status == "pending" and not x["done"])
        ]

        if not result:
            print("暂无待办")
            return

        print(f"{'编号':<6}{'状态':<8}{'创建时间':<20}内容")
        print("-" * 60)
        for x in result:
            state = "已完成" if x["done"] else "待完成"
            print(f"{x['id']:<6}{state:<8}{x['created_at']:<20}{x['content']}")

    else:
        print(f"错误：未知命令 '{cmd}'")


if __name__ == "__main__":
    try:
        main()
    except OSError as e:
        print(f"文件操作失败：{e}")
    except Exception as e:
        print(f"程序运行出错：{e}")