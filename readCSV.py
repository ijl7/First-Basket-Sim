import csv
#import scraper

i = 22200001
while i < 22201230:
    if i != 22200674 and i != 22200714:
        with open('2022\\' + str(i) + '.csv', mode='r') as file:
            csvFile = csv.DictReader(file)

            columnNames = []

            for row in csvFile:
                if "10" == row['eventmsgtype']:
                    print(row['player1_name'] + ' vs ' + row['player2_name'] + ', ' + row['player3_team_abbreviation'] + ' wins tip')
                    break

            for row in csvFile:
                if "1" == row['eventmsgtype']:
                    print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                    break

    i += 1