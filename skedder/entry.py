from config.config_loader import ConfigLoader
# from requests import get
import requests
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from gcal import main
from datetime import datetime, timedelta
import dateutil.parser as parser
from pprint import pprint
import arrow #for DST

# import sys
# sys.exit('exiting early')

#load gcal in and make it available
service = main({
    # "production": True
})

calendars = ConfigLoader().config() #load in team calendars

def rfcify(date, time=None): #converts dates from '%m-%d-%Y' [HH:MM:SS] to rfc format
    dst = arrow.get(date, "MM-DD-YYYY").to('US/Pacific').dst()
    offset = "-07:00" if dst.seconds > 0 else "-08:00"
    if time: # date & time
        return parser.parse(f"{date} {time}").isoformat() + offset
    else: # date only
        return datetime.strptime(date, '%m-%d-%Y').isoformat() + offset


def add_hours(start, hours=2):
    return (parser.parse(start) + timedelta(hours=hours)).isoformat()

def location_case(location):
    return location if location == "NHL" else location.title()

def game_already_on_date(game, calId):
    # print("game date? ", game['date'])
    min_date = rfcify(game['date']) # timeMin needs to be a RFC3339 timestamp
    max_date = add_hours(min_date, 24)
    try:
        result = service.events().list(calendarId=calId, timeMin=min_date, timeMax=max_date).execute()
        # print(f"length of items {len(result['items'])}")
        return result['items'][0] if result and len(result['items']) > 0 else None
    except Exception as exception:
        print("game_already_on_date:  Error checking if game already on date", exception)
        pass

def matchup_format(away, home):
    return f"{away} @ {home}"

def add_game(game, calId):
    start_time = rfcify(game['date'], game['time'])
    tz = 'America/Los_Angeles'
    event = {
        'summary': matchup_format(game['away'], game['home']),
        'location': location_case(game['location']),
        'start': {
            'dateTime': start_time,
            'timeZone': tz,
        },
        'end': {
            'dateTime': add_hours(start_time),
            'timeZone': tz,
        }
    }
    print(f"Adding {event['summary']}")
    try:
        return service.events().insert(calendarId=calId, body=event).execute()
    except:
        print('Error removing game', game['id'], matchup_format(game['away'], game['home']))
        return False

def remove_game(game, calId):
    try:
        print(f"Removing {game['id']} - {game['summary']}...")
        if service.events().delete(calendarId=calId, eventId=game['id']).execute() == '': return True
    except:
        print('Error removing game', game['id'], matchup_format(game['away'], game['home']))
        return False

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
    for calendar in calendars:
        games = parse_games(calendar['url'])
        pprint(games)
        for game in games: # For each (remaining) game:
            # print(f"{game['away']} at {game['home']} already on cal? ", "Yes" if game_already_on_date(game, calendar['gcal_id']) else "No") # check calendar for existing event for that team on that day
            
            existing_game = game_already_on_date(game, calendar['gcal_id'])
        
            #cleanup events
            minDate = rfcify(game['date'])
            maxDate = add_hours(minDate, 24)
            resp = service.events().list(calendarId=calendar['gcal_id'], timeMin=minDate, timeMax=maxDate).execute()
            if resp['items'] and len(resp['items']) == 2:
            #     print(f"Duplicates on {minDate}!")
                for itm in resp['items']:
                    remove_game(itm, calendar['gcal_id']) 

            if existing_game: # if one exists, the datetime, location, home, away teams match up, continue the loop (skipping an insert)
                if (rfcify(game['date'], game['time']) == existing_game['start']['dateTime'] and 
                    matchup_format(game['away'], game['home']) == existing_game['summary'] and
                    location_case(game['location']) == existing_game['location']):
                    print(f"{game['away']} at {game['home']} game exists and is correct; not continuing work.")
                else:
                    print(f"{game['away']} at {game['home']}: something's different. Deleting existing one.")
                    if remove_game(existing_game, calendar['gcal_id']): # else, delete the existing event for that day for that team
                        add_game(game, calendar['gcal_id'])
            else:
                add_game(game, calendar['gcal_id'])



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