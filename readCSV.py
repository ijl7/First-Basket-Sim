import csv
import math
#import scraper

i = 22200001
playerTeam = {}
tipWin = {}
teamLineups = {}
playerStarts = {}
firstBaskets = {}
while i < 22201230:
    if i != 22200674 and i != 22200714:
        with open('2022\\' + str(i) + '.csv', mode='r') as file:
            csvFile = csv.DictReader(file)

            homeLineup = []
            awayLineup = []
            homeTuple = ()
            awayTuple = ()

            
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
                    #add all players with their team
                    for player in homeLineup:
                        if playerTeam.__contains__(player):
                            playerStarts[player] += 1
                        else:
                            playerTeam.__setitem__(player, row['home_team_abbrev'])
                            playerStarts.__setitem__(player, 1)
                            firstBaskets.__setitem__(player, 0)
                    for player in awayLineup:
                        if playerTeam.__contains__(player):
                            playerStarts[player] += 1
                        else:
                            playerTeam.__setitem__(player, row['away_team_abbrev'])
                            playerStarts.__setitem__(player, 1)
                            firstBaskets.__setitem__(player, 0)
                    #add all team lineups
                    homeTuple = tuple(homeLineup)
                    if teamLineups.__contains__(homeTuple):
                        None
                    else:
                        teamLineups.__setitem__(homeTuple, row['home_team_abbrev'])
                    if teamLineups.__contains__(awayTuple):
                        None
                    else:
                        teamLineups.__setitem__(awayTuple, row['away_team_abbrev'])
                    print(row['player1_name'] + ' vs ' + row['player2_name'] + ', ' + row['player3_team_abbreviation'] + ' wins tip')
                    homeWin = tipWin.__contains__(playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Win')
                    homeLoss = tipWin.__contains__(playerTeam[row['player1_name']] + ' ' + row['player1_name'] + ' Loss')
                    awayWin = tipWin.__contains__(playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Win')
                    awayLoss = tipWin.__contains__( playerTeam[row['player2_name']] + ' ' + row['player2_name'] + ' Loss')
                    #add all tip wins and losses for players
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
                    firstBaskets[row['player1_name']] += 1
                    break
                    

    i += 1


tipKeys = list(tipWin.keys())
tipKeys.sort()
tipWin = {i : tipWin[i] for i in tipKeys}
print(tipWin)
teamLineups = dict(sorted(teamLineups.items(), key=lambda x:x[1]))
print(teamLineups)

file = open('tipWinChart.txt', 'w')
file.write('Team\t|\t\t\tName\t\t\t|\tL\t|\tW\t|\tWin%\n')
lastKey = ''
for key in tipWin.keys():
    #if player win hasnt been recorded yet
    if lastKey[0:len(lastKey)-4] == key[0:len(lastKey)-4]:
        file.write(str(tipWin[key]) + '\t|\t' + str(round(tipWin[key]/(tipWin[key]+tipWin[lastKey]), 3)) + '\n')
    else:
    #weird tab formatting
        playerName = key[4:len(key)-4]
        i = 6
        file.write(key[0:3] + '\t\t|\t' + playerName)
        while i > math.trunc(len(playerName)/4):
            file.write('\t')
            i -= 1
        file.write('|\t' + str(tipWin[key]) + '\t|\t')
    lastKey = key
file.close()

file = open('lineupChart.txt', 'w')
file.write('Team\t|\tLineup\n')
for key in teamLineups.keys():
    file.write(teamLineups[key] + '\t\t|\t' + str(key) + '\n')
file.close()

file = open('firstBasketChart.txt', 'w')
file.write('Player\t\t\t\t\t\t|\tSt.\t|\tFirst Baskets\n')
for player in playerStarts:
    #weird tab formatting
    file.write(player)
    i = 7
    while i > math.trunc(len(player)/4):
        file.write('\t')
        i -= 1
    file.write('|\t' + str(playerStarts[player]) + '\t|\t' + str(firstBaskets[player]) + '\n')
file.close()