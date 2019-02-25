import unittest
import sys
sys.path.append('/Users/elevine/Sites/skedder/skedder/')
# import os
# import entry
from pprint import pprint
# import testing_ground as tg
import utilities as utils
from seed import games, calEvents


class TestOutdatedEvents(unittest.TestCase):

    def test_find_outdated_events(self):
        # print(games)
        # print(calEvents)
        print('length before method: ', len(calEvents))
        remaining = utils.find_outdated_events(calEvents['items'], games)
        print('length after method: ', len(remaining))
        self.assertEqual(len(remaining), 1)
        pprint(remaining)



# class TestStringMethods(unittest.TestCase):

#     def test_upper(self):
#         self.assertEqual('foo'.upper(), 'FOO')

#     def test_isupper(self):
#         self.assertTrue('FOO'.isupper())
#         self.assertFalse('Foo'.isupper())

#     def test_split(self):
#         s = 'hello world'
#         self.assertEqual(s.split(), ['hello', 'world'])
#         # check that s.split fails when the separator is not a string
#         with self.assertRaises(TypeError):
#             s.split(2)

if __name__ == '__main__':
    unittest.main()