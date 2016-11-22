import json


VERSION = '3.1.0'


def parse_search_phrase(s):
    result = []
    quote = ''
    word = ''
    for x in range(len(s)):
        c = s[x]
        if not quote:
            if c == '"' or c == "'":
                quote = c
            elif c == ' ':
                if word:
                    result.append(word)
                    word = ''
            else:
                word += c
        else:
            if c == quote:
                quote = ''
            else:
                word += c
    if word:
        result.append(word)
    return result
