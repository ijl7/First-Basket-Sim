import csv
import math
import random
import replace_accents as replaceaccents
#import scraper


playerTeam = []
tipWin = {}
teamLineups = {}
playerStarts = {}
firstBaskets = {}
playerShots = {}
tipData = []
fbResults= []
printedResults = {}
line1 = []
line2 = []
def get2021():
    i = 22100001
    while i < 22101231:
        if i != 22100717 and i != 22100773 and i != 22101171:
            with open('2021\\' + str(i) + '.csv', mode='r') as file:
                csvFile = csv.DictReader(file)

                homeLineup = []
                awayLineup = []

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
                                #playerTeam.append(homeTeam + ' ' + player)
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
                                #playerTeam.append(awayTeam + ' ' + player)
                                if playerStarts.__contains__(player):
                                    playerStarts[player] += 1
                                else:
                                    playerStarts.__setitem__(player, 1)
                                    firstBaskets.__setitem__(player, 0)
                                    playerShots.__setitem__(player, 0)
                              
                        player1Name = row['player1_name']
                        player2Name = row['player2_name']
                        homeWin = tipWin.__contains__(player1Name + ' Win')
                        homeLoss = tipWin.__contains__(player1Name + ' Loss')
                        awayWin = tipWin.__contains__(player2Name + ' Win')
                        awayLoss = tipWin.__contains__(player2Name + ' Loss')
                        #add all tip wins and losses for players
                        if row['player1_team_abbreviation'] == row['player3_team_abbreviation']:
                            if homeWin:
                                tipWin[player1Name + ' Win'] += 1
                            else:
                                tipWin.__setitem__(player1Name + ' Win', 1)
                                tipWin.__setitem__(player1Name + ' Loss', 0)
                            if awayLoss:
                                tipWin[player2Name + ' Loss'] += 1
                            else:
                                tipWin.__setitem__(player2Name + ' Loss', 1)
                                tipWin.__setitem__(player2Name + ' Win', 0)
                        else:
                            if homeLoss:
                                tipWin[player1Name + ' Loss'] += 1
                            else:
                                tipWin.__setitem__(player1Name + ' Loss', 1)
                                tipWin.__setitem__(player1Name + ' Win', 0)
                            if awayWin:
                                tipWin[player2Name + ' Win'] += 1
                            else:
                                tipWin.__setitem__(player2Name + ' Win', 1)
                                tipWin.__setitem__(player2Name + ' Loss', 0)
                        break

                for row in csvFile:
                    if '1' == row['eventmsgtype']:
                        #print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                        playerShots[row['player1_name']] += 1
                        firstBaskets[row['player1_name']] += 1
                        break
                    elif '2' == row['eventmsgtype']:
                        playerShots[row['player1_name']] += 1

        i += 1
