from multiprocessing import Pool
from ..Season import *
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
    a.predictSeason()
    return a.leagueSched

def superBowls(a):
    a.predictSeason()
    return a.getSuperBowls()

Base.DIVISIONS[3][2] = 'Oakland Raiders'
Base.AFC[-2] = 'Oakland Raiders'
Base.AFC[-1] = 'San Diego Chargers'
Base.DIVISIONS[3][-1] = 'San Diego Chargers'
Base.NFC[-3] = 'St. Louis Rams'
Base.DIVISIONS[-1][-3] = 'St. Louis Rams'
#rate, seas = Ratings.getOldRatings(2018)
#rate, seas = replaceTeams(rate, seas, 'Oakland Raiders', 'Las Vegas Raiders', 'Washington Redskins', 'Washington Football Team')
#for i in seas:
#    seas[i] = 500.0
MAX_LENGTH = 25#len(max(rate, key=lambda x:len(x)))

if __name__ == "__main__":
    old = time.time()
    allSeasons = []
    results = []
    for i in range(2003, 2016):
        rate = Ratings.getOldRatings(i-1)[0]
        seas = rewriteSeas(rate.copy())
        allSeasons.append(Season(0, i, rate.copy(), seas.copy()))
        
    with Pool(2) as p:
        t = p.map(chances, allSeasons)
    results.extend(t)

    print('End of 2015')

    Base.NFC[-3] = 'Los Angeles Rams'
    Base.DIVISIONS[-1][-3] = 'Los Angeles Rams'
    rate = Ratings.getOldRatings(2015)[0]
    rate['Los Angeles Rams'] = rate['St. Louis Rams']
    del rate['St. Louis Rams']
    seas = rewriteSeas(rate.copy())
    s = Season(0, 2016, rate.copy(), seas.copy())
    results.append(chances(s))
    print('End of 2016')

    allSeasons = []
    Base.AFC[-1] = 'Los Angeles Chargers'
    Base.DIVISIONS[3][-1] = 'Los Angeles Chargers'
    for i in range(2017, 2020):
        rate = Ratings.getOldRatings(i-1)[0]
        if('San Diego Chargers' in rate):
            rate['Los Angeles Chargers'] = rate['San Diego Chargers']
            del rate['San Diego Chargers']
        seas = rewriteSeas(rate.copy())
        allSeasons.append(Season(0, i, rate.copy(), seas.copy()))

    for i in allSeasons:
        results.append(chances(i))

    #with Pool(2) as p:
    #    t = p.map(chances, allSeasons)

    #results.extend(t)
    print('End of Everything')

    #with Pool(2) as p:
    #    t = p.map(chances, allSeasons)
    new = time.time()
    
    print("{} seconds taken".format(new-old))

    #allSeasons = []
    #for i in range(2018, 2020):
    #    rate = Ratings.getOldRatings(i-1)[0]
    #    allSeasons.append(Season(0, i, rate, seas.copy()))
    #season = Season(0, 2019, rate, seas)

        #print("%-{}s %8s %8s %8s %8s %8s".format(MAX_LENGTH) % ("Team Name", "Won SB", "Made SB", "Won Div", "Made Playoffs", "Avg Win"))
    #for i in t:
    #    print("%-{}s %8s %8s %8s %8s %8s".format(MAX_LENGTH) % (str(i[0]), str(i[1]), str(i[2]), str(i[3]), str(i[4]), str(i[5])))

