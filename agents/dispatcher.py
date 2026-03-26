"""
Dispatcher Agent — 搜索模式提取与文件定位工具
"""

import re


TASK_SEARCH_PATTERNS = {
    "print": r'\bprint\s+[^(]',
    "print()": r'\bprint\s+[^(]',
    "raw_input": r'\braw_input\s*\(',
    "xrange": r'\bxrange\s*\(',
    "unicode": r'\bunicode\s*\(',
    "basestring": r'\bbasestring\b',
    "has_key": r'\.has_key\s*\(',
    "except": r'\bexcept\s+\w+\s*,\s*\w+',
    "urllib2": r'\burllib2\b',
    "StringIO": r'\b(StringIO|cStringIO)\b',
    "iteritems": r'\.(iteritems|itervalues|iterkeys)\s*\(',
    "long": r'\blong\s*\(',
    "range": r'\bxrange\b',
    "dict.items": r'\.(iteritems|itervalues|iterkeys)\b',
}


def extract_search_pattern(task_description: str) -> str:
    """
    从任务描述中提取搜索模式。
    优先使用预定义映射，否则尝试从描述中提取关键词。
    """
    desc_lower = task_description.lower()

    # 尝试匹配预定义的搜索模式
    for keyword, pattern in TASK_SEARCH_PATTERNS.items():
        if keyword.lower() in desc_lower:
            return pattern

    # 尝试从描述中提取引号包裹的模式
    quoted = re.findall(r'[`"\'](.*?)[`"\']', task_description)
    if quoted:
        return re.escape(quoted[0])

    # 最后的回退: 使用描述中的第一个英文关键词
    words = re.findall(r'[a-zA-Z_]\w+', task_description)
    if words:
        return r'\b' + re.escape(words[0]) + r'\b'

    return r'.'
