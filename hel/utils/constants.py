import re


class Constants:

    # Since MongoDB doesn't allow periods in key names,
    # we need to use names with them replaced by other char,
    # which is defined here.
    key_replace_char = '\uf123'

    # The regexp used to validate a package name
    name_pattern = re.compile('^[A-Za-z0-9-]+$')

    date_format = '%Y-%m-%d %H:%M:%S'