def get2022():
    i = 22200001
    while i < 22201231:
        if i != 22200674 and i != 22200714:
            with open('2022\\' + str(i) + '.csv', mode='r') as file:
                csvFile = csv.DictReader(file)

                homeLineup = []
                awayLineup = []

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
                                #playerTeam.append(homeTeam + ' ' + player)
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
                                #playerTeam.append(awayTeam + ' ' + player)
                                if playerStarts.__contains__(player):
                                    playerStarts[player] += 1
                                else:
                                    playerStarts.__setitem__(player, 1)
                                    firstBaskets.__setitem__(player, 0)
                                    playerShots.__setitem__(player, 0)
                                
                        player1Name = row['player1_name']
                        player2Name = row['player2_name']
                        homeWin = tipWin.__contains__(player1Name + ' Win')
                        homeLoss = tipWin.__contains__(player1Name + ' Loss')
                        awayWin = tipWin.__contains__(player2Name + ' Win')
                        awayLoss = tipWin.__contains__(player2Name + ' Loss')
                        #add all tip wins and losses for players
                        if row['player1_team_abbreviation'] == row['player3_team_abbreviation']:
                            if homeWin:
                                tipWin[player1Name + ' Win'] += 1
                            else:
                                tipWin.__setitem__(player1Name + ' Win', 1)
                                tipWin.__setitem__(player1Name + ' Loss', 0)
                            if awayLoss:
                                tipWin[player2Name + ' Loss'] += 1
                            else:
                                tipWin.__setitem__(player2Name + ' Loss', 1)
                                tipWin.__setitem__(player2Name + ' Win', 0)
                        else:
                            if homeLoss:
                                tipWin[player1Name + ' Loss'] += 1
                            else:
                                tipWin.__setitem__(player1Name + ' Loss', 1)
                                tipWin.__setitem__(player1Name + ' Win', 0)
                            if awayWin:
                                tipWin[player2Name + ' Win'] += 1
                            else:
                                tipWin.__setitem__(player2Name + ' Win', 1)
                                tipWin.__setitem__(player2Name + ' Loss', 0)
                        break

                for row in csvFile:
                    if '1' == row['eventmsgtype']:
                        #print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                        playerShots[row['player1_name']] += 1
                        firstBaskets[row['player1_name']] += 1
                        break
                    elif '2' == row['eventmsgtype']:
                        playerShots[row['player1_name']] += 1

        i += 1
def get2023():
    i = 22300001
    while i < 22301231:
        if i != 22300425 and i != 22300576 and i != 22300589 and i != 22301130:
            with open('2023\\' + str(i) + '.csv', mode='r') as file:
                csvFile = csv.DictReader(file)

                homeLineup = []
                awayLineup = []

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
                              
                        player1Name = row['player1_name']
                        player2Name = row['player2_name']
                        homeWin = tipWin.__contains__(player1Name + ' Win')
                        homeLoss = tipWin.__contains__(player1Name + ' Loss')
                        awayWin = tipWin.__contains__(player2Name + ' Win')
                        awayLoss = tipWin.__contains__(player2Name + ' Loss')
                        #add all tip wins and losses for players
                        if row['player1_team_abbreviation'] == row['player3_team_abbreviation']:
                            if homeWin:
                                tipWin[player1Name + ' Win'] += 1
                            else:
                                tipWin.__setitem__(player1Name + ' Win', 1)
                                tipWin.__setitem__(player1Name + ' Loss', 0)
                            if awayLoss:
                                tipWin[player2Name + ' Loss'] += 1
                            else:
                                tipWin.__setitem__(player2Name + ' Loss', 1)
                                tipWin.__setitem__(player2Name + ' Win', 0)
                        else:
                            if homeLoss:
                                tipWin[player1Name + ' Loss'] += 1
                            else:
                                tipWin.__setitem__(player1Name + ' Loss', 1)
                                tipWin.__setitem__(player1Name + ' Win', 0)
                            if awayWin:
                                tipWin[player2Name + ' Win'] += 1
                            else:
                                tipWin.__setitem__(player2Name + ' Win', 1)
                                tipWin.__setitem__(player2Name + ' Loss', 0)
                        break

                for row in csvFile:
                    if '1' == row['eventmsgtype']:
                        #print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                        playerShots[row['player1_name']] += 1
                        firstBaskets[row['player1_name']] += 1
                        break
                    elif '2' == row['eventmsgtype']:
                        playerShots[row['player1_name']] += 1
        if i != 22301100:
            i += 1
        else:
            i = 22301201
