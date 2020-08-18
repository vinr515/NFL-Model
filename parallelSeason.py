from multiprocessing import Pool
from NFL_Model.Season import *
import time

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

rate, seas = Ratings.getOldRatings(2019)
rate, seas = replaceTeams(rate, seas, 'Oakland Raiders', 'Las Vegas Raiders', 'Washington Redskins', 'Washington Football Team')

if __name__ == "__main__":
    old = time.time()
    season = Season(0, 2020, rate, seas)
    with Pool(4) as p:
        t = p.map(season.predictSeason)

    new = time.time()
    season.outputChances()
    print("{} seconds taken".format(new-old))
