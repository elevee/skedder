from config.config_loader import ConfigLoader
# from requests import get
import requests
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
# from gcal import main
import utilities as utils
import time
from datetime import datetime, timedelta
import dateutil.parser as parser
from pprint import pprint

import sys

calendars = ConfigLoader().config() #load in team calendars

def parse_games(teamName, url, seasonStartYear):
    def column_is(i):
        return {
            0: "date",
            1: "result",
            2: "opponent",
            3: "location",
            4: "time"
        }.get(i, "invalid")    # invalid is default if i not found

    source = requests.get(url).text
    soup = BeautifulSoup(source, 'html.parser')
    rows = soup.find('tbody').find_all('tr') # Site already filters games that have been played
    games = []
    game_count = 0
    first_game_month = None #need to track first game month to compare when calculating year
    print('you have ' + str(len(rows)) + ' total games:')
    for row in rows:
        game = {}
        if 'completed' in row['class']:
            print('this is a completed game')
            game['completed'] = True;
        else:
            print('this is a scheduled game')
            game['completed'] = False;
        colIdx = 0
        for cell in row.find_all('td'):
            column = column_is(colIdx)
            # print('column is '+column)
            output = ""
            if column == "date":
                date_array = utils.cell_data_to_list(cell)
                date_array.pop(0) #remove day string (e.g. Mon)

                if rows.index(row) == 0: #first game of season
                    first_game_month = utils.getMonthNumber(date_array[0]) #set first game month
                
                date_array.append(str(
                    utils.getGameYear(
                        first_game_month,
                        utils.getMonthNumber(date_array[0]),
                        seasonStartYear
                    )
                ))
                _date = ' '.join(date_array)
                output = utils.format(column, _date)
            elif column == "result":
                output = None
            elif column == "opponent":
                opp_array = utils.cell_data_to_list(cell)
                is_home = False if len(opp_array) > 1 and opp_array[0].strip() == "@" else True
                game['isHome'] = is_home
                if not is_home:
                    opp_array.pop(0)
                output = ' '.join(opp_array)
                game['away'] = output if is_home else teamName
                game['home'] = teamName if is_home else output
            elif column == "time":
                if game['completed']:
                    print('game\'s been completed')
                    game['boxscore_url'] = cell.a['href']
                    output = None
                else:
                    output = utils.format(column, cell)
            else:
                output = cell.text.strip()
            game[column] = output
            colIdx = colIdx+1
        games.append(game)
        game_count = game_count+1
        # print('____________')
    pprint(games)
    return games

def parse_boxscore(game):
    boxscore = {}
    html = []
    source = requests.get(game['boxscore_url']).text
    soup = BeautifulSoup(source, 'html.parser')
    
    gamesheet_url = soup.find('div', class_='live_game_sheet').find('a')['href']
    game_sheet_source = requests.get(gamesheet_url).text
    gamesheet_soup = BeautifulSoup(game_sheet_source, 'html.parser')
    boxscore['time'] = utils.format('time', gamesheet_soup.find('span', {'id': 'game_time'}))
    scores = soup.find('span', class_='scores')
    scoring_summary = soup.find('ul', class_='scoring_summary')
    html.append(f"<h1>{game['away']}  {scores.find('span', class_='away').text}   ")
    html.append(f"{game['home']}  {scores.find('span', class_='home').text} </h1>")
    html.append(f"More: <a href='{game['boxscore_url']}'>Gamesheet</a><br><br>")
    
    # for li in scoring_summary.find_all('li'):
    #     if li['class'] and 'interval_row' in li['class']:
    #         # print(li.find('span').text.strip())
    #         print('hi')
    #         # html.append(f"<h4>{li.find('span').text} Period</h4>")
    #     if 'scoring_info' in li['class']:
    #         print('score!')
    
    boxscore['description'] = ''.join(html)

    #we return the time (which is no longer available on the sked), and the description, a long string with final score and link to gamesheet
    return boxscore 

def lambda_handler(event, context):
    if utils.service:
        for calendar in calendars:
            games = parse_games(calendar['team'], calendar['url'], calendar['season_start_year'])
            if games and len(games) > 0:
                pprint(games)

                for game in games: # For each (remaining) game:
                    game_string = (game['opponent'] if game['isHome'] else calendar['team']) + \
                        " at " + \
                        (calendar['team'] if game['isHome'] else game['opponent'])
                    # print(game_string + " already on cal? " + ("Yes" if utils.game_already_on_date(game, calendar['gcal_id']) else "No")) # check calendar for existing event for that team on that day
                    description = None

                    if 'completed' in game and 'boxscore_url' in game:
                        boxscore_obj = parse_boxscore(game)
                        game['time'] = boxscore_obj['time'] # start time brought back from the dead!
                        game['description'] = boxscore_obj['description']

                    existing_game = utils.game_already_on_date(game, calendar['gcal_id'])
                
                    #cleanup events
                    minDate = utils.rfcify(game['date'])
                    minDate = utils.add_hours(minDate, 3) #need to advance the min time a few hours to account for spillover from prev date's late night games
                    maxDate = utils.add_hours(minDate, 24)
                    resp = utils.service.events().list(calendarId=calendar['gcal_id'], timeMin=minDate, timeMax=maxDate).execute()
                    if resp['items'] and len(resp['items']) > 1:
                        for itm in resp['items']:
                            utils.remove_game(itm, calendar['gcal_id']) 

                    if existing_game: # if one exists, the datetime, location, home, away teams match up, continue the loop (skipping an insert)
                        if (utils.is_same_game(existing_game, game)):
                            if 'completed' in game and game['completed'] and not 'description' in existing_game:
                                utils.update_game(game, calendar['gcal_id'], existing_game) # add completed game (update description)
                                print(f"{game_string} game exists but has been updated with scoresheet info")
                            else:
                                print(f"{game_string} game exists and is correct; not continuing work.")
                        else:
                            print(f"{game_string}: something's different. Deleting existing one.")
                            utils.add_game(game, calendar['gcal_id']) # add new game (old one is set to delete at end of func)
                    else:
                        utils.add_game(game, calendar['gcal_id'])
                
                # cleanup any orphaned events on different dates or with wrong info
                calEvents = utils.games_on_calendar(games[0]['date'], calendar['gcal_id']) #grab events from date of first remaining game
                orphaned_games = utils.find_outdated_events(calEvents, games)
                if orphaned_games and len(orphaned_games) > 0:
                    print('Found orphaned records!')
                    pprint(orphaned_games)
                    for orphan in orphaned_games:
                        print('Orphaned record about to be removed: ', orphan['id']) # remove games from calEvents as we check their validity
                        utils.remove_game(orphan, calendar['gcal_id'])
            else:
                print("No games found for ", calendar['team'])


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