def get2024():
    i = 22400001
    while i < 22401231:
        if i != 22400495:
            with open('2024\\' + str(i) + '.csv', mode='r', encoding='utf-8') as file:
                csvFile = csv.DictReader(file)

                homeLineup = []
                awayLineup = []
                homeTuple = ()
                awayTuple = ()
                for row in csvFile:
                    if '10' == row['eventmsgtype']:
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_1']))
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_2']))
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_3']))
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_4']))
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_5']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_1']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_2']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_3']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_4']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_5']))
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
                        awayTuple = tuple(awayLineup)
                        if teamLineups.__contains__(homeTuple):
                            None
                        else:
                            teamLineups.__setitem__(homeTuple, row['home_team_abbrev'])
                        if teamLineups.__contains__(awayTuple):
                            None
                        else:
                            teamLineups.__setitem__(awayTuple, row['away_team_abbrev'])
                        #print(row['player1_name'] + ' vs ' + row['player2_name'] + ', ' + row['player3_team_abbreviation'] + ' wins tip')
                        player1Name = replaceaccents.replace_accents_characters(row['player1_name'])
                        player2Name = replaceaccents.replace_accents_characters(row['player2_name'])
                        homeWin = tipWin.__contains__(player1Name + ' Win')
                        homeLoss = tipWin.__contains__(player1Name + ' Loss')
                        awayWin = tipWin.__contains__(player2Name + ' Win')
                        awayLoss = tipWin.__contains__(player2Name + ' Loss')
                        #add all tip wins and losses for players
                        if row['player1_team_abbreviation'] == row['player3_team_abbreviation']:
                            if homeWin:
                                tipWin[player1Name + ' Win'] += 1
                            else:
                                tipWin.__setitem__(player1Name + ' Win', 1)
                                tipWin.__setitem__(player1Name + ' Loss', 0)
                            if awayLoss:
                                tipWin[player2Name + ' Loss'] += 1
                            else:
                                tipWin.__setitem__(player2Name + ' Loss', 1)
                                tipWin.__setitem__(player2Name + ' Win', 0)
                        else:
                            if homeLoss:
                                tipWin[player1Name + ' Loss'] += 1
                            else:
                                tipWin.__setitem__(player1Name + ' Loss', 1)
                                tipWin.__setitem__(player1Name + ' Win', 0)
                            if awayWin:
                                tipWin[player2Name + ' Win'] += 1
                            else:
                                tipWin.__setitem__(player2Name + ' Win', 1)
                                tipWin.__setitem__(player2Name + ' Loss', 0)
                        break

                for row in csvFile:
                    player = replaceaccents.replace_accents_characters(row['player1_name'])
                    if '1' == row['eventmsgtype']:
                        #print(row['away_team_abbrev'] + " @ " + row['home_team_abbrev'] + ", " + row['player1_name'])
                        if playerShots.__contains__(player):
                            playerShots[player] += 1
                        else:
                            playerShots.__setitem__(player, 0)
                        if firstBaskets.__contains__(player):
                            firstBaskets[player] += 1
                        else:
                            firstBaskets.__setitem__(player, 0)
                        break
                    elif '2' == row['eventmsgtype']:
                        if playerShots.__contains__(player):
                            playerShots[player] += 1
                        else:
                            playerShots.__setitem__(player, 0)
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
    file.write('Name\t\t\t\t\t|\tL\t|\tW\t|\tWin%\n')
    lastPlayer = ''
    for player in tipWin.keys():
        #if player win hasnt been recorded yet
        if lastPlayer[0:len(lastPlayer)-4] == player[0:len(lastPlayer)-4]:
            file.write(str(tipWin[player]) + '\t|\t' + str(round(tipWin[player]/(tipWin[player]+tipWin[lastPlayer]), 3)) + '\n')
        else:
        #weird tab formatting
            playerName = player[0:len(player)-4]
            i = 6
            file.write(playerName)
            while i > math.trunc(len(playerName)/4):
                file.write('\t')
                i -= 1
            file.write('|\t' + str(tipWin[player]) + '\t|\t')
        lastPlayer = player
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
        playerName = key[0:len(key)-4]
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
    
    print('This gives ' + p1 + ' a ' + str(round(p1TipNormal*100, 3)) + '% chance to win the tip.')
    print('This gives ' + p2 + ' a ' + str(round((1-p1TipNormal)*100, 3)) + '% chance to win the tip.')
    
