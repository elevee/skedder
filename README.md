# Skedder

A script that parses adult league hockey schedules that are known to change without notice and imports them into corresponding shared Google Calendars.


Place teams you want to track in `skedder/config/config.json`, along with their corresponding shared Google Calendar ids:
```json
[{
    "url": "http://toyota.frontline-connect.com/leagueschedule.cfm?fac=toyota&facid=1&Sched_id=910&teamid=5519&gtypeid=0&divisionid=0",
    "team": "Kings",
    "gcal_id": "xxxxxxxxxxxxxxxxxxxxxxxxxx@group.calendar.google.com"
}, {
    "url": "http://toyota.frontline-connect.com/leagueschedule.cfm?fac=toyota&facid=1&Sched_id=938&teamid=5626&gtypeid=0&divisionid=0",
    "team": "Harambe",
    "gcal_id": "xxxxxxxxxxxxxxxxxxxxxxxxxx@group.calendar.google.com"
}]
```

From there, run `make build` from the (home) directory that contains the `Makefile`. This packs the project with its dependencies into a zip which can be uploaded to a service like Amazon Lambda.