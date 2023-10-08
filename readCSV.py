import csv
#import scraper

i = 22200001
while i < 22201230:
    if i != 22200674 and i != 22200714:
        with open('2022\\' + str(i) + '.csv', mode='r') as file:
            csvFile = csv.DictReader(file)

            columnNames = []

            for row in csvFile:
                if "1" == row['eventmsgtype']:
                    print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                    break

    i += 1