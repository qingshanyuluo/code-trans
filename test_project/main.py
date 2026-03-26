# -*- coding: utf-8 -*-
"""
Python 2 风格的主入口 — 用于测试代码迁移 Agent
"""

import sys
from utils import greet, count_items, check_dict


def get_user_name():
    """使用 raw_input 获取用户输入"""
    name = raw_input("Please enter your name: ")
    return name


def show_menu():
    """显示菜单"""
    print "=" * 40
    print "  Welcome to the Demo Application"
    print "=" * 40
    print "1. Greet"
    print "2. Count"
    print "3. Check Dict"
    print "4. Exit"
    print "-" * 40


def process_numbers(numbers):
    """处理数字列表"""
    result = []
    for i in xrange(len(numbers)):
        result.append(numbers[i] * 2)
    print "Processed:", result
    return result


def main():
    show_menu()
    name = get_user_name()
    greet(name)

    choice = raw_input("Enter choice (1-4): ")

    if choice == "1":
        greet(name)
    elif choice == "2":
        n = raw_input("Enter number: ")
        count_items(int(n))
    elif choice == "3":
        data = {"name": name, "age": 25}
        check_dict(data, "name")
    elif choice == "4":
        print "Goodbye!"
        sys.exit(0)
    else:
        print "Invalid choice!"


if __name__ == "__main__":
    main()
