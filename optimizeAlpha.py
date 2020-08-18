
from NFL_Model.Update import *
from multiprocessing import Pool
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
import random
import time
numpy = Base.numpy
plt = Base.plt
linear = Base.linear
MLPClassifier = Base.MLPClassifier

def getRows():
    with open('gameData/newHold.csv', 'r') as f:
        DATA = f.read().split('\n')[1:]
        DATA = [i.split(',') for i in DATA]
    return DATA

def findRatings(rows, dicts=False, rating=None):
    if(rating == None):
        rating = Ratings.getOldRatings(1999)[0]
    """
    for i in rating:
        rating[i] = 500.0
    """
    #season = rating.copy()
    
    season = {}
    for i in rating:
        season[i] = 500.0
    
    year = "2000"
    ratingList = []

    for i in rows:
        if(i[0] != year):
            rating, season = removeTeams(rating, season, i[0])
            year = i[0]
        if(len(i) < 3):
            print(i)
        ratingList.append([rating[i[2]], season[i[2]], rating[i[3]], season[i[3]]])
        if(i[4] == "1"):
            win, lose = i[2], i[3]
        else:
            win, lose = i[3], i[2]
        game = [(win, lose, i[2], int(i[5]), '')]
        rating = Ratings.changeWeekRatings(game, rating)
        season = Ratings.changeWeekRatings(game, season)

    if(dicts):
        return rating, season
    return ratingList     

def removeTeams(rating, season, year):
    if(year == '2002'):
        rating['Houston Texans'] = 500.0
        season['Houston Texans'] = 500.0
    elif(year == '2016'):
        rating['Los Angeles Rams'] = rating['St. Louis Rams']
        season['Los Angeles Rams'] = season['St. Louis Rams']
        del rating['St. Louis Rams'], season['St. Louis Rams']
    elif(year == '2017'):
        rating['Los Angeles Chargers'] = rating['San Diego Chargers']
        season['Los Angeles Chargers'] = season['San Diego Chargers']
        del rating['San Diego Chargers'], season['San Diego Chargers']

    #season = rating.copy()
    
    for i in season:
        season[i] = 500.0
    
    return rating, season
    
def addRatings(data, ratings):
    newData = []
    for i in range(len(data)):
        line = data[i][:2] + ratings[i] + data[i][4:]
        line = list(map(float, line))
        newData.append(line)
    return newData

def doubleData(data, week=False):
    """Doubles the data into home and away rows"""
    newData = []
    for i in data:
        if(week):
            homeLine = [i[0], i[1], i[2]-i[4], i[3]-i[5]]
        else:
            homeLine = [i[0], i[2]-i[4], i[3]-i[5]]
        injDiff = [i[j]-i[j+12] for j in range(8, 20)]
        homeLine.extend(injDiff)
        awayLine = [-j for j in homeLine]
        awayLine[0] = homeLine[0]
        if(week):
            awayLine[1] = homeLine[1]
        homeLine.insert(1, 1)
        awayLine.insert(1, 0)
        homeLine.append(i[6])
        awayLine.append(1-i[6])
        newData.append(homeLine)
        newData.append(awayLine)
    return newData

def splitData(data):
    train = [i[1:] for i in data if i[0] < 2018]
    validate = [i[1:] for i in data if i[0] == 2018]
    test = [i[1:] for i in data if i[0] == 2019]
    return train, validate, test

def xyData(data):
    x = [i[:-1] for i in data]
    y = [i[-1] for i in data]
    return x, y

def score(realY, predY):
    num = 0
    for i in range(len(realY)):
        if((realY[i] > 0.5) == (predY[i] > 0.5)):
            num += 1
    return num

def trainModels(train, validate, test, reg):
    trainX, trainY = xyData(train)
    valX, valY = xyData(validate)
    testX, testY = xyData(test)

    reg.fit(trainX, trainY)
    
    predY = reg.predict(valX)
    testPred = reg.predict(testX)
    return reg, score(valY, predY), score(testY, testPred)

def findBestModel(modelList=None):
    data = getRows()
    ratingsList = findRatings(data)
    finalData = addRatings(data, ratingsList)
    finalData = doubleData(finalData)
    train, validate, test = splitData(finalData)

    if(modelList == None):
        modelList = [linear.LogisticRegression(solver='lbfgs')]
    """
[MLPClassifier(), linear.LinearRegression(), linear.BayesianRidge(),
                 MLPClassifier(alpha=0.001), MLPClassifier(alpha=0.01),
                 MLPClassifier(max_iter=500), MLPClassifier(max_iter=750),
                     linear.LogisticRegression(solver='lbfgs')]
    """
        
    results = []
    for i in modelList:
        reg, valScore, testScore = trainModels(train, validate, test, i)
        results.append((reg, valScore, testScore, len(test)))

    bestModel = max(results, key=lambda x:x[1])
    return bestModel

def bestAlpha(start, end, num):
    x = [i for i in range(start, end)]
    scores = []
    for i in range(start, end):
        Base.RATING_DAMP = i
        points = []
        for j in range(num):
            reg, valScore, testScore, testPoint = findBestModel()
            points.append((valScore/testPoint)*100)
        scores.append(sum(points)/len(points))
        print(i, end=',')
    plt.scatter(x, scores)
    plt.xlabel('Rating Damp (alpha)')
    plt.ylabel('Mean Validation Score (%)')
    plt.title('Model Accuracy with Different Rating Damps')
    plt.show()