def retrieveLineups():
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
def getLineupChoice(line1, line2):
    lineNum1 = input('Which lineups are starting? (Put in 0 to enter your own lineups)\n')
    lineNum2 = input()
    if lineNum1 != '0':
        line1 = lines1[int(lineNum1)-1]
    else:
        i = 1
        while i <= 5:
            player = input('Enter Player ' + str(i) + ':\n')
            line1.append(player)
            i += 1
    if lineNum2 != '0':
        line2 = lines2[int(lineNum2)-1]
    else:
        i = 1
        while i <= 5:
            player = input('Enter Player ' + str(i) + ':\n')
            line2.append(player)
            i += 1
    return (line1, line2)

def getFirstBasket():
    t1Chance = []
    t2Chance = []
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
    return (t1Chance, t2Chance)

def getAllBaskets():
    t1Chance = []
    t2Chance = []
    i = 22400001
    useGame = True
    while i < 22401231:
        if i != 22400495 and useGame:
            with open('2024\\' + str(i) + '.csv', mode='r', encoding='utf-8') as file:
                csvFile = csv.DictReader(file)
                for row in csvFile:
                    useLine = True
                    homeLineup = []
                    awayLineup = []
                    homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_1']))
                    homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_2']))
                    homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_3']))
                    homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_4']))
                    homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_5']))
                    awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_1']))
                    awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_2']))
                    awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_3']))
                    awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_4']))
                    awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_5']))
                    j = 0
                    while j < 5:
                        #check all players in the home and away lineup for line1
                        if homeLineup.__contains__(line1[j]):
                            None
                        elif awayLineup.__contains__(line1[j]):
                            None
                        else:
                            useLine = False
                        j += 1
                    if useLine:
                        #only add if the player you want is shooting
                        if line1.__contains__(replaceaccents.replace_accents_characters(row['player1_name'])):
                            if row['eventmsgtype'] == '2':
                                t1Chance.append(replaceaccents.replace_accents_characters(row['player1_name']) + ' Miss')
                            elif row['eventmsgtype'] == '1':
                                t1Chance.append(replaceaccents.replace_accents_characters(row['player1_name']) + ' Make')
                    useLine = True
                    j = 0
                    while j < 5:
                        #check all players in the home and away lineup for line2
                        if homeLineup.__contains__(line2[j]):
                            None
                        elif awayLineup.__contains__(line2[j]):
                            None
                        else:
                            useLine = False
                        j += 1
                    if useLine:
                        #only add if the player you want is shooting
                        if line2.__contains__(replaceaccents.replace_accents_characters(row['player1_name'])):
                            if row['eventmsgtype'] == '2':
                                t2Chance.append(replaceaccents.replace_accents_characters(row['player1_name']) + ' Miss')
                            elif row['eventmsgtype'] == '1':
                                t2Chance.append(replaceaccents.replace_accents_characters(row['player1_name']) + ' Make')
        i += 1
    if int(years) < 4:
        i = 22300001
        useGame = True
        while i < 22301231:
            if i != 22300425 and i != 22300576  and i != 22300589 and i != 22301130 and useGame:
                with open('2023\\' + str(i) + '.csv', mode='r', encoding='utf-8') as file:
                    csvFile = csv.DictReader(file)
                    for row in csvFile:
                        useLine = True
                        homeLineup = []
                        awayLineup = []
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_1']))
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_2']))
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_3']))
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_4']))
                        homeLineup.append(replaceaccents.replace_accents_characters(row['home_player_5']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_1']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_2']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_3']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_4']))
                        awayLineup.append(replaceaccents.replace_accents_characters(row['away_player_5']))
                        j = 0
                        while j < 5:
                            #check all players in the home and away lineup for line1
                            if homeLineup.__contains__(line1[j]):
                                None
                            elif awayLineup.__contains__(line1[j]):
                                None
                            else:
                                useLine = False
                            j += 1
                        if useLine:
                            #only add if the player you want is shooting
                            if line1.__contains__(row['player1_name']):
                                if row['eventmsgtype'] == '2':
                                    t1Chance.append(row['player1_name'] + ' Miss')
                                elif row['eventmsgtype'] == '1':
                                    t1Chance.append(row['player1_name'] + ' Make')
                        useLine = True
                        j = 0
                        while j < 5:
                            #check all players in the home and away lineup for line2
                            if homeLineup.__contains__(line2[j]):
                                None
                            elif awayLineup.__contains__(line2[j]):
                                None
                            else:
                                useLine = False
                            j += 1
                        if useLine:
                            #only add if the player you want is shooting
                            if line2.__contains__(row['player1_name']):
                                if row['eventmsgtype'] == '2':
                                    t2Chance.append(row['player1_name'] + ' Miss')
                                elif row['eventmsgtype'] == '1':
                                    t2Chance.append(row['player1_name'] + ' Make')
            i += 1
    if int(years) < 3:
        i = 22200001
        useGame = True
        while i < 22201231:
            if i != 22200674 and i != 22200714 and useGame:
                with open('2022\\' + str(i) + '.csv', mode='r') as file:
                    csvFile = csv.DictReader(file)
                    for row in csvFile:
                        useLine = True
                        homeLineup = []
                        awayLineup = []
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
                        j = 0
                        while j < 5:
                            #check all players in the home and away lineup for line1
                            if homeLineup.__contains__(line1[j]):
                                None
                            elif awayLineup.__contains__(line1[j]):
                                None
                            else:
                                useLine = False
                            j += 1
                        if useLine:
                            #only add if the player you want is shooting
                            if line1.__contains__(row['player1_name']):
                                if row['eventmsgtype'] == '2':
                                    t1Chance.append(row['player1_name'] + ' Miss')
                                elif row['eventmsgtype'] == '1':
                                    t1Chance.append(row['player1_name'] + ' Make')
                        useLine = True
                        j = 0
                        while j < 5:
                            #check all players in the home and away lineup for line2
                            if homeLineup.__contains__(line2[j]):
                                None
                            elif awayLineup.__contains__(line2[j]):
                                None
                            else:
                                useLine = False
                            j += 1
                        if useLine:
                            #only add if the player you want is shooting
                            if line2.__contains__(row['player1_name']):
                                if row['eventmsgtype'] == '2':
                                    t2Chance.append(row['player1_name'] + ' Miss')
                                elif row['eventmsgtype'] == '1':
                                    t2Chance.append(row['player1_name'] + ' Make')
            i += 1         
    if int(years) < 2:
        i = 22100001
        useGame = True
        while i < 22101231:
            if i != 22100717 and i != 22100773 and i != 22101171 and useGame:
                with open('2021\\' + str(i) + '.csv', mode='r') as file:
                    csvFile = csv.DictReader(file)
                    for row in csvFile:
                        useLine = True
                        homeLineup = []
                        awayLineup = []
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
                        j = 0
                        while j < 5:
                            #check all players in the home and away lineup for line1
                            if homeLineup.__contains__(line1[j]):
                                None
                            elif awayLineup.__contains__(line1[j]):
                                None
                            else:
                                useLine = False
                            j += 1
                        if useLine:
                            #only add if the player you want is shooting
                            if line1.__contains__(row['player1_name']):
                                if row['eventmsgtype'] == '2':
                                    t1Chance.append(row['player1_name'] + ' Miss')
                                elif row['eventmsgtype'] == '1':
                                    t1Chance.append(row['player1_name'] + ' Make')
                        useLine = True
                        j = 0
                        while j < 5:
                            #check all players in the home and away lineup for line2
                            if homeLineup.__contains__(line2[j]):
                                None
                            elif awayLineup.__contains__(line2[j]):
                                None
                            else:
                                useLine = False
                            j += 1
                        if useLine:
                            #only add if the player you want is shooting
                            if line2.__contains__(row['player1_name']):
                                if row['eventmsgtype'] == '2':
                                    t2Chance.append(row['player1_name'] + ' Miss')
                                elif row['eventmsgtype'] == '1':
                                    t2Chance.append(row['player1_name'] + ' Make')
            i += 1
    return (t1Chance, t2Chance)

