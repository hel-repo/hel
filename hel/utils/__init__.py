# -*- coding: utf-8 -*-
import copy
import json


VERSION = '3.4.0'


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


def update(d, nd):
    if type(d) == dict and type(nd) == dict:
        result = copy.copy(d)
        for k, v in nd.items():
            if k in d:
                data = update(d[k], v)
                if data is not None:
                    result[k] = data
                else:
                    del result[k]
            else:
                if v is not None:
                    result[k] = v
        return result
    else:
        return nd
