# -*- coding: utf-8 -*-

import unittest
import re
import unicodedata
import textwrap


def _string_sanity_check(string):
    if string is None:
        return ''
    if not isinstance(string, basestring):
        return str(string)
    return string


''' Tests if string contains a substring. '''


def includes(haystack, needle):
    haystack = _string_sanity_check(haystack)
    needle = _string_sanity_check(needle)
    if needle in haystack:
        return True
    else:
        return False

# ---


class FilterModule(object):

    def filters(self):
        return {
            'includes': includes
        }

# ---


class TestStringUtlisFunctions(unittest.TestCase):

    def test_includes(self):
        self.assertEqual(includes('foobar', 'ob'), True)
        self.assertEqual(includes('foobar', 'qux'), False)
        self.assertEqual(includes('foobar', 'bar'), True)
        self.assertEqual(includes('foobar', 'buzz'), False)
        self.assertEqual(includes(12345, 34), True)
        self.assertEqual(includes(12345, 6), False)
        self.assertEqual(includes('', 34), False)
        self.assertEqual(includes(None, 34), False)
        self.assertEqual(includes(None, ''), True)


if __name__ == '__main__':
    unittest.main()
