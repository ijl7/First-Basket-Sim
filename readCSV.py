import csv
import math
import random
#import scraper

i = 22200001
playerTeam = []
tipWin = {}
teamLineups = {}
playerStarts = {}
firstBaskets = {}
playerShots = {}
tipData = []
fbResults= []
printedResults = {}
line1 = None
line2 = None
while i < 22201230:
    if i != 22200674 and i != 22200714:
        with open('2022\\' + str(i) + '.csv', mode='r') as file:
            csvFile = csv.DictReader(file)

            homeLineup = []
            awayLineup = []
            homeTuple = ()
            awayTuple = ()

            basketMade = True

            
            for row in csvFile:
                if '10' == row['eventmsgtype']:
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
                                playerShots.__setitem__(player, 0)
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
                                playerShots.__setitem__(player, 0)
                            
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
                    #print(row['player1_name'] + ' vs ' + row['player2_name'] + ', ' + row['player3_team_abbreviation'] + ' wins tip')
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
                if '1' == row['eventmsgtype']:
                    #print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                    playerShots[row['player1_name']] += 1
                    firstBaskets[row['player1_name']] += 1
                    basketMade = False
                    break
                elif '2' == row['eventmsgtype']:
                    playerShots[row['player1_name']] += 1

    i += 1

def sortDicts(tipWin, teamLineups, playerTeam):
    tipKeys = list(tipWin.keys())
    tipKeys.sort()
    tipWin = {i : tipWin[i] for i in tipKeys}

    teamLineups = dict(sorted(teamLineups.items(), key=lambda x:x[1]))

    playerTeam = sorted(playerTeam)
    return (tipWin, teamLineups, playerTeam)


def writeTipWinChart():
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

def writeLineupChart():
    file = open('lineupChart.txt', 'w')
    file.write('Team\t|\tLineup\n')
    for key in teamLineups.keys():
        file.write(teamLineups[key] + '\t\t|\t' + str(key) + '\n')
    file.close()

def writeFBChart():
    file = open('firstBasketChart.txt', 'w')
    file.write('Team\t|\tPlayer\t\t\t\t\t\t|\tSt.\t|\tShots\t|\tFB\t|\tFB%\n')
    for pt in playerTeam:
        team = pt[0:3]
        player = pt[4:len(pt)]
        #weird tab formatting
        file.write(team +'\t\t|\t' + player)
        i = 7
        while i > math.trunc(len(player)/4):
            file.write('\t')
            i -= 1
        if playerShots[player] != 0:
            file.write('|\t' + str(playerStarts[player]) + '\t|\t' + str(playerShots[player]) + '\t\t|\t' + str(firstBaskets[player]) + '\t|\t' + str(round(firstBaskets[player]/playerShots[player], 3)) + '\n')
        else:
            file.write('|\t' + str(playerStarts[player]) + '\t|\t' + str(playerShots[player]) + '\t\t|\t' + str(firstBaskets[player]) + '\t|\t' + str(0) + '\n')
    file.close()

def predictTipWin():
    p1Percent = 0.0
    p2Percent = 0.0
    lastKey = ''
    for key in tipWin.keys():
        playerName = key[4:len(key)-4]
        #if player win hasnt been recorded yet
        if lastKey[0:len(lastKey)-4] == key[0:len(lastKey)-4]:
            if p1 == playerName:
                p1Percent = round(tipWin[key]/(tipWin[key]+tipWin[lastKey]), 8)
            if p2 == playerName:
                p2Percent = round(tipWin[key]/(tipWin[key]+tipWin[lastKey]), 8)
        lastKey = key
    
    winner = 0
    
    p1Tip = p1Percent*(1-p2Percent)
    p2Tip = p2Percent*(1-p1Percent)

    p1TipNormal = p1Tip/(p1Tip+p2Tip)
    
    for i in range(1000000):
        if i <= round(p1TipNormal*1000000):
            winner = 1
        else:
            winner = 2
        tipData.append({'Player': winner})
    p1Count = 0
    p2Count = 0
    for sim in tipData:
        if sim['Player'] == 1:
            p1Count += 1
        else:
            p2Count += 1
    '''print(p1 + ' won the tip ' + str(p1Count) + ' times.')
    print(p2 + ' won the tip ' + str(p2Count) + ' times.')
    print('This gives ' + p1 + ' a ' + str(p1Count/10000) + '% chance to win the tip.')
    print('This gives ' + p2 + ' a ' + str(p2Count/10000) + '% chance to win the tip.')'''
    
def getLineups():
    lines1 = []
    lines2 = []
    for player in playerTeam:
        if player[4:len(player)] == p1:
            t1 = player[0:3]
        elif player[4:len(player)] == p2:
            t2 = player[0:3]
    for key in teamLineups.keys():
        if teamLineups[key] == t1:
            lines1.append(key)
        elif teamLineups[key] == t2:
            lines2.append(key)
    return (lines1, lines2)
t1Chance = []
t2Chance = []
def getShooter():
    randInt = random.randint(0,999999)
    ballFirst = tipData[randInt]['Player']
    result = ' Miss'
    while result[len(result)-4:len(result)] != 'Make':
        if ballFirst == 1:
            #print(str(t1) + ' ball')
            result = t1Chance[random.randint(0,len(t1Chance)-1)]
        else:
            #print(str(t2) + ' ball')
            result = t2Chance[random.randint(0,len(t2Chance)-1)]
        if ballFirst == 1:
            ballFirst = 2
        else:
            ballFirst = 1
        #print(str(result))
    fbResults.append(result[0:len(result)-5])

(tipWin, teamLineups, playerTeam) = sortDicts(tipWin, teamLineups, playerTeam)
writeTipWinChart()
writeLineupChart()
writeFBChart()
p1 = input('Who is jumping for the ball?\n')
p2 = input()
predictTipWin()
(lines1, lines2) = getLineups()
i = 1
for lineup in lines1:
    print(str(i) + '. ' + str(lineup))
    i += 1
i = 1
for lineup in lines2:
    print(str(i) + '. ' + str(lineup))
    i += 1
lineNum1 = input('Which lineups are starting?\n')
lineNum2 = input()
line1 = lines1[int(lineNum1)-1]
line2 = lines2[int(lineNum2)-1]
for player in line1:
    for j in range(firstBaskets[player]):
        t1Chance.append(player + ' Make')
    for j in range(playerShots[player]-firstBaskets[player]):
        t1Chance.append(player + ' Miss')
for player in line2:
    for j in range(firstBaskets[player]):
        t2Chance.append(player + ' Make')
    for j in range(playerShots[player]-firstBaskets[player]):
        t2Chance.append(player + ' Miss')

for i in range(100000):
    getShooter()
fbResults = sorted(fbResults)
for player in fbResults:
    if printedResults.__contains__(player):
        printedResults[player] += 1
    else:
        printedResults.__setitem__(player, 1)
printedResults = dict(sorted(printedResults.items(), key=lambda x:x[1], reverse=True))
for result in printedResults.keys():
    print(result + ':\t' + str(round(printedResults[result]/1000, 3)) + '% chance:\t+' + str(round(((1/(printedResults[result]/100000))-1)*100)) + ' odds')
