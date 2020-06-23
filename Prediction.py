import Injury
from nflPredict import regD, HFA_VALS

class Prediction:
    """Predicts the score for all games included. gamesList is from
    getGame()"""
    def __init__(self, gamesList, year, rate, seas):
        print("Check if Injuries are correct. (Changed from Injury score to Injury difference")
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
        ratingDiff = rate[i[0]] - rate[i[1]]
        seasDiff = seas[i[0]] - seas[i[1]]
        injury = Injury.getFuture(i, year)
        line = [ratingDiff, seasDiff] + injury + [i[0], i[1]]
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
    probs = list(regD.predict(inputData))
    ###Subtract HFA because the predictions are done for the away team
    ###And percentages should add up to 100 (Home+HFA[1], Away-HFA[1])
    probs = [(i*100)-HFA_VALS[1] for i in probs]
    
    winners = [winner(probs[i], gameList[i][-2], gameList[i][-1]) for i in range(len(probs))]

    return winners

def winner(percent, away, home):
    """Takes the number from getResult, and turns it into a team"""
    ###All predictions are done from away's Point of View
    percent = 99.9 if percent > 100 else percent
    formatPercent = str(round(percent, 1)) + "%"
    ###Use the unformatted percent so a tie is very unlikely
    ###(All 0's return 50.002%, which would show an away win here
    if(percent < 50):
        return home + ", " + formatPercent
    if(percent > 50):
        return away + ", " + formatPercent
    return "Tie"