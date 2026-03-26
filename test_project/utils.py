# -*- coding: utf-8 -*-
"""
Python 2 风格的工具模块 — 用于测试代码迁移 Agent
"""

import sys


def greet(name):
    """打印欢迎消息"""
    print "Hello, " + name + "!"
    print "Welcome to the system."


def count_items(n):
    """使用 xrange 计数"""
    total = 0
    for i in xrange(n):
        total += i
    print "Total:", total
    return total


def check_dict(d, key):
    """使用 dict.has_key() 检查"""
    if d.has_key(key):
        print "Found:", key
        return True
    else:
        print "Not found:", key
        return False


def iterate_dict(d):
    """使用 iteritems 迭代字典"""
    for k, v in d.iteritems():
        print k, "->", v


def to_unicode(s):
    """使用 unicode() 和 basestring"""
    if isinstance(s, basestring):
        return unicode(s, 'utf-8')
    return unicode(str(s), 'utf-8')


def handle_error():
    """使用旧式 except 语法"""
    try:
        result = 1 / 0
    except ZeroDivisionError, e:
        print "Error:", str(e)
        return None


if __name__ == "__main__":
    greet("World")
    count_items(10)
    check_dict({"a": 1, "b": 2}, "a")
