from . import nflPredict as Base
from bs4 import Comment
import os

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

def findInjuries(team, homeTeam, gameCode, roster=None, starters=None):
    """Finds the injury score of the gameCode game for team
If roster or starters is given, it will be used, and will take less time
homeTeam is 0 for away, 1 for home. team is the team name"""
    if(not(starters)):
        starters = getGameStarters(gameCode)
        if(type(starters[1]) == str):
            starters = starters[0]
        else:
            starters = starters[homeTeam]
    if(not(roster)):
        year = Base.getGameYear(gameCode)
        roster = getRoster(team, year)

    return findScore(roster, starters)

def findScore(roster, starters):
    """Returns the injury scores, giving number of injuries for a position"""
    realName = lambda name: name.replace("*","").replace("+","").strip()
    if(type(starters) == list):
        ###The last two in roster are the kicker and punter which aren't listed
        starterName = [i[1] for i in starters]
    
        ###This adds the position for every player whose name isn't in
        ###The list of starter names
        injuries = [i[0] for i in roster if not(realName(i[1]) in starterName)] ###Make the position one used by RATING_AND_INJURY
        for i in range(len(injuries)):
            if(injuries[i] in Base.POS_CONVERT):
                injuries[i] = Base.POS_CONVERT[injuries[i]]
    else:
        allText = starters.prettify()
        injuries = [i[0] for i in roster if not realName(i[1]) in allText]

    injuries = [injuries.count(i) for i in Base.POS_ORDER]

    return injuries

def formatStarters(string):
    """Takes all of the tags from the players list and turns it into (pos, name)"""
    string = string[:string.index('<')].strip()
    return string

def getDifference(game, aRost=None, hRost=None, aStart=None, hStart=None):
    """Returns the injury difference for a past game (away team - home team)"""
    awayTeam = Base.getLoser(game[2], [game[0], game[1]])
    awayInj = findInjuries(awayTeam, 0, game[4], roster=aRost, starters=aStart)
    homeInj = findInjuries(game[2], 1, game[4], roster=hRost, starters=hStart)
    
    diff = subtract(awayInj, homeInj)
    return diff

def getFuture(game, year):
    """Returns the injury difference for a future game in year (home team - away team)"""
    ###Future games list all of their injuries, including backups
    ###So the backups need to be separated
    url = "https://www.pro-football-reference.com" + game[2]
    soup = Base.openWebsite(url)
    
    awayAbbr, homeAbbr = Base.TEAM_ABBRS[game[0]], Base.TEAM_ABBRS[game[1]]
    awayInj = soup.find("div", attrs={"id":"all_{}_current_injuries".format(awayAbbr)})
    homeInj = soup.find("div", attrs={"id":"all_{}_current_injuries".format(homeAbbr)})

    ###Gets the injuries
    awayInj, homeInj = getFutInjuries(awayInj), getFutInjuries(homeInj)
    
    ###[[pos, name], [pos, name], ...] for all starters
    awayInj, homeInj = getStarters(awayInj, game[0], year), getStarters(homeInj, game[1], year)

    awayInj = [Base.POS_CONVERT[i[0]] for i in awayInj if i[0] in Base.POS_CONVERT]
    homeInj = [Base.POS_CONVERT[i[0]] for i in homeInj if i[0] in Base.POS_CONVERT]
    ###Apply the injuryVal function to get a number for each player, then add it
    awayScore = [awayInj.count(i) for i in Base.POS_ORDER]
    homeScore = [homeInj.count(i) for i in Base.POS_ORDER]
    return subtract(homeScore, awayScore)
    
