# -*- coding: utf-8 -*-
# http://stackoverflow.com/a/8866661
def are_equal(a, b):
    unmatched = list(b)
    for element in a:
        try:
            unmatched.remove(element)
        except ValueError:
            return False
    return not unmatched
