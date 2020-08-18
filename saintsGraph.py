
from NFL_Model.Update import *
numpy = Base.numpy
plt = Base.plt


def addYear(year, rating):
    newList = []
    for i in year:
        rating = Ratings.changeWeekRatings([i], rating)
        if('New Orleans Saints' in i):
            newList.append(rating['New Orleans Saints'])

    return newList, rating

def moving_average(l):
    p = []
    for i in range(len(l)-5):
        p.append(numpy.mean(l[i:i+5]))
    return p

def plotGraph(x, y):
    plt.figure(figsize=(12.2, 6.1))
    plt.plot(x, y, color='#A08A58')
    plt.xticks([i for i in range(1,len(y),84)],[2000+i//16 for i in range(1,len(y),84)])
    plt.xlabel('Year')
    plt.ylabel('All-Time Rating')
    plt.title('New Orleans Saints All-Time Rating')

def labelSbs(sbList, yVals):
    for i in sbList:
        xPoint = int(16*(i-1999))+1
        yPoint = yVals[xPoint]-2
        plt.annotate('Super Bowl Win', xy=(xPoint, yPoint), xycoords='data',
                     xytext=(xPoint, yPoint-3), textcoords='data',
                     arrowprops=dict(facecolor='black',width=0.05,headwidth=5,headlength=5))
        

with open('gameData/newHold.csv', 'r') as f:
    gameData = f.read().split('\n')[1:-1]
    gameData = [i.split(',') for i in gameData]

newData = [[] for i in range(2000, 2020)]
for i in gameData:
    index = int(i[0])-2000
    home = i[1]
    if(i[3] == '1'):
        win, lose = i[1], i[2]
    else:
        win, lose = i[2], i[1]
    points = int(i[4])
    newData[index].append((win, lose, home, points, ''))
    
oldRating = Ratings.getOldRatings(1999)[0]
oldSaints = [oldRating['New Orleans Saints']]

for i in range(2000, 2020):
    if(i == 2002):
        oldRating['Houston Texans'] = 500.0
    elif(i == 2016):
        oldRating['Los Angeles Rams'] = oldRating['St. Louis Rams']
        del oldRating['St. Louis Rams']
    elif(i == 2017):
        oldRating['Los Angeles Chargers'] = oldRating['San Diego Chargers']
        del oldRating['San Diego Chargers']

    year = newData[i-2000]
    newList, oldRating = addYear(year, oldRating)
    oldSaints.extend(newList)

x = [i for i in range(321)]
moveAvg = moving_average(oldSaints)
moveAvg.extend([oldSaints[-1]]*5)

"""
plt.figure(figsize=(8, 4))
plt.plot(x, moveAvg, color='#A08A58')
plt.xticks([i for i in range(1,len(oldSaints),84)],[2000+i//21 for i in range(1,len(oldSaints),84)])
plt.xlabel('Year')
plt.ylabel('All-Time Rating')
plt.title('New Orleans Saints All-Time Rating')
plt.annotate('Super Bowl Win', xy=(211, 500), xycoords='data',
             xytext=(0.5, 0.5), textcoords='axes fraction',
             arrowprops=dict(facecolor='black', shrink=0.05))
"""
plt.rcParams.update({'font.size':20})
plotGraph(x, moveAvg)
labelSbs([2009], oldSaints)
plt.show()
