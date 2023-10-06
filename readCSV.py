import csv
#import scraper

i = 21800001
with open('2022\\' + str(i) + '.csv', mode='r') as file:
    csvFile = csv.DictReader(file)

    columnNames = []

    for row in csvFile:
        if "1" == row['eventmsgtype']:
            print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
            break