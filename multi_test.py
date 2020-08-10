from multiprocessing import Pool
import time
print("Bob the Bjgct")
from Update import *

Base.TEAM_ABBRS['Oakland Raiders'] = Base.TEAM_ABBRS['Las Vegas Raiders']
Base.TEAM_ABBRS['St. Louis Rams'] = Base.TEAM_ABBRS['Los Angeles Rams']
Base.TEAM_ABBRS['San Diego Chargers'] = Base.TEAM_ABBRS['Los Angeles Chargers']

def getHead():
    with open('gameData/newHold.csv', 'r') as f:
        HEAD = f.read().split('\n')[0] + '\n'
    return HEAD

def getYear(i):
    print("Getting year {}".format(i))
    year = Train.getYear(i)[:17]
    rosters = {}
    text = ""
    for j in Ratings.getOldRatings(i)[0]:
        rosters[j] = Injury.getRoster(j, i)
    print("Finished rosters for year {}".format(i))
    q = 0
    for j in year:
        q+=1
        for k in j:
            home, away = k[2], Base.getLoser(k[2], [k[1], k[0]])
            if(k[2] == k[0]):
                homeWins = '1'
            else:
                homeWins = '0'
            points = str(k[3])
            homeInj = list(map(str, Injury.findInjuries(home, 1, k[-1], roster=rosters[home])))
            awayInj = list(map(str, Injury.findInjuries(away, 0, k[-1], roster=rosters[away])))
            line = [str(i), home, away, homeWins, points]
            line.extend(homeInj); line.extend(awayInj)
            line = ','.join(line) + '\n'
            text += line
        print("Year {} Week {}".format(i,q))
    return text

if __name__ == '__main__':
    old = time.time()
    with Pool(4) as p:
        t = p.map(getYear, range(2000, 2020))
    new = time.time()
    print("Time: ", new-old)

    HEAD = 'Year,Home,Away,Home Wins,Points,HQB,HRB,HWR,HTE,HT,HG,HC,HDT,HDE,HLB,HCB,HS,AQB,ARB,AWR,ATE,AT,AG,AC,ADT,ADE,ALB,ACB,AS\n'

    ALL_TEXT = ''.join(t)
    ALL_TEXT = HEAD + ALL_TEXT
    
    #with open('gameData/newHold.csv', 'w') as f:
    #    f.write(ALL_TEXT)
