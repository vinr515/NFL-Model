from NFL_Model import Prediction, Ratings, Train, Injury, Season, Game, Plays
from bs4 import Comment
from NFL_Model import nflPredict as Base
import os, numpy

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

def getWeek(year, week):
    """Gets a list of games for the last and next week, even playoffs"""
    lastWeek = Train.getWeek(year, week)
    if(week < 17):
        nextWeek = Train.getWeek(year, week+1, True)
    else:
        nextWeek = Train.getWeek(year, week+14, True)

    return lastWeek, nextWeek

def masseyGames(year, week):
    allGames = []
    for i in range(week):
        try:
            allGames.extend(Train.getWeek(year, i+1))
        except ValueError:
            print("Can't get week {}".format(i+1))

    return allGames

def masseyMatchups(allGames):
    teamOrder = list(Base.SEASON_RATINGS.keys())
    teamGames = {}
    for i in teamOrder:
        line = []
        teamYear = [j for j in allGames if i in j]
        for j in teamOrder:
            if(j == i):
                line.append(len(teamYear))
            else:
                numGames = len([k for k in teamYear if j in k])
                line.append(-numGames)
        teamGames[i] = line.copy()

    return teamOrder, teamGames

def masseyMatrix(allGames):
    teamOrder, teamGames = masseyMatchups(allGames)
    matrix = []
    for i in teamOrder[:-1]:
        matrix.append(teamGames[i])
    matrix.append([1 for i in range(len(matrix[0]))])

    return matrix

def masseyPoints(allGames):
    teamOrder = list(Base.SEASON_RATINGS.keys())
    teamList = {}
    for i in teamOrder:
        teamList[i] = 0

    for i in allGames:
        teamList[i[0]] = teamList[i[0]]+i[3]
        teamList[i[1]] = teamList[i[1]]-i[3]
    
    columnVector = [[teamList[i]] for i in teamOrder]
    return columnVector

def masseyRankings(year, week):
    allGames = masseyGames(year, week)
    matrix = masseyMatrix(allGames)
    points = masseyPoints(allGames)

    try:
        inverse = numpy.linalg.inv(matrix)
        comb = inverse.dot(points)
        print("Invertible")
        return comb
    except numpy.linalg.LinAlgError:
        leastSquares = numpy.linalg.lstsq(matrix, points)
        print("Not Invertible")
        return leastSquares

def outputBothRankings(year, week):
    """Outputs both the model's rankings, and Massey Rankings, to make it easier
to compare"""
    massRank = masseyRankings(year, week)
    teamList = list(Base.SEASON_RATINGS.keys())
    finalOrder = [[teamList[i], massRank[i][0]] for i in range(len(teamList))]
    finalOrder = sorted(finalOrder, key=lambda x:x[1], reverse=True)

    rateCoef, seasCoef = Base.RATING_AND_INJURY.coef_[2], Base.RATING_AND_INJURY.coef_[3]
    rateFactor, seasFactor = rateCoef/(seasCoef+rateCoef), seasCoef/(seasCoef+rateCoef)
    combineMethod = lambda x:(rateFactor*Base.TEAM_RATINGS[x])+(seasFactor*Base.SEASON_RATINGS[x])
    teamOrder = sorted(Base.TEAM_RATINGS, key=combineMethod, reverse=True)

    print("%-40s %-30s" % ("Massey Rankings", "Model Rankings"))
    for i in range(32):
        line = (i+1, finalOrder[i][0], str(round(finalOrder[i][1], 2)))
        line = line + (teamOrder[i], str(round(combineMethod(teamOrder[i]), 2)))
        print("%-2d: %-30s %-5s %-30s %-5s" % line)

    return

def outputMassey(year, week):
    rankings = masseyRankings(year, week)
    teamList = list(Base.SEASON_RATINGS.keys())
    finalOrder = [[teamList[i], rankings[i][0]] for i in range(len(teamList))]
    finalOrder = sorted(finalOrder, key=lambda x:x[1], reverse=True)

    for i in range(len(finalOrder)):
        print("%-2d: %-30s %-10s".format(i+1) % (i+1, finalOrder[i][0], str(round(finalOrder[i][1], 2))))
    
def outputPreds(preds):
    """Outputs next weeks predictions, sorted by chance, least to most"""
    ###Gets just the percentage and sorts it
    preds = sorted(preds, key=lambda x:float(x.split(', ')[1][:4]))
    for i in preds:
        print(i)

    return

def outputPower():
    """Outputs the power rankings, using Base.TEAM_RATINGS and Base.SEASON_RATINGS"""
    rateCoef, seasCoef = Base.RATING_AND_INJURY.coef_[2], Base.RATING_AND_INJURY.coef_[3]
    rateFactor, seasFactor = rateCoef/(seasCoef+rateCoef), seasCoef/(seasCoef+rateCoef)

    combineMethod = lambda x:(rateFactor*Base.TEAM_RATINGS[x])+(seasFactor*Base.SEASON_RATINGS[x])
    teamOrder = sorted(Base.TEAM_RATINGS, key=combineMethod, reverse=True)

    for i in range(len(teamOrder)):
        team = teamOrder[i]
        line = (i+1, team, str(round(combineMethod(team), 1)))
        print("%-2d: %-30s %-7s" % line)

def update(weekNum, year):
    """Updates Team Ratings, Playoff Predictions, etc.
Week Num is the last week played"""
    lastWeek, nextWeek = getWeek(year, weekNum)
    ###Step 2: Find Power Rankings
    oldRate, oldSeas  = Base.TEAM_RATINGS.copy(), Base.SEASON_RATINGS.copy()

    if(weekNum <= 17): ###Team Ratings aren't changed in the playoffs, only Season Ratings
        Base.TEAM_RATINGS = Ratings.changeWeekRatings(lastWeek, Base.TEAM_RATINGS)
    Base.SEASON_RATINGS = Ratings.changeWeekRatings(lastWeek, Base.SEASON_RATINGS)

    ###Step 4: Change Power Ranking Change Numbers
    Base.RATE_CHANGE = Ratings.getChange(oldRate, Base.TEAM_RATINGS)
    Base.SEAS_CHANGE = Ratings.getChange(oldSeas, Base.SEASON_RATINGS)
        
    ###Step 6: Prediction
    p = Prediction.Prediction(nextWeek, year, Base.TEAM_RATINGS.copy(), Base.SEASON_RATINGS.copy(), weekNum+1)
    preds = p.getPredictions()
    print('\n')
    outputPreds(preds)
    print('\n')
    outputBothRankings(year, weekNum)
    Ratings.writeRatings(Base.TEAM_RATINGS, Base.SEASON_RATINGS)
