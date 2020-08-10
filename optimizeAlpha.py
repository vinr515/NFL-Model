from Update import *
from multiprocessing import Pool
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
import random
numpy = Base.numpy
plt = Base.plt
linear = Base.linear
MLPClassifier = Base.MLPClassifier

def getRows():
    with open('gameData/newHold.csv', 'r') as f:
        DATA = f.read().split('\n')[1:]
        DATA = [i.split(',') for i in DATA]
    return DATA[:-1]

def findRatings(rows, dicts=False, rating=None):
    if(rating == None):
        rating = Ratings.getOldRatings(1999)[0]
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
        ratingList.append([rating[i[1]], season[i[1]], rating[i[2]], season[i[2]]])
        if(i[3] == "1"):
            win, lose = i[1], i[2]
        else:
            win, lose = i[2], i[1]
        game = [(win, lose, i[1], int(i[4]), '')]
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
        if(not('St. Louis Rams' in rating)):
            print(rating)
            print('fdafasfasdfsad')
        rating['Los Angeles Rams'] = rating['St. Louis Rams']
        season['Los Angeles Rams'] = season['St. Louis Rams']
        del rating['St. Louis Rams'], season['St. Louis Rams']
    elif(year == '2017'):
        rating['Los Angeles Chargers'] = rating['San Diego Chargers']
        season['Los Angeles Chargers'] = season['San Diego Chargers']
        del rating['San Diego Chargers'], season['San Diego Chargers']

    for i in season:
        season[i] = 500.0
    return rating, season
    
def addRatings(data, ratings):
    newData = []
    for i in range(len(data)):
        line = data[i][:1] + ratings[i] + data[i][3:]
        line = list(map(float, line))
        newData.append(line)
    return newData

def doubleData(data):
    """Doubles the data into home and away rows"""
    newData = []
    for i in data:
        homeLine = [i[0], i[1]-i[3], i[2]-i[4]]
        injDiff = [i[j]-i[j+12] for j in range(7, 19)]
        homeLine.extend(injDiff)
        awayLine = [-j for j in homeLine]
        awayLine[0] = homeLine[0]
        homeLine.append(i[5])
        awayLine.append(1-i[5])
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
                    
    return modelList

def oneGo(i):
    Base.RATING_DAMP = i
    results = []
    for j in modelList:
        reg, valScore, testScore = trainModels(train, validate, test, j)
        results.append([reg, valScore, testScore, len(validate), i])
        print('.', end='')
    line = max(results, key=lambda x:x[1])
    return line

def newModel(modelList):
    results = []
    for i in modelList:
        reg, valScore, testScore = trainModels(train, validate, test, i)
        results.append((reg, valScore, testScore, len(test)))

    return results

modelList = getModelList()
data = getRows()
ratingsList = findRatings(data)
finalData = addRatings(data, ratingsList)
finalData = doubleData(finalData)
train, validate, test = splitData(finalData)

total = train+validate
random.seed(50)
random.shuffle(total)
train, validate = total[:-1024], total[-1024:]
"""
if __name__ == '__main__':
    with Pool(4) as p:
        t = p.map(oneGo, range(15, 21))

    print(max(t, key=lambda x:x[1]))
"""
