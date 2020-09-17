from multiprocessing import Pool
from NFL_Model.Season import *
import NFL_Model.Train
import time
import os

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

SPLIT_CHARS = '!'
def replaceList(series, old, new):
    return SPLIT_CHARS.join(series).replace(old, new).split(SPLIT_CHARS)

def replaceTeams(rate, seas, *args):
    for i in range(0, len(args), 2):
        for j in range(len(Base.DIVISIONS)):
            if(args[i] in Base.DIVISIONS[j]):
                Base.DIVISIONS[j] = replaceList(Base.DIVISIONS[j], args[i], args[i+1])
                break
        if(args[i] in Base.NFC):
            Base.NFC = replaceList(Base.NFC, args[i], args[i+1])

        rate[args[i+1]] = rate[args[i]]; del rate[args[i]]
        seas[args[i+1]] = seas[args[i]]; del seas[args[i]]

    return rate, seas

def rewriteSeas(seas):
    newSeas = seas.copy()
    for i in newSeas:
        newSeas[i] = 500.0
    return newSeas

def chances(a):
    a.predictSeason()
    return a.getData()

def schedule(a):
    """Returns the League Schedule. Each game/list is
[Win, Lose, Home, Chance, Points]"""
    a.predictSeason()
    sched, afcSeeds, nfcSeeds = a.leagueSched, a.afcSeeds, a.nfcSeeds
    return sched, afcSeeds, nfcSeeds

def superBowls(a):
    a.predictSeason()
    return a.getSuperBowls()

def outputSched(index, stop, sched):
    while(index < stop):
        line = sched[index]
        stringLine = "%-!s AT %-!s. %-!s wins by %-@s points (had a %-#s chance)"
        stringLine = stringLine.replace("!", str(MAX_LENGTH))
        stringLine = stringLine.replace("@","4").replace("#","5")
        
        away = Base.getLoser(line[2], [line[1], line[0]])
        perc = str(round(float(line[3])*100, 1))
        print(stringLine % (away, line[2], line[0], str(line[-1]), perc))
        index += 1

    return index

def outputSeeds(afcSeeds, nfcSeeds):
    formatString = "%-{}s %-{}s".format(MAX_LENGTH, MAX_LENGTH)
    print(formatString % ("AFC", "NFC"))
    for i in range(len(nfcSeeds)):
        afcLine = "{}. {}".format(str(i+1), afcSeeds[i])
        nfcLine = "{}. {}".format(str(i+1), nfcSeeds[i])
        print(formatString % (afcLine, nfcLine))

def outputWins(afcPlayoffs, nfcPlayoffs, winDict):
    newLength = MAX_LENGTH-6
    formatString = "%-{}s %-{}s %-{}s %-{}s %-{}s %-{}s".format(newLength, 3,3, newLength,3,3)
    divOrder = ["West", "South", "North", "East", "West", "South", "North", "East"]
        
    for i in range(4):
        afcOrder = outputDiv(Base.DIVISIONS[i], afcPlayoffs, winDict)
        nfcOrder = outputDiv(Base.DIVISIONS[i+4], nfcPlayoffs, winDict)
        divName = divOrder.pop()

        print(formatString % ("AFC "+divName, "W", "L", "NFC "+divName, "W", "L"))
        
        for j in range(len(afcOrder)):
            afcTeam, nfcTeam = afcOrder[j], nfcOrder[j]
            afcLoss, nfcLoss = 16-winDict[afcTeam], 16-winDict[nfcTeam]
            print(formatString % (afcTeam, str(winDict[afcTeam]), afcLoss,
                                  nfcTeam, str(winDict[nfcTeam]), nfcLoss))
        print()

def outputDiv(div, playoffs, winDict):
    order = []
    for i in playoffs:
        if(i in div):
            order.append(i)
    rest = sorted([i for i in div if not i in order], key=lambda x:winDict[x], reverse=True)
    order = order + rest
    return order
        
#Base.DIVISIONS[3][2] = 'Oakland Raiders'
#Base.AFC[-2] = 'Oakland Raiders'
#Base.AFC[-1] = 'San Diego Chargers'
#Base.DIVISIONS[3][-1] = 'San Diego Chargers'
#Base.NFC[-3] = 'St. Louis Rams'
#Base.DIVISIONS[-1][-3] = 'St. Louis Rams'
#rate, seas = Ratings.getOldRatings(2018)
#rate, seas = replaceTeams(rate, seas, 'Oakland Raiders', 'Las Vegas Raiders', 'Washington Redskins', 'Washington Football Team')
#for i in seas:
#    seas[i] = 500.0
Base.replace({'Washington Redskins':'Washington Football Team'}, full=True,
             rate = Base.TEAM_RATINGS, seas = Base.SEASON_RATINGS)
Base.SIM_NUM = 5000
MAX_LENGTH = 30#len(max(rate, key=lambda x:len(x)))

PREDICT_YEAR = 2020

if __name__ == "__main__":
    old = time.time()
    s = Season(0, PREDICT_YEAR, Base.TEAM_RATINGS, Base.SEASON_RATINGS)
    
    with Pool(2) as p:
        #results = p.map(schedule, [s])[0]
        results = p.map(chances, [s])[0]

    new = time.time()

    """
    sched, afcSeeds, nfcSeeds = results
    regSched, postSched, sbSched = sched[:256], sched[256:-1], sched[-1:]
    
    splitPoint = int(len(postSched)/2)
    afcSched, nfcSched = postSched[:splitPoint], postSched[splitPoint:]
    newPost = []

    for i in range(len(postSched)):
        num = i//2
        if(i%2 == 0):
            newPost.append(afcSched[num])
        else:
            newPost.append(nfcSched[num])

    sched = regSched + newPost + sbSched
    
    weekLengths = [len(i) for i in Train.getYear(PREDICT_YEAR, future=True)[:17]]
    playoffRounds = [(6, "Wildcard"), (4, "Divisional"), (2, "Championship")
                     , (1, "Super Bowl")]

    winDict = {}
    for i in Base.TEAM_RATINGS:
        winDict[i] = 0
    for i in sched[:256]:
        winDict[i[0]] += 1

    output = (input('Show Schedule (y/n): ').lower() == 'y')
    if(output):
        index = 0
        for i in range(len(weekLengths)):
            print("\nWeek {}: ".format(i+1))
            index = outputSched(index, index+weekLengths[i], sched)
                
        print("\nSeeding ")
        outputSeeds(afcSeeds, nfcSeeds)
        for i in playoffRounds:
            print("\n{} Round: ".format(i[1]))
            index = outputSched(index, index+i[0], sched)

    print("\nRegular Season Standings")
    outputWins(afcSeeds, nfcSeeds, winDict)
    """
    
    print("%-{}s %8s %8s %8s %8s %8s".format(MAX_LENGTH) % ("Team Name", "Won SB", "Made SB", "Won Div", "Made Playoffs", "Avg Win"))
    for i in results:
        i = [i[0]] + [str(round(i[j], 1))+'%' for j in range(1, len(i)-1)] + [round(i[-1], 1)]
        print("%-{}s %8s %8s %8s %8s %8s".format(MAX_LENGTH) % (str(i[0]), str(i[1]), str(i[2]), str(i[3]), str(i[4]), str(i[5])))

    print('\n\n')
    for i in results:
        if(i[1] == 0):
            print("{} has a 0% chance of winning the Super Bowl".format(i[0]))
        if(i[2] == 0):
            print("{} has a 0% chance of making the Super Bowl".format(i[0]))
    print("{} Seconds  ".format(new-old))
