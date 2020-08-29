from . import Prediction, Ratings, Train, Injury, Season, Game, Plays
from bs4 import Comment
from . import nflPredict as Base
import os

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

def divisionWinners(teamData):
    ###Find division winners (not sorted by chance)
    afcTeams, nfcTeams = [], []
    for i in Base.DIVISIONS:
        dataSet = [teamData[j] for j in i]
        ###Take the winner. 
        winner = max(dataSet, key=lambda x:x[1][-1])
        if(winner[0] in Base.AFC):
            afcTeams.append(winner)
        else:
            nfcTeams.append(winner)
            
    return afcTeams, nfcTeams

def findData(weekGames):
    """Finds injury data to add to the data file"""
    inputData = []
    for i in weekGames:
        print(".", end='')
        url = "https://www.pro-football-reference.com" + i[2]
        soup = Base.openWebsite(url)
        ###Get the injuries
        awayAbbr, homeAbbr = Base.TEAM_ABBRS[i[0]], Base.TEAM_ABBRS[i[1]]
        diffScore = getSevereScore(soup, awayAbbr, homeAbbr)
        
        rateDiff = Base.TEAM_RATINGS[i[0]] - Base.TEAM_RATINGS[i[1]]
        seasDiff = Base.SEASON_RATINGS[i[0]] - Base.SEASON_RATINGS[i[1]]
        ###Add to input list
        line = [rateDiff, seasDiff]; line.extend(diffScore)
        inputData.append(line)

    return predict(inputData)

def findSevereScores(injs):
    score = [0 for i in range(12)]
    for i in injs:
        newPos = i[0]
        ###Convert position to what's in RATING_AND_INJURY, get number for the injury
        if(newPos in Base.POS_CONVERT): newPos = Base.POS_CONVERT[newPos]
        thisScore = severeScore[i[2].lower()]

        if(newPos in Base.POS_ORDER):
            score[Base.POS_ORDER.index(newPos)] += thisScore
            
        if(not(newPos in POS_ORDER) and newPos.lower() != 'k' and newPos.lower() != 'p'):
            print(newPos, 'getSevere')

    return score

def getSevere(injuries, teamName):
    """Finds a special injury score for a team, based on the players chance of play (out, probable ...)"""
    print("2019 --- It uses 2019")
    ###Find the comment, split it into tags
    findComment = lambda text:isinstance(text, Comment)
    comm = str(injuries.find(string=findComment)).split("\n")
    comm = [i.split("<") for i in comm if "tr" in i and "th" in i]

    ###Split the comment into injured people
    injuryList = []
    for i in comm:
        inj = [j[j.index(">")+1:] for j in i if "href" in j or "pos" in j or "injury_class" in j]
        injuryList.append(inj)

    ###Format the list, remove backups
    injuryList = [[i[1], i[0], i[2]] for i in injuryList]
    injs = Injury.getStarters(injuryList, teamName, 2019)
    
    return findSevereScores(injs)

def getSevereScore(soup, awayAbbr, homeAbbr):
    awayInj = soup.find("div", attrs={"id":"all_{}_current_injuries".format(awayAbbr)})
    homeInj = soup.find("div", attrs={"id":"all_{}_current_injuries".format(homeAbbr)})
    ###Get the actual number and the difference to put in RATING_AND_INJURY
    awayScore, homeScore = getSevere(awayInj, i[0]), getSevere(homeInj, i[1])
    diffScore = Injury.subtract(awayScore, homeScore)

    return diffScore

def getWeek(year, week):
    ###Step 1: Load week data
    print("Loading Weeks. Check if Ranking Change is correct")
    lastWeek = trainer.getWeek(year, week)
    if(weekNum < 17):
        nextWeek = trainer.getWeek(year, week+1, True)
    else:
        print("Predict the Playoffs Separately")
        if(weekNum == 17): nextWeek = trainer.getWeek(year, 30, True)
        else: nextWeek = trainer.getWeek(year, week+1, True)

    return nextWeek


def playoffPicture(teamChances):
    """Returns 12 teams in the playoffs, first 6 are AFC, next 6 are NFC
teamChances is a list where each element is: [name, [all chances in a list]]"""
    teamData = {}
    ###Dictionary to access team chances by name
    for i in teamChances:
        name = i[0]
        teamData[name] = i

    afcTeams, nfcTeams = divisionWinners(teamData)
    afcTeams, nfcTeams = wildcards(afcTeams, nfcTeams)
    
    afcTeams = [i[0]+','+str(i[1][2])+','+str(i[1][3]) for i in afcTeams]
    nfcTeams = [i[0]+','+str(i[1][2])+','+str(i[1][3]) for i in nfcTeams]
    string = '\n'.join(afcTeams) + '\n' + '\n'.join(nfcTeams)
    return string

def predict(inputData):
    """Returns a list of predictions. inputData is a list of lists to put in RATING_AND_INJURY"""
    probs = list(Base.RATING_AND_INJURY.predict(inputData))
    probs = [round(i*100, 1) for i in probs]
    for i in range(len(probs)):
        if(probs < 50):
            probs[i] = weekGames[i][1] + ', ' + str(probs[i]) + '%'
        else:
            probs[i] = weekGames[i][0] + ', ' + str(probs[i]) + '%'

    return probs
    
