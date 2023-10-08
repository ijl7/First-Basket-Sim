import csv
#import scraper

i = 22200001
while i < 22201231:
    if i != 22200674 and i != 22200714:
        with open('2022\\' + str(i) + '.csv', mode='r') as file:
            csvFile = csv.DictReader(file)

            homeLineup = []
            awayLineup = []

            for row in csvFile:
                if "10" == row['eventmsgtype']:
                    homeLineup.append(row['home_player_1'])
                    homeLineup.append(row['home_player_2'])
                    homeLineup.append(row['home_player_3'])
                    homeLineup.append(row['home_player_4'])
                    homeLineup.append(row['home_player_5'])
                    awayLineup.append(row['away_player_1'])
                    awayLineup.append(row['away_player_2'])
                    awayLineup.append(row['away_player_3'])
                    awayLineup.append(row['away_player_4'])
                    awayLineup.append(row['away_player_5'])
                    print(homeLineup)
                    print(awayLineup)
                    print(row['player1_name'] + ' vs ' + row['player2_name'] + ', ' + row['player3_team_abbreviation'] + ' wins tip')
                    break

            for row in csvFile:
                if "1" == row['eventmsgtype']:
                    print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                    break

    i += 1