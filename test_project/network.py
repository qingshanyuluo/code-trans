# -*- coding: utf-8 -*-
"""
Python 2 风格的网络模块 — 用于测试代码迁移 Agent
"""

import urllib2
import StringIO


def fetch_url(url):
    """使用 urllib2 获取 URL 内容"""
    try:
        response = urllib2.urlopen(url)
        content = response.read()
        print "Fetched", len(content), "bytes from", url
        return content
    except urllib2.URLError, e:
        print "Error fetching URL:", str(e)
        return None


def parse_response(data):
    """使用 StringIO 解析响应"""
    buffer = StringIO.StringIO(data)
    lines = buffer.readlines()
    print "Parsed", len(lines), "lines"
    return lines


def build_request(url, params):
    """构建 HTTP 请求"""
    encoded = urllib2.urlencode(params)
    full_url = url + "?" + encoded
    request = urllib2.Request(full_url)
    request.add_header("User-Agent", "Python-Migration-Test/1.0")
    print "Built request:", full_url
    return request


if __name__ == "__main__":
    url = "http://example.com"
    print "Testing network module..."
    content = fetch_url(url)
    if content is not None:
        lines = parse_response(content)
        print "Done! Got", len(lines), "lines"