def endingRatings(year, alpha, start=None):
    Base.RATING_DAMP = alpha
    rows = getRows()
    rows = [i for i in rows if i[0] == str(year)]
    rating, season = findRatings(rows, True, start)
    return rating, season

def getModelList():
    modelList = [linear.LinearRegression()]
    cVals = [.001, .01, .1, 1, 10]
    kernVals = ['linear', 'poly', 'rbf', 'sigmoid']
    for i in cVals:
        for j in kernVals:
            modelList.append(SVC(C=i, kernel=j, probability=True))

    iterVals = [300, 500]
    tol = [0.01, 0.001, 0.0001]
    alphaVals = [1e-5, 1e-6, 1e-7]
    for i in iterVals:
        for j in tol:
            for k in alphaVals:
                for l in alphaVals:
                    modelList.append(linear.BayesianRidge(n_iter=i, tol=j, alpha_1=k, alpha_2=l))

    estimators = [100, 200, 300, 400, 500]
    for i in estimators:
        modelList.append(RandomForestClassifier(n_estimators=i))
    return modelList

def getSearchLine(model, paramDict):
    old  = time.time()
    search = GridSearchCV(model, paramDict)
    search.fit(trainX, trainY)
    pred = search.best_estimator_.predict(valX)
    num = score(valY, pred)/len(valY)
    print('.')
    new = time.time()
    print("Time: {}".format(new-old))
    return [search.best_estimator_, num]

def oneGo(i):
    Base.RATING_DAMP = i
    
    results = []
    cVals = [.001, .01, .1, 1, 10]
    alphaVals = [1e-7, 1e-5]
    tol = [0.01, 0.001, 0.0001]
    
    linReg = linear.LinearRegression().fit(trainX, trainY)
    pred = linReg.predict(valX)
    linearLine = [linReg, score(valY, pred)/len(valY)]
    
    print('.\nTime: 0')
    print(linearLine)
    ridgeLine = getSearchLine(linear.Ridge(), {'alpha':cVals, 'max_iter':[100, 750]})
    print(ridgeLine)
    logLine = getSearchLine(linear.LogisticRegression(), {'C':cVals, 'tol':tol,
                                                            'max_iter':[100, 700]})
    print(logLine)
    bayLine = getSearchLine(linear.BayesianRidge(), {'n_iter':[300, 500], 'tol':tol,
                                                      'alpha_1':alphaVals, 'alpha_2':alphaVals, 'lambda_1':alphaVals,
                                                      'lambda_2':alphaVals})
    print(bayLine)
    forestLine = getSearchLine(RandomForestClassifier(), {'n_estimators':[200, 700],
                                                          'max_features':['auto','sqrt','log2']})
    print(forestLine)
    #svcLine = getSearchLine(SVC(), {'C':cVals, 'kernel':['linear', 'poly', 'rbf', 'sigmoid'],
    #                                 'probability':[True]})
    #print(svcLine)
    
    return [linearLine, ridgeLine, logLine, bayLine, forestLine]#, svcLine]
    
    """
    for j in modelList:
        reg, valScore, testScore = trainModels(train, validate, test, j)
        results.append([reg, valScore, testScore, len(validate), i])
        print('.', end='')
    
    return results
    """

def newModel(modelList):
    results = []
    for i in modelList:
        reg, valScore, testScore = trainModels(train, validate, test, i)
        results.append((reg, valScore, testScore, len(test)))

    return results
"""
baseRating = {'Arizona Cardinals': 496.2, 'Atlanta Falcons': 499.9,
              'Baltimore Ravens': 499.9, 'Buffalo Bills': 503.0,
              'Carolina Panthers': 500.1, 'Chicago Bears': 497.7,
              'Cincinnati Bengals': 493.7, 'Dallas Cowboys': 501.6,
              'Denver Broncos': 501.9, 'Detroit Lions': 499.4,
              'Green Bay Packers': 501.5, 'Indianapolis Colts': 500.3,
              'Jacksonville Jaguars': 503.8, 'Kansas City Chiefs': 501.4,
              'Miami Dolphins': 500.8, 'Minnesota Vikings': 505.1,
              'New England Patriots': 500.6, 'New Orleans Saints': 495.1,
              'New York Giants': 499.1, 'New York Jets': 502.6,
              'Oakland Raiders': 501.9, 'Philadelphia Eagles': 495.5,
              'Pittsburgh Steelers': 499.5, 'San Diego Chargers': 498.0,
              'San Francisco 49ers': 498.2, 'Seattle Seahawks': 501.5,
              'St. Louis Rams': 504.3, 'Tampa Bay Buccaneers': 500.5,
              'Washington Redskins': 500.2, 'Tennessee Titans': 502.2,
              'Cleveland Browns': 494.4}
"""
#modelList = getModelList()
data = getRows()
ratingsList = findRatings(data)
finalData = addRatings(data, ratingsList)
finalData = doubleData(finalData, True)
train, validate, test = splitData(finalData)

total = train+validate
random.seed(50)
random.shuffle(total)
train, validate = total[:-512], total[-512:]
trainX, trainY = xyData(train)
valX, valY = xyData(validate)
"""
if __name__ == '__main__':
    with Pool(4) as p:
        t = p.map(oneGo, range(15, 21))

    print(max(t, key=lambda x:x[1]))
"""