def outputPreds(preds):
    """Outputs next weeks predictions, sorted by chance, least to most"""
    preds = [i.split(", ") for i in preds]
    preds = [[i[0], float(i[1][:-1])] for i in preds]
    preds = sorted(preds, key=lambda x:x[1])
    for i in preds:
        print(i[0], i[1])

def regUpdate(prevWins, lastWeek, weekNum, year):
    prevWins = updateWins(prevWins, lastWeek)
    print(prevWins)
    ###Step 8: Season Predictions
    print("Doing Season Predictions")
    print("-----")
    chances = seasonPreds(prevWins, weekNum, year)
    chances = [[i[0], i[1:]] for i in chances]
    print("-----")

    ###Step 9: Find the projected playoff picture
    picture = playoffPicture(chances)
    print(picture)
    print("-----")

    ###10: One sim of the playoffs
    simPreds(prevWins, weekNum)

    print("-----")
    print("Do Results")

def seasonPreds(prevWins, week, year):
    ###Create Season object
    seas = Season(week, year, TEAM_RATINGS, SEASON_RATINGS, records=prevWins)
    ###Predict and get data
    seas.predictSeason()
    ###Turn into list, and print something that can be pasted into file
    chances = seas.getData()
    outChances = [list(map(str, i)) for i in chances]
    outChances = [','.join(i) for i in outChances]
    outChances = '\n'.join(outChances)
    print(outChances)
    ###Return chances for playoff picture
    return chances

def simPreds(prevWins, week):
    ###Create object
    seas = Season(week, records=prevWins, searchFor={"sim":500})
    sched = seas.findSpecial()
    data = seas.getSimData(sched)

    data = [list(map(str, i)) for i in data]
    data = [','.join(i) for i in data]
    data = '\n'.join(data)
    print(data)       

def update(weekNum, year, prevWins):
    """Updates Team Ratings, Playoff Predictions, etc.
Week Num is the last week played
prevWins is a dictionary of last weeks win count for each team"""
        
    nextWeek = getWeek(year, weekNum)
    ###Step 2: Find Power Rankings
    oldRate, oldSeas  = Base.TEAM_RATINGS.copy(), Base.SEASON_RATINGS.copy()

    if(weekNum <= 17): ###Team Ratings aren't changed in the playoffs, only Season Ratings
        Base.TEAM_RATINGS = Ratings.changeWeekRatings(lastWeek, Base.TEAM_RATINGS)
    Base.SEASON_RATINGS = Ratings.changeWeekRatings(lastWeek, Base.SEASON_RATINGS)

    ###Step 4: Change Power Ranking Change Numbers
    RATE_CHANGE = Ratings.getChange(oldRate, Base.TEAM_RATINGS)
    SEAS_CHANGE = Ratings.getChange(oldSeas, Base.SEASON_RATINGS)

    ###Step 5: Data
    newString = findData(nextWeek)
    print('----------- Predictions with Injury Severity')
    print('\n'.join(newString))
    print('-----------------')
        
    ###Step 6: Prediction
    print("Predicting next weeks games")
    p = Prediction(nextWeek, year)
    preds = p.getPredictions()
    print("\n\n")
    outputPreds(preds)
    print("\nWriting Preds\n")
    writePreds(preds, nextWeek)

    ###Step 7: Update win dictionary
    if(weekNum <= 17):
        regUpdate(prevWins, lastWeek, weekNum, year)

    ###Step 11:
    print("Writing Ratings  ")
    Ratings.writeRatings(Base.TEAM_RATINGS, Base.SEASON_RATINGS)

def updateWins(winDict, lastWeek):
    copyDict = winDict.copy()
    for i in lastWeek:
        copyDict[getName(i[0])] += 1
    return copyDict

def wildcards(afcTeams, nfcTeams):
    ###Sort by chance (like seeding)
    afcTeams, nfcTeams = sorted(afcTeams, key=lambda x:x[1][-1], reverse=True),\
                         sorted(nfcTeams, key=lambda x:x[1][-1], reverse=True)
    
    afcRemain = [teamData[i] for i in teamData if(i in AFC and not(teamData[i] in afcTeams))]
    nfcRemain = [teamData[i] for i in teamData if(i in NFC and not(teamData[i] in nfcTeams))]

    afcRemain = sorted(afcRemain, key=lambda x:x[-1][-1], reverse=True)
    nfcRemain = sorted(nfcRemain, key=lambda x:x[-1][-1], reverse=True)

    afcTeams.extend(afcRemain[:3]); nfcTeams.extend(nfcRemain[:3])
    return afcTeams, nfcTeams

def writePoints(fileData, pointVals):
    """Returns a string that should be overwritten to dataCollect.csv"""
    oldText, newText = "", ""
    for i in fileData.split("\n"):
        ###Split into parts with all data, and this weeks, without point data
        if(len(i.split(",")) == 4):
            oldText += i + "\n"
        else:
            newText += i + "\n"

    newText = newText[:-1]
    for i in range(len(newText.split("\n"))):
        if(i >= len(pointVals)):
            break
        j = newText.split("\n")[i]
        ###Add the next column of points
        nextRow = j + "," + str(pointVals[i]) + "\n"
        oldText += nextRow
    return oldText

def writePreds(preds, nextWeek):
    print("To put in guiText.txt")
    for i in range(len(nextWeek)):
        game, pre = nextWeek[i], preds[i].split(', ')
        win = pre[0]
        percent = pre[-1][:-1]
        lose = getLoser(win, [game[0], game[1]])
        home = game[1]
        print(win, lose, home, percent, sep=',')
