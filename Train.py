from . import nflPredict as Base
import os

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

def getFuture(tableRow):
    """Returns a (away, home, website) tuple, when you don't want the result"""
    cols = tableRow.find_all("td")
    if(not(len(cols))): return
    if(len(cols) == 8):
        away, home = cols[2].text, cols[5].text
        try:
            gameCode = cols[1].find("a").get("href")
        except AttributeError:
            return
    else:
        ###First column (week) isn't a "td" object, so each index goes down one
        win, lose, place = cols[3].text, cols[5].text, cols[4].text
        if(place == "@"):
            away, home = win, lose
        else:
            away, home = lose, win
            
        try:
            gameCode = cols[6].find("a").get("href")
        except AttributeError:
            return
        
    return (away, home, gameCode)

def getGame(tableRow): 
    """Returns a tuple of (winner, loser, home, points) for that game (row in table)"""
    ###Games in the future don't have all the stats, and their data is in different columns
    if(len(tableRow.find_all("td")) == 8):
        return getFuture(tableRow)

    winner, loser = tableRow.find_all("td")[3], tableRow.find_all("td")[5]
    winner,  loser = winner.text.strip(), loser.text.strip()    
    wPoints, lPoints = tableRow.find_all("td")[7], tableRow.find_all("td")[8]
    
    try:
        pointDiff = int(wPoints.text.strip()) - int(lPoints.text.strip())
    except ValueError:
        raise ValueError("Call Train.getWeek(year, week, future=True), since some games haven't been played")

    gameCode = tableRow.find_all("td")[6].find("a").get("href")
    ###The 6th position (index 4) has @ if it was winner @ loser
    if(tableRow.find_all("td")[4].text.strip().lower() == "@"):
        return (winner, loser, loser, pointDiff, gameCode)
    return (winner, loser, winner, pointDiff, gameCode)

def getWeek(year, week, future=False):
    """Returns the week in that year The tuples are (winner, loser, home, points)"""
    url = "https://www.pro-football-reference.com/years/" + str(year) + "/games.htm"
    soup = Base.openWebsite(url)

    games = []
    ###Each row (tr tag) is a different game
    row = soup.find_all("tr")
    for i in row:
        if(i.find("th").get('csk') == str(week)):
            if(future):
                ###If future is true, it will add a game in the future form, without points
                games.append(getFuture(i))
            else:
                games.append(getGame(i))

    return games

def getYear(year, future=False):
    """Gets one year of games. Faster than getting it week by week
because this opens one website while that opens 21"""
    games = {}
    url = "https://www.pro-football-reference.com/years/{}/games.htm".format(str(year))
    soup = Base.openWebsite(url)
    row = soup.find_all("tr")

    for i in row:
        num = i.find('th').get('csk')
        ###Week 29 doesn't have anything
        if(num == '29' or not(num)): continue
        
        if(future): thisGame = getFuture(i)
        else: thisGame = getGame(i)
        
        if(num in games and thisGame):
            games[num].append(thisGame)
        elif(thisGame):
            games[num] = [thisGame]

    weekNums = sorted(list(games.keys()), key=lambda x:int(x))
    realGames = []
    for i in weekNums:
        realGames.append(games[i])

    return realGames
