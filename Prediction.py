from NFL_Model import Injury
from NFL_Model import nflPredict as Base
import Season
import os

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

class Prediction:
    """Predicts the score for all games included. gamesList is from
    getGame()"""
    def __init__(self, gamesList, year, rate, seas, week):
        self.year = year
        self.rate = rate.copy()
        self.seas = seas.copy()
        self.week = checkWeek(week, gamesList)
        if(listWorks(gamesList)):
            self.gamesList = convert(gamesList, year, self.week, rate, seas)
            self.predictions = predictAll(self.gamesList, self.week)
        else:
            self.gamesList = [-1]
            self.predictions = [-1]
        
    def addGame(self, newGame):
        """Add a game. It's result will be predicted"""
        self.gamesList.append(newGame)
            
    def getGameList(self):
        """Returns the list of games to predict"""
        return self.gamesList

    def getPredictions(self):
        """Returns predictions for games. Use this"""
        return [winnerString(*i) for i in self.predictions]

def checkWeek(week, games):
    if(type(week) == int):
        return [week for i in range(len(games))]
    if(len(week) < len(games)):
        return week + [week[-1] for i in range(len(games)-len(week))]
    if(len(week) > len(games)):
        return week[:len(games)]
    if(len(week) == len(games)):
        return week
    raise ValueError("Week should be an integer or list, not {}".format(type(week)))

def convert(gamesList, year, week, rate, seas):
    """Takes the list of games from nflPredict.Train and only keeps the data
    It needs ([ratingDiff, season rating diff, injury])"""
    newList = []
    print("Gathering Data ", end='')
    for j in range(len(gamesList)):
        i = gamesList[j]
        ratingDiff = rate[i[1]] - rate[i[0]]
        seasDiff = seas[i[1]] - seas[i[0]]
        injury = Injury.getFuture(i, year)
        line = [1, week[j], ratingDiff, seasDiff] + injury + [i[1], i[0]]
        newList.append(line)
        print(".", end='')

    return newList

def listWorks(gamesList):
    """Checks if the gamesList can be used."""
    ###Checks if  gamesList is a list/tuple of games
    outer = type(gamesList) == list or type(gamesList) == tuple
    if(not(outer)):
        return False
    ###Checks if each list/tuple is also a list/tuple of info
    inner = type(gamesList[0]) == list or type(gamesList[0]) == tuple
    if(not(inner)):
        return False
    ###Checks if each game is future (3 pieces of info)
    number = len(gamesList[0]) == 3
    if(not(number)):
        return False
    return True


def predictAll(gameList, week):
    """Finds a list of predictions for all games in gamesList
    Use if the predictions haven't been found yet"""
    predictions = []
    inputData = [i[:-2] for i in gameList]
    ###It goes [Home, Week, ...]
    probs = list(Base.RATING_AND_INJURY.predict(inputData))

    winners = [getWinner(probs[i], gameList[i][-2], gameList[i][-1]) for i in range(len(probs))]
    #winners = [winnerString(probs[i], gameList[i][-2], gameList[i][-1]) for i in range(len(probs))]

    return winners

def getWinner(percent, home, away):
    if(percent > .5):
        return home, percent
    if(percent < .5):
        return away, 1-percent
    return "{} and {}".format(home, away), percent

def winnerString(winner, percent):
    """Returns a string that says who wins, and by how much"""
    if(percent == .5):
        return "Tie between " + winner
    
    formatPercent = lambda x:str(round(x, 1))
    percentString = str(formatPercent(100*percent))
    points = pointSpread(percent)
    return "{}, {}% (by about {} points)".format(winner, percentString, points)

def pointSpread(percent):
    """Calculates the point spread for a game with a %chance of winning (0-1)"""
    ###leftBounds is for percent (who in this case won the game)
    leftBounds, rightBounds = Season.getBounds(percent)
    ###This is the average of all possible scores, not necessarily the most common
    halfScore = min(leftBounds, key=lambda x:abs(.5-x[1]))[2]
    ###Number of scores that are higher than the halfScore
    numPlus = max(leftBounds, key=lambda x:x[2])[2] - halfScore
    ###Number of scores that are less than the halfScore
    numMinus = (halfScore - 1) + len(rightBounds)
    totalNum = (numPlus - numMinus)/2 + halfScore

    return totalNum