def getTeamBaskets():
    t1FB = {}
    t2FB = {}
    for basket in t1Chance:
        if basket[len(basket)-4:len(basket)] == 'Make':
            playerName = basket[0:len(basket)-5]
            if t1FB.__contains__(playerName):
                t1FB[playerName] += 1
            else:
                t1FB.__setitem__(playerName, 1)
    for basket in t2Chance:
        if basket[len(basket)-4:len(basket)] == 'Make':
            playerName = basket[0:len(basket)-5]
            if t2FB.__contains__(playerName):
                t2FB[playerName] += 1
            else:
                t2FB.__setitem__(playerName, 1)
    t1Total = 0
    t2Total = 0
    for player in t1FB:
        t1Total += t1FB[player]
    for player in t2FB:
        t2Total += t2FB[player]
    t1FB = dict(sorted(t1FB.items(), key=lambda x:x[1], reverse=True))
    t2FB = dict(sorted(t2FB.items(), key=lambda x:x[1], reverse=True))
    return (t1FB, t2FB, t1Total, t2Total)
        
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
years = input('What years would you like? (1 for 2021 onwards, 2 for 2022 onwards, 3 for 2023 onwards, or 4 for 2024 onwards)\n')
get2024()
if int(years) < 4:
    get2023()
if int(years) < 3:
    get2022()
