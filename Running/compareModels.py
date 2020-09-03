"""compareModels.py is in the "Running" folder. This folder is used for special
scripts. Other files like Train, Injury, Prediction, etc. that have methods are
in the NFL_Model folder.
This changes the path to the NFL_Model, so the files are organized, but
can still be run. """
from NFL_Model.Update import *
from sklearn.metrics import log_loss, roc_curve, roc_auc_score
import urllib3
import concurrent.futures
import time
from NFL_Model.Running import optimizeAlpha as alpha
import pickle
import os
BeautifulSoup = Base.BeautifulSoup
plt = Base.plt

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

Base.TEAM_ABBRS['Oakland Raiders'] = Base.TEAM_ABBRS['Las Vegas Raiders']
Base.TEAM_ABBRS['St. Louis Rams'] = Base.TEAM_ABBRS['Los Angeles Rams']
Base.TEAM_ABBRS['San Diego Chargers'] = Base.TEAM_ABBRS['Los Angeles Chargers']

THIS_MODEL = Base.RATING_AND_INJURY

def getHead():
    with open(folderPath+'gameData/newHold.csv', 'r') as f:
        HEAD = f.read().split('\n')[0] + '\n'
    return HEAD

def getYear(year):
    """Returns a list of x and y values for every game in one year"""
    data = alpha.getRows()
    
    ratingsList = alpha.findRatings(data)
    finalData = alpha.addRatings(data, ratingsList)
    finalData = alpha.doubleData(finalData, True)
    finalData = [j for j in finalData if j[0] == year and j[1] == 1]

    finalX, finalY = alpha.xyData(finalData)
    finalX = [j[1:] for j in finalX]
    return finalX, finalY

def getOrder(year):
    """Returns a list of [Away Team, Home Team] lists in one year. The X and Y
values from getYear() are in this order"""
    data = alpha.getRows()
    data = [[i[3], i[2]] for i in data if i[0] == str(year)]
    return data

def compareModels(year, func):
    """Compares two models from one year using "func". "func" takes in two lists
and returns two numbers"""
    outcomes, probs = preds538(year)
    xVals, yVals = getYear(year)

    preds = THIS_MODEL.predict(xVals)
    outcomeList = [func(yVals, preds), func(outcomes, probs)]
    return outcomeList
    
def preds538(year, order=False):
    """Returns the outcomes and chances of winning predicted by 538 for one year.
If order = True, it also returns the order of the games, like getOrder()"""
    url = 'https://projects.fivethirtyeight.com/{}-nfl-predictions/games/'.format(year)
    http = urllib3.PoolManager()
    r_tags = http.request("GET", url).data.decode('utf-8')
    soup = BeautifulSoup(r_tags, "html.parser")
    weeks = findWeeks(soup)
    probs, outcomes = [], []
    gameOrder = []
    for i in weeks:
        #probs.append([]); outcomes.append([])
        for j in i.find_all('div', attrs={'class':'game'}):
            game = gameData(j, order)
            #probs[-1].append(game[0])
            #outcomes[-1].append(game[1])
            probs.append(game[0])
            outcomes.append(game[1])

            if(order):
                gameOrder.append(game[2])

    if(not(order)):
        return outcomes, probs
    return outcomes, probs, gameOrder

def findWeeks(soup):
    """Returns a list of weeks of predictions for 538"""
    weeks = soup.find_all('section', attrs={'class':'week'})
    weeks = [i for i in weeks if 'week' in i.find('h3').text.lower()]
    return weeks

def gameData(game, order=False):
    """Returns the chance of winning and away and home team for one game"""
    body = game.find('table', attrs={'class':'game-body'}).find('tbody')
    homeTeam = body.find_all('tr')[-1]
    chance = homeTeam.find('td', attrs={'class':'td number chance'}).text
    chance = int(chance[:-1])/100
    
    win = homeTeam.find_all('td')[1].attrs['class']
    if('loser' in ''.join(win).lower()):
        win = 0
    else:
        win = 1

    if(not(order)):
        return chance, win
    awayTeam = body.find_all('tr')[0]
    homeName = homeTeam.find_all('td')[1].text.strip()
    awayName = awayTeam.find_all('td')[1].text.strip()

    return chance, win, [awayName, homeName]
def numCorrect(outcomes, probs):
    a = 0
    for i in range(len(outcomes)):
        if((probs[i] >= 0.5) == (outcomes[i] == 1)):
            a += 1
    return a/len(outcomes)

def rocGraph(year):
    outcomes, probs = preds538(year)

    xVals, yVals = getYear(year)
    preds = THIS_MODEL.predict(xVals)

    five_fp, five_tp, _ = roc_curve(outcomes, probs)
    rate_fp, rate_tp, _ = roc_curve(yVals, preds)

    plt.plot(five_fp, five_tp, color='blue', label='FiveThirtyEight')
    plt.plot(rate_fp, rate_tp, color='green', label='This Model')
    plt.legend()
    plt.title('Comparison of models for the {} season'.format(year))
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.show()

    five, rate = roc_auc_score(outcomes, probs), roc_auc_score(yVals, preds)
    return rate, five

def findGaps(year):
    xVals, yVals = getYear(year)
    gameOrder = getOrder(year)
    #games, gameOrder = findRatings(getGames(year), year)

    preds = THIS_MODEL.predict(xVals)

    outcomes, probs, newOrder = preds538(2019, True)
    gameOrder = changeNames(gameOrder)

    finalOrder = sorted(gameOrder)
    newY, newPreds, newOutcomes, newProbs = [], [], [], []
    newXVals = []
    for i in range(len(finalOrder)):
        thisIndex = gameOrder.index(finalOrder[i])
        fiveIndex = newOrder.index(finalOrder[i])

        newY.append(yVals[thisIndex])
        newPreds.append(preds[thisIndex])
        newXVals.append(xVals[thisIndex])
        newOutcomes.append(outcomes[fiveIndex])
        newProbs.append(probs[fiveIndex])

    return newY, newPreds, newXVals, newOutcomes, newProbs, finalOrder

def changeNames(order):
    swapDict = {'New York Jets':'N.Y. Jets', 'New York Giants':'N.Y. Giants',
                'Los Angeles Rams':'L.A. Rams', 'Los Angeles Chargers':'L.A. Chargers'}
    for i in range(len(order)):
        line = []
        for j in order[i]:
            if(j in swapDict):
                line.append(swapDict[j])
            else:
                line.append(j.replace(Base.getName(j), '').strip())
        order[i] = line.copy()

    return order

"""
def f(x):
    time.sleep(5)
    return x*x

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(f, i) for i in [0, 1, 2, 3, 4, 5]]
    print([f.result() for f in futures])

old = time.time()
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(getYear, i) for i in range(2000, 2020)]
    allText = [f.result() for f in futures]
new = time.time()
print("Time: ", new-old)
"""
