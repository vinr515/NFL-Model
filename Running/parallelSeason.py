from multiprocessing import Pool
from NFL_Model.Season import *
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
Base.SIM_NUM = 5000
rate, seas = Ratings.getOldRatings(2018)
#rate, seas = replaceTeams(rate, seas, 'Oakland Raiders', 'Las Vegas Raiders', 'Washington Redskins', 'Washington Football Team')
for i in seas:
    seas[i] = 500.0
MAX_LENGTH = len(max(rate, key=lambda x:len(x)))

if __name__ == "__main__":
    old = time.time()
    season = Season(0, 2019, rate, seas)
    with Pool(2) as p:
        t = p.map(superBowls, [season])[0]
    new = time.time()

    print("%-{}s %8s %8s %8s %8s %8s".format(MAX_LENGTH) % ("Team Name", "Won SB", "Made SB", "Won Div", "Made Playoffs", "Avg Win"))
    for i in t:
        print("%-{}s %8s %8s %8s %8s %8s".format(MAX_LENGTH) % (str(i[0]), str(i[1]), str(i[2]), str(i[3]), str(i[4]), str(i[5])))

    
    print("{} seconds taken".format(new-old))