if int(years) < 2:
    get2021()
(tipWin, teamLineups, playerTeam) = sortDicts(tipWin, teamLineups, playerTeam)
writeTipWinChart()
writeLineupChart()
writeFBChart()
p1 = input('Who is jumping for the ball?\n')
p2 = input()
predictTipWin()
(lines1, lines2) = retrieveLineups()
i = 1
for lineup in lines1:
    print(str(i) + '. ' + str(lineup))
    i += 1
i = 1
for lineup in lines2:
    print(str(i) + '. ' + str(lineup))
    i += 1
(line1, line2) = getLineupChoice(line1, line2)
mode = input('Would you like first basket data (1), or all plays (2)?\n')
if int(mode) == 1:
    (t1Chance, t2Chance) = getFirstBasket()
else:
    (t1Chance,t2Chance) = getAllBaskets()
print(t1Chance)
print(t2Chance)
(t1FB, t2FB, t1Total, t2Total) = getTeamBaskets()
print('------- Team 1 -------')
for result in t1FB.keys():
    print(result + ':\t' + str(round((t1FB[result]/t1Total)*100, 3)) + '% chance:\t+' + str(round(((1/(t1FB[result]/(t1Total)))-1)*100)) + ' odds')
print('------- Team 2 -------')
for result in t2FB.keys():
    print(result + ':\t' + str(round((t2FB[result]/t2Total)*100, 3)) + '% chance:\t+' + str(round(((1/(t2FB[result]/(t2Total)))-1)*100)) + ' odds')
print('\n')
for i in range(10000000):
    getShooter()
fbResults = sorted(fbResults)
for player in fbResults:
    if printedResults.__contains__(player):
        printedResults[player] += 1
    else:
        printedResults.__setitem__(player, 1)
#sort results by highest percent chance to score
printedResults = dict(sorted(printedResults.items(), key=lambda x:x[1], reverse=True))
for result in printedResults.keys():
    print(result + ':\t' + str(round(printedResults[result]/100000, 3)) + '% chance:\t+' + str(round(((1/(printedResults[result]/10000000))-1)*100)) + ' odds')