def getFutInjuries(injuries):
    """Returns a list of [name, position] lists of injuries for a future game
Injuries is a bs4 Tag"""
    ###The actual table is with javascript, so we get it with the comment
    findComment = lambda text:isinstance(text, Comment)
    ###Separate the comment by line
    comm = str(injuries.find(string=findComment)).split("\n")
    ###Only keep the ones that have to do with the table (tr, th)
    comm = [i.split("<") for i in comm if "tr" in i and "th" in i]
    injuryList = []
    for i in comm:
        ###Only href and pos have the name and position
        ###Adding one means the tag (>) isn't there
        inj = [j[j.index(">")+1:] for j in i if "href" in j or "pos" in j]
        injuryList.append(inj)

    injuryList = [[i[1], i[0]] for i in injuryList]
    return injuryList
    
def getGameStarters(url):
    """Returns a list of (position, name) tuples for the games starters"""
    rosters = getStarterTags(url)
    if(type(rosters[1]) != str):
        awayPlayers, homePlayers = getPlayers(rosters[0]), getPlayers(rosters[1])
        return awayPlayers, homePlayers
    else:
        return rosters

def getPlayers(roster):
    players = []
    for i in roster:
        i = i.split('>')
        ###Everything in the list is either a tag or something we want.
        ###Tags start with <
        keepData = [j for j in i if (len(j) > 1) and (j[0] != '<')]
        if(len(keepData) < 2):
            print(roster)
            print(keepData)
            print("This is where it doesn't work. ")
        name, pos = formatStarters(keepData[0]), formatStarters(keepData[1])
        players.append((pos, name,))

    return players

def getRoster(team, year):
    """Returns a list of (Position, Name) tuples for the entire roster"""
    soup = Base.openWebsite(getRosterUrl(Base.TEAM_ABBRS[team], year))
    starterStats = soup.find_all("tr", class_="full_table")
    roster = []
    for i in starterStats:
        ###The last slice is used to make the position LB instead of RLB,
        ###Since both are used
        pos = i.find("th").text.strip()[-2:]
        name = i.find("td", attrs={"data-stat":"player"}).text.strip()
        roster.append((pos, name,))
        
    return roster

def getRosterUrl(team, year):
    """Returns the url that has the starting roster for the team for that year"""
    url = "https://www.pro-football-reference.com/teams/{}/{}_roster.htm"
    return url.format(team, str(year))

def getStarters(injuries, team, year):
    """Removes all backups from the list of injuries"""
    roster = getRoster(team, year)
    ###Remove awards and positions from these players. Positions can sometimes
    ###change, but names won't and there usually aren't repeat names
    roster = [i[1].replace("*", "").replace("+","") for i in roster]
    ###Only keeps player in that years roster. i[1] is the name
    starters = [i for i in injuries if i[1] in roster]
    return starters

def getStarterTags(url):
    """Returns a list of tags in the comment with the games starters"""
    soup = Base.openWebsite("https://www.pro-football-reference.com"+url)
    ###The comment is right above the actual tags for the starters
    awayStarters = soup.find("div", attrs={"id":"all_vis_snap_counts"})
    homeStarters = soup.find("div", attrs={"id":"all_home_snap_counts"})
    if(awayStarters == None):
        return (soup, "This game does not have a snap count list")

    findComment = lambda text: isinstance(text, Comment)
    ###Gets everything in the div tag that is a comment, then splits it by tag
    awayRoster = awayStarters.find(string=findComment).split(">")
    homeRoster = homeStarters.find(string=findComment).split(">")

    awayPlayers = removeHeaders(awayRoster)
    homePlayers = removeHeaders(homeRoster)
    return awayPlayers, homePlayers

def removeHeaders(splitTags):
    newTags, flag, line = [], False, ''
    for i in splitTags:
        if('<tr' in i and not(flag)):
            flag = True
            line = ''
        elif('</tr' in i and flag):
            flag = False
            newTags.append(line.strip())
        elif(flag):
            line += i + '>'

    ###Scope is row for all players, and never for headers
    newTags = [i for i in newTags if 'scope="row"' in i]
    return newTags

def subtract(aInj, bInj):
    """Subtracts injuries from each position. (aInj - bInj)"""
    if(len(aInj) != len(bInj)): print("Injury lists are not the same size")
    diff = [aInj[i]-bInj[i] for i in range(len(aInj))]
    return diff
