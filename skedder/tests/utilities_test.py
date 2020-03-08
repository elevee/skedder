import unittest
import sys
sys.path.append('/Users/ericlevine/Sites/skedder/skedder/')
# import os
# import entry
from pprint import pprint
# import testing_ground as tg
import utilities as utils
from seed import sampleCalEvents, sampleWebEvents

class TestUtilityMethods(unittest.TestCase):

    def test_add_hours(self):
        sampleGame = sampleWebEvents[0]
        # pprint(sampleGame)
        self.assertEqual(utils.add_hours(sampleGame['date']), '2019-09-09T02:00:00', 'Date not adding 2 hours by default to time string')
        self.assertEqual(utils.add_hours('2019-09-09T15:00:00'), '2019-09-09T17:00:00', 'Date not adding 2 hours by default to ISO string (with specific time)')
        self.assertEqual(utils.add_hours('2019-09-09T15:00:00', 5), '2019-09-09T20:00:00', 'Date not adding x hours when passed as 2nd argument to ISO string (with specific time)')
#         print('length before method: ', len(calEvents))
#         remaining = utils.find_outdated_events(calEvents['items'], games)
#         print('length after method: ', len(remaining))
#         self.assertEqual(len(remaining), 1)


if __name__ == '__main__':
    unittest.main()