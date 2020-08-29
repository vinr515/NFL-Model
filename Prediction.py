from . import Injury
from . import nflPredict as Base
import os

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

class Prediction:
    """Predicts the score for all games included. gamesList is from
    getGame()"""
    def __init__(self, gamesList, year, rate, seas):
        self.year = year
        self.rate = rate
        self.seas = seas
        if(listWorks(gamesList)):
            self.gamesList = convert(gamesList, year)
            self.predictions = predictAll(self.gamesList)
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
        return self.predictions

def convert(gamesList, year, rate, seas):
    """Takes the list of games from nflPredict.Train and only keeps the data
    It needs ([ratingDiff, season rating diff, injury])"""
    newList = []
    print("Gathering Data ", end='')
    for i in gamesList:
        ratingDiff = rate[i[1]] - rate[i[0]]
        seasDiff = seas[i[1]] - seas[i[0]]
        injury = Injury.getFuture(i, year)
        line = [ratingDiff, seasDiff] + injury + [i[1], i[0]]
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


def predictAll(gameList):
    """Finds a list of predictions for all games in gamesList
    Use if the predictions haven't been found yet"""
    predictions = []
    inputData = [i[:-2] for i in gameList]
    probs = list(Base.RATING_AND_INJURY.predict(inputData))
    ###Subtract HFA because the predictions are done for the away team
    ###And percentages should add up to 100 (Home+HFA[1], Away-HFA[1])
    probs = [(i*100) for i in probs]
    
    winners = [winner(probs[i], gameList[i][-2], gameList[i][-1]) for i in range(len(probs))]

    return winners

def winner(percent, home, away):
    """Takes the number from getResult, and turns it into a team"""
    ###All predictions are done from home's Point of View
    percent = 99.9 if percent > 100 else percent
    formatPercent = str(round(percent, 1))
    ###Use the unformatted percent so a tie is very unlikely
    if(percent > 50):
        return "{}, {}%".format(home, formatPercent)
    if(percent < 50):
        return "{}, {}%".format(away, formatPercent)
    return "Tie between {} and {}".format(home, away)
