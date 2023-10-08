import csv
#import scraper

i = 22200001
playerTeam = {}
tipWin = {}
while i < 22201230:
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
                    for player in homeLineup:
                        if playerTeam.__contains__(player):
                            None
                        else:
                            playerTeam.__setitem__(player, row['home_team_abbrev'])
                    for player in awayLineup:
                        if playerTeam.__contains__(player):
                            None
                        else:
                            playerTeam.__setitem__(player, row['away_team_abbrev'])       
                    print(row['player1_name'] + ' vs ' + row['player2_name'] + ', ' + row['player3_team_abbreviation'] + ' wins tip')
                    homeWin = tipWin.__contains__(playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Win')
                    homeLoss = tipWin.__contains__(playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Loss')
                    awayWin = tipWin.__contains__(playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Win')
                    awayLoss = tipWin.__contains__( playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Loss')
                    if row['player1_team_abbreviation'] == row['player3_team_abbreviation']:
                        if homeWin:
                            tipWin[playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Win'] += 1
                        else:
                            tipWin.__setitem__(playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Win', 1)
                            tipWin.__setitem__(playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Loss', 0)
                        if awayLoss:
                            tipWin[playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Loss'] += 1
                        else:
                            tipWin.__setitem__(playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Loss', 1)
                            tipWin.__setitem__(playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Win', 0)
                    else:
                        if homeLoss:
                            tipWin[playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Loss'] += 1
                        else:
                            tipWin.__setitem__(playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Loss', 1)
                            tipWin.__setitem__(playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Win', 0)
                        if awayWin:
                            tipWin[playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Win'] += 1
                        else:
                            tipWin.__setitem__(playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Win', 1)
                            tipWin.__setitem__(playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Loss', 0)
                    break

            for row in csvFile:
                if "1" == row['eventmsgtype']:
                    print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                    break

    i += 1
tipKeys = list(tipWin.keys())
tipKeys.sort()
tipWin = {i : tipWin[i] for i in tipKeys}
print(tipWin)

file = open('chart.txt', 'w')
file.write('Team\t|\t\t\tName\t\t\t\t|\tL\t|\tW\t|\tWin%\n')
lastKey = ''
for key in tipWin.keys():
    if(lastKey[0:len(lastKey)-4] == key[0:len(lastKey)-4]):
        file.write(str(tipWin[key]) + '\t|\t' + str(round(tipWin[key]/(tipWin[key]+tipWin[lastKey]), 3)) + '\n')
    elif(len(key[4:len(key)-4]) < 12):
        file.write(key[0:3] + '\t\t|\t' + key[4:len(key)-4] + '\t\t\t\t\t|\t' + str(tipWin[key]) + '\t|\t')
    elif(len(key[4:len(key)-4]) >= 16 and len(key[4:len(key)-4]) <= 19):
        file.write(key[0:3] + '\t\t|\t' + key[4:len(key)-4] + '\t\t\t|\t' + str(tipWin[key]) + '\t|\t')
    elif(len(key[4:len(key)-4]) >= 20):
        file.write(key[0:3] + '\t\t|\t' + key[4:len(key)-4] + '\t\t|\t' + str(tipWin[key]) + '\t|\t')
    else:
        file.write(key[0:3] + '\t\t|\t' + key[4:len(key)-4] + '\t\t\t\t|\t' + str(tipWin[key]) + '\t|\t')
    lastKey = key


