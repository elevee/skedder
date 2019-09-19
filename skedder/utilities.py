from gcal import main
from time import strptime
from datetime import datetime, timedelta
import dateutil.parser as parser
from pprint import pprint
import arrow #for DST

import sys

# FYI THERE ARE TWO strptime METHODS. One on datetime, one on time

#load gcal in and make it available
service = main({
    # "production": True
    "testing": True
})

def add_game(game, calId):
    pprint('game is')
    pprint(game)
    start_time = rfcify(game['date'], game['time'])
    tz = 'America/Los_Angeles'
    event = {
        'summary': matchup_format(game['away'], game['home']),
        'location': game['location'],
        'start': {
            'dateTime': start_time,
            'timeZone': tz,
        },
        'end': {
            'dateTime': add_hours(start_time),
            'timeZone': tz,
        }
    }
    if 'description' in game:
        event['description'] = game['description']
    print(f"Adding {event['summary']}")
    try:
        return service.events().insert(calendarId=calId, body=event).execute()
    except:
        print('Error removing game', game['id'], matchup_format(game['away'], game['home']))
        return False

def add_hours(start, hours=2):
    return (parser.parse(start) + timedelta(hours=hours)).isoformat()

def cell_data_to_list(raw_cell):
    array_with_empty_items = raw_cell.text.strip().split(' ')
    print(array_with_empty_items)
    return list(filter(None, array_with_empty_items)) #gets rid of empty array elements

def find_outdated_events(calEvents, webEvents):
    # print("ooh we removing outdated!")
    remaining_events = calEvents
    for webEvent in webEvents: #for each event on the official cal
        for calEvent in remaining_events: # check whether existing gcal events
            if is_same_game(calEvent, webEvent): # are the same
                remaining_events.remove(calEvent) # and exclude them from being deleted
                continue
    return remaining_events

def format(input_type, cell):
    if input_type == 'date':
        return datetime.strptime(cell, '%b %d %Y').strftime('%m-%d-%Y')
    elif input_type == 'time':
        time_array = cell.text.strip().split(' ')
        time_array.pop() # get rid of PST/PDT timezone
        return ' '.join(time_array)

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

def games_on_calendar(startDate, calId): # provided a start date, returns list of games on gCal
    try:
        calEvents = service.events().list(calendarId=calId, timeMin=rfcify(startDate)).execute()
        return calEvents['items']
    except Exception as exception:
        print("something went wrong with games_on_calendar", exception)

def getMonthNumber(monthAbbrev):
    return strptime(monthAbbrev, '%b').tm_mon

def getGameYear(initialGameMonth, currentGameMonth):
    current_year = datetime.now().year;
    return current_year + 1 if initialGameMonth > currentGameMonth else current_year

def is_same_game(calEvent, webEvent):
    return (rfcify(webEvent['date'], webEvent['time']) == calEvent['start']['dateTime'] and 
        matchup_format(webEvent['away'], webEvent['home']) == calEvent['summary'] and
        webEvent['location'] == calEvent['location'])

def is_inside_games(calEvent, games):
    # todo: implement as a lambda function to find out if a calEvent is inside games array at all. Could delete right then.
    # return list(filter(lambda x: x['id'] === xxxx, calEvent))
    pass

def matchup_format(away, home):
    return f"{away} @ {home}"

def remove_game(game, calId):
    try:
        print(f"Removing {game['id']} - {game['summary']}...")
        if service.events().delete(calendarId=calId, eventId=game['id']).execute() == '': return True
    except:
        print('Error removing game', game['id'], matchup_format(game['away'], game['home']))
        return False

def rfcify(date, time=None): #converts dates from '%m-%d-%Y' [HH:MM:SS] to rfc format
    dst = arrow.get(date, "MM-DD-YYYY").to('US/Pacific').dst()
    offset = "-07:00" if dst.seconds > 0 else "-08:00"
    if time: # date & time
        return parser.parse(f"{date} {time}").isoformat() + offset
    else: # date only
        return datetime.strptime(date, '%m-%d-%Y').isoformat() + offset

def update_game(game, calId, existing_game):
    event = existing_game
    event['description'] = game['description'] #just adding description to the existing event
    print(f"Updating Event ID:{existing_game['id']}")
    try:
        return service.events().update(calendarId=calId, eventId=existing_game['id'], body=event).execute()
    except:
        print('Error updating game', existing_game['id'])
        return False
