import json


VERSION = '0.6.1'


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


def jexc(http_exc, info=None):
    if not info:
        info = http_exc.explanation
    data = {
        'message': info,
        'code': http_exc.code,
        'title': http_exc.title,
        'success': False
    }
    e = http_exc()
    e.content_type = 'application/json'
    e.body = json.dumps(data).encode()
    raise e
