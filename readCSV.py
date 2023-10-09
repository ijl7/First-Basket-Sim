import csv
import math
#import scraper

i = 22200001
playerTeam = []
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
                    homeTeam = row['home_team_abbrev']
                    awayTeam = row['away_team_abbrev']
                    #add all players with their team
                    for player in homeLineup:
                        if playerTeam.__contains__(homeTeam + ' ' + player):
                            if playerStarts.__contains__(player):
                                playerStarts[player] += 1
                        else:
                            playerTeam.append(homeTeam + ' ' + player)
                            if playerStarts.__contains__(player):
                                playerStarts[player] += 1
                            else:
                                playerStarts.__setitem__(player, 1)
                                firstBaskets.__setitem__(player, 0)
                    for player in awayLineup:
                        if playerTeam.__contains__(awayTeam + ' ' + player):
                            if playerStarts.__contains__(player):
                                playerStarts[player] += 1
                        else:
                            playerTeam.append(awayTeam + ' ' + player)
                            if playerStarts.__contains__(player):
                                playerStarts[player] += 1
                            else:
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
                    player1Team = row['player1_team_abbreviation']
                    player1Name = row['player1_name']
                    player2Team = row['player2_team_abbreviation']
                    player2Name = row['player2_name']
                    homeWin = tipWin.__contains__(player1Team + ' ' + player1Name + ' Win')
                    homeLoss = tipWin.__contains__(player1Team + ' ' + player1Name + ' Loss')
                    awayWin = tipWin.__contains__(player2Team + ' ' + player2Name + ' Win')
                    awayLoss = tipWin.__contains__(player2Team + ' ' + player2Name + ' Loss')
                    #add all tip wins and losses for players
                    if row['player1_team_abbreviation'] == row['player3_team_abbreviation']:
                        if homeWin:
                            tipWin[player1Team + ' ' + player1Name + ' Win'] += 1
                        else:
                            tipWin.__setitem__(player1Team + ' ' + player1Name + ' Win', 1)
                            tipWin.__setitem__(player1Team + ' ' + player1Name + ' Loss', 0)
                        if awayLoss:
                            tipWin[player2Team + ' ' + player2Name + ' Loss'] += 1
                        else:
                            tipWin.__setitem__(player2Team + ' ' + player2Name + ' Loss', 1)
                            tipWin.__setitem__(player2Team + ' ' + player2Name + ' Win', 0)
                    else:
                        if homeLoss:
                            tipWin[player1Team + ' ' + player1Name + ' Loss'] += 1
                        else:
                            tipWin.__setitem__(player1Team + ' ' + player1Name + ' Loss', 1)
                            tipWin.__setitem__(player1Team + ' ' + player1Name + ' Win', 0)
                        if awayWin:
                            tipWin[player2Team + ' ' + player2Name + ' Win'] += 1
                        else:
                            tipWin.__setitem__(player2Team + ' ' + player2Name + ' Win', 1)
                            tipWin.__setitem__(player2Team + ' ' + player2Name + ' Loss', 0)
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

teamLineups = dict(sorted(teamLineups.items(), key=lambda x:x[1]))

playerTeam = sorted(playerTeam)

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
file.write('Team\t|\tPlayer\t\t\t\t\t\t|\tSt.\t|\tFB\t|\tFB%\n')
for pt in playerTeam:
    team = pt[0:3]
    player = pt[4:len(pt)]
    #weird tab formatting
    file.write(team +'\t\t|\t' + player)
    i = 7
    while i > math.trunc(len(player)/4):
        file.write('\t')
        i -= 1
    file.write('|\t' + str(playerStarts[player]) + '\t|\t' + str(firstBaskets[player]) + '\t|\t' + str(round(firstBaskets[player]/playerStarts[player], 3)) + '\n')
file.close()