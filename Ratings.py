from . import nflPredict as Base
import os

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"
"""
y = (2/2**x)+1 for x > 0,
y = -x + 2 for x <= 0.
y = x^2/50 for points

This way beating a much worse team will not move you up much, and a much
better team doesn't move you too much. Beating by 7 is beating next team
Divided by 20 so one game doesn't affect that much.
"""

def adjustRating(old, difference, points):
    """Returns what the new rating should be for one game/team"""
    pointsAdjust = points**2/49
    ###You subtract points djust, since a lower x is a higher y, so worse loss
    ###Means less rating, better win means more rating
    difference -= pointsAdjust

    if(difference > 0):
        newRating = (2/2**(difference)) + 1
    else:
        newRating = -difference + 3
    newRating /= Base.RATING_DAMP

    if(points < 0):
        return old - newRating
    return old + newRating

def changeWeekRatings(weekGames, rate):
    """Adjusts the ratings for all 32 teams, using the outcomes from the week.
weekGames is a list, like the one returned from getWeekGames()"""
    newRate = rate.copy()
    for i in weekGames:
        winRating, loseRating = newRate[i[0]], newRate[i[1]]
        diff = winRating - loseRating
        ###Reset the values in the dictionary to the new ratings
        newRate[i[0]] = round(adjustRating(winRating, diff, i[-2]), 1)
        newRate[i[1]] = round(adjustRating(loseRating, diff, -i[-2]), 1)

    return newRate

def getChange(oldRatings, newRatings):
    """Gets the change in power ranking for each team as a dictionary"""
    oldRank = sorted(oldRatings, key=lambda x:oldRatings[x], reverse=True)
    newRank = sorted(newRatings, key=lambda x:newRatings[x], reverse=True)
    newChange = {}
    for i in range(len(newRank)):
        team = newRank[i]
        ###newRank.index(team) is i
        rateChange = oldRank.index(team) - i
        newChange[team] = rateChange

    return newChange

def getOldRatings(year):
    """Returns All-Time Ratings and Season Ratings dictionary at the end of year"""
    ###For Ratings after 2000, they are All-Time and then Season, with a space in the middle
    with open(folderPath+'gameData/pastRatings.csv', 'r') as f:
        pastRatings = f.read().split('\n')[:-1]

    order = pastRatings[0].split(',')[1:]
    pastRatings = pastRatings[1:]
    index = year-Base.START_YEAR
    line = pastRatings[index].split(',')[1:]

    newRate, newSeas = {}, {}
    for i in range(len(order)):
        if(line[i] != ''):
            nums = line[i].split(' ')
            if(len(nums) == 1):
                newSeas[order[i]] = float(nums[0])
            elif(len(nums) == 2):
                newRate[order[i]] = float(nums[0])
                newSeas[order[i]] = float(nums[1])

    return newRate, newSeas

def writeRatings(rate, season):
    """Rewrites TEAM_RATINGS onto nflRatings.csv"""
    with open(folderPath+'gameData/nflRatings.csv', 'r') as f:
        divs = f.read().split('\n')[1:-1]
    ###Get a list of (team, division) tuples, like (Indianapolis Colts, AFC South)
    divs = dict([(i.split(",")[0], i.split(",")[3]) for i in divs])
    ###Create a mapping that will eventually become a string
    ###nflRatings.csv is sorted by team name, so this should be too
    mapping = [(i, str(rate[i]), str(season[i]), divs[i], TEAM_ABBRS[i],
                str(RATE_CHANGE[i]), str(SEAS_CHANGE[i])) for i in sorted(rate)]

    mapping.insert(0, ('Team', 'Rating', 'Season', 'Division', 'Abbreviation',
                       'Rate Change', 'Season Change'))
    string = ""
    
    for i in mapping:
        string += ','.join(i) + '\n'

    with open(folderPath+'gameData/nflRatings.csv', 'w') as f:
        f.write(string)
