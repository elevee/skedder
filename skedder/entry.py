from config.config_loader import ConfigLoader
# from requests import get
import requests
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
# from gcal import main
import utilities as utils
from datetime import datetime, timedelta
import dateutil.parser as parser
from pprint import pprint

import sys

calendars = ConfigLoader().config() #load in team calendars

def parse_games(url):
    # print(calendar['url'])
    
    def column_is(i):
        return {
            0: "date",
            1: "time",
            2: "home",
            3: "away",
            4: "location"
        }.get(i, "invalid")    # invalid is default if i not found

    source = requests.get(url).text
    soup = BeautifulSoup(source, 'html.parser')
    rows = soup.find('div', class_='tupcoming').find_all('tr', class_='hidden-xs') # Site already filters games that have been played
    games = []
    game_count = 0
    print('row length is', len(rows))
    for row in rows:
        game = {}
        colIdx = 0
        for cell in row.find_all('td'):
            column = column_is(colIdx)
            output = ""
            if column == "date":
                date_array = cell.text.strip('\n').split(' ')
                date_array.pop(0) #remove day string
                _date = ' '.join(date_array)
                output = datetime.strptime(_date, '%b %d, %Y').strftime('%m-%d-%Y')
            elif column == "time":
                output = cell.text.split('-')[0].strip()
            else:
                output = cell.text.strip()
            game[column] = output 
            colIdx = colIdx+1
            # print('++++')
        # print(f"Game #{game_count+1}", game)
        games.append(game)
        game_count = game_count+1
        # print('____________')
    return games


def lambda_handler(event, context):
    if utils.service:
        for calendar in calendars:
            games = parse_games(calendar['url'])
            pprint(games)
            for game in games: # For each (remaining) game:
                # print(f"{game['away']} at {game['home']} already on cal? ", "Yes" if game_already_on_date(game, calendar['gcal_id']) else "No") # check calendar for existing event for that team on that day
                
                existing_game = utils.game_already_on_date(game, calendar['gcal_id'])
            
                #cleanup events
                minDate = utils.rfcify(game['date'])
                maxDate = utils.add_hours(minDate, 24)
                resp = utils.service.events().list(calendarId=calendar['gcal_id'], timeMin=minDate, timeMax=maxDate).execute()
                if resp['items'] and len(resp['items']) > 1:
                #     print(f"Duplicates on {minDate}!")
                    for itm in resp['items']:
                        utils.remove_game(itm, calendar['gcal_id']) 

                if existing_game: # if one exists, the datetime, location, home, away teams match up, continue the loop (skipping an insert)
                    if (utils.is_same_game(existing_game, game)):
                        print(f"{game['away']} at {game['home']} game exists and is correct; not continuing work.")
                    else:
                        print(f"{game['away']} at {game['home']}: something's different. Deleting existing one.")
                        # if remove_game(existing_game, calendar['gcal_id']): # else, delete the existing event for that day for that team
                        #     add_game(game, calendar['gcal_id'])
                # else:
                    # add_game(game, calendar['gcal_id'])
            # cleanup any orphaned events on different dates
            calEvents = utils.games_on_calendar(games[0]['date'], calendar['gcal_id']) #grab events from date of first remaining game
            orphaned_games = utils.find_outdated_events(calEvents, games)
            if orphaned_games and len(orphaned_games) > 0:
                print('Found orphaned records!')
                pprint(orphaned_games)
                for orphan in orphaned_games:
                    print('Found orphaned records: ', orphan['id']) # remove games from calEvents as we check their validity
                    utils.remove_game(orphan, calendar['gcal_id'])


# sys.exit('exiting early')

# sampleGame = {
#   'away': 'Harambe',
#   'date': '02-26-2019',
#   'home': 'Bad Beat',
#   'location': 'OLYMPIC',
#   'time': '09:00 PM'
# }


# deleting_obj = {
#   'iCalUID': 'xxxxxxxxxxxx@google.com',
#   'id': 'xxxxxxxxxxxxxxxxxxxx',
#   'summary': 'Dog & Pony show'
# }
# cid = 'xxxxxxxxxxxxxxxxxxx@group.calendar.google.com'

# response = add_game(sampleGame, cid)
# response = remove_game(deleting_obj, cid)
# pprint(response)
# print('Event created: %s' % (response.get('htmlLink')))

# {
#     "summary": "blah",
#     "location": "location",
#     "start": {
#         "dateTime": "2019-02-26 21:00:00",
#         "timeZone": 'America/Los_Angeles',
#     },
#     "end": {
#         "dateTime": "2019-02-26 23:00:00",
#         "timeZone": 'America/Los_Angeles',
#     }
# }

if __name__ == "__main__": # runnable on CLI
    class Event:
        def get(self, key):
            e = { 'key' : 'value' }
            return e[key]
    context = 'context'
    event = Event()
    lambda_handler(event, context)