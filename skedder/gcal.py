from __future__ import print_function
import datetime
import pickle
import os.path
from pprint import pprint
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# import sys
# sys.exit()

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main(opts):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    
    # here we have different token paths because lambdas can only put writable files in /tmp/
    token_path_dev = 'tmp/token.pickle'
    token_path_prod = '/' + token_path_dev
    token_path = token_path_prod if opts.get('production', False) else token_path_dev
    # print("token path is ", token_path)
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    # os.remove(token_path)

    if os.path.exists(token_path):
        # if os.path.getsize(token_path) > 0:
        with open(token_path, 'rb') as token:
            # print('Token exists', token)
            creds = pickle.load(token)
            # print('Creds: ', creds)
    elif os.path.exists(token_path_dev): #check dev location for initial pickle
        with open(token_path_dev, 'rb') as token:
            # print('Token exists', token)
            creds = pickle.load(token)
            # print('Creds: ', creds)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # print('Attempting to refresh creds')
            creds.refresh(Request())
        else:
            # print('Valid creds, starting flow')
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            # print('Storing creds', creds)
            pickle.dump(creds, token)


    service = build('calendar', 'v3', credentials=creds)
    return service
    
    # Call the Calendar API
    # now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    # print('Getting the upcoming 10 events')
    # events_result = service.events().list(calendarId='primary', timeMin=now,
    #                                     maxResults=10, singleEvents=True,
    #                                     orderBy='startTime').execute()

    # events_result = service.events().list(
    #     calendarId='XXXXXXXXXXXXXXXXXX'
    # ).execute()
    # events = events_result.get('items', [])
    # pprint(events)

    # if not events:
    #     print('No upcoming events found.')
    # for event in events:
    #     start = event['start'].get('dateTime', event['start'].get('date'))
        # print(start, event['summary'])

if __name__ == '__main__':
    main()