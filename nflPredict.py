###A program using Machine Learning to try and predict the NFL
###Non-Injury models are ~65% accurate, Injury models are ~67.5% accurate
###HFA = Home Field Advantage

###Machine Learning imports
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
import matplotlib.pyplot as plt
import numpy
from sklearn import linear_model as linear
from sklearn.neural_network import MLPClassifier
print("ML imports imported. ")
###To access webpages for NFL info
from bs4 import BeautifulSoup, Comment
import urllib.request
import random
import pickle
import urllib3
import requests
import os
urllib3.disable_warnings()

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

###Numbers of times to sim season for season predictions
SIM_NUM = 2000

###The formula for changing ratings changes them too much. Divide by
###RATING_DAMP to get the real correction
###(Changing ratings formula returns 5, 5/RATING_DAMP = .5, change the rating
###by .5
RATING_DAMP = 20

###New Machine Learning:
with open(folderPath+'gameData/Regression_Models.pkl', 'rb') as f:
    RATING_ONLY, RATING_AND_INJURY, IN_GAME, PLAY_TYPE, YARDS_GAINED = pickle.load(f)

MODEL_IN_KEY = {RATING_ONLY:['All-Time Rating Difference', 'Season Rating Difference'],
                RATING_AND_INJURY:['Home/Away', 'Week', 'All-Time Difference',
                                   'Season Difference', 'QB Injury Difference', 'RB', 'WR',
                                   'TE', 'T', 'G', 'C', 'DT', 'DE', 'LB', 'CB', 'S'],
                IN_GAME:['All-Time Difference', 'Season Difference', 'Seconds Left', 'Start Yard', 'Point Difference'],
                PLAY_TYPE:['Home/Away', 'Down', 'To Go', 'Yard', 'Away Points', 'Home Points'],
                YARDS_GAINED:['Seconds Passed', 'Down', 'To Go', 'Yard', 'Team Score', 'Opponent Score',
                              'Pass?', 'Run?', 'FG?', 'PAT?', '2PT?']}
                
PLAY_TYPE_OUT_KEY = ['Field Goal', 'Kickoff', 'Kneel', 'PAT', 'Pass', 'Punt', 'Run',
                 'Two Point Attempt']

### %increase for the home team for RATING_ONLY and RATING_AND_INJURY
### Also a % decrease for away team
HFA_VALS = [2, 2.5]

###Some uncommon positions are counted as other ones. (NTs are rare, so they're counted as DTs)
###This converts. OL is T because G matters less and C matters more, so T is in the middle
POS_CONVERT = {"FB":"RB", "OL":"T", "DL":"DT", "NT":"DT", "DB":"CB", "SS":"S",
               "FS":"S", 'RG':'G', 'RT':'T', 'LG':'G', 'LT':'T'}
POS_ORDER = ['QB', 'RB', 'WR', 'TE', 'T', 'G', 'C', 'DT', 'DE', 'LB', 'CB', 'S']

severeScore = {'probable': 0.25, 'questionable': 0.5, 'out': 1,
               'doubtful': 0.75, 'i-r': 1}

###The first year of Ratings in pastRatings.csv
###Chosen because it was the first year that didn't have a bunch of 1 year teams
START_YEAR = 1922


def getAllRatings():
    """Returns the current ratings for the (32) teams"""
    with open(folderPath+'gameData/nflRatings.csv', 'r') as f:
        ###1 is the heading, -1 is a blank newline
        ratings = f.read().split("\n")[1:-1]
        ratingsDict, seasonDict, divisions, abbrs = {}, {}, {}, {}
        rateChange, seasChange = {}, {}
        for i in ratings:
            data = i.split(",")
            name, rate, seasonRate, div, abbr, rChange, sChange = data
            ratingsDict[name] = float(rate)
            seasonDict[name] = float(seasonRate)
            
            abbrs[name] = abbr
            rateChange[name] = int(rChange)
            seasChange[name] = int(sChange)
            
            if(div in divisions):
                divisions[div].append(name)
            else:
                divisions[div] = [name]

    allData = (ratingsDict, seasonDict, divisions, abbrs, rateChange,
               seasChange)
    return allData


def getName(total):
    """Returns the team's name, with total being the entire thing
(Returns "Rams" for "Los Angeles Rams")"""
    return total.split(" ")[-1]

def openWebsite(url):
    errorMessages = []
    for i in [reqOpen, libOpen, lib3Open]:
        try:
            soup = i(url)
            return soup
        except Exception as e:
            errorMessages.append(str(e))
            continue
        
    raise ValueError("Website Not Found: ", ' AND '.join(errorMessages))
    
def reqOpen(url):
    r = requests.get(url).text
    return BeautifulSoup(r, "html.parser")

def libOpen(url, errorText=''):
    """Opens the url website, and returns a soup object"""
    hdr = {"User-Agent":"Mozilla/5.0"}

    req = urllib.request.Request(url, headers=hdr)
    r = urllib.request.urlopen(req)
    r_tags = r.read()
    r_tags = r_tags.decode('utf-8')
    return BeautifulSoup(r_tags, "html.parser")

def lib3Open(url):
    http = urllib3.PoolManager()
    r_tags = http.request("GET", url).data.decode('utf-8')
    soup = BeautifulSoup(r_tags, "html.parser")
    return soup

def getGameYear(gameCode):
    """Returns the year the game was with the gamecode"""
    year = int(gameCode.split("/")[-1][:4])
    ###Games before May are postseason, so are from the year before
    if(int(gameCode.split("/")[-1][4:6]) < 3):
        year -= 1
    return year

def getDivisions(divDict):
    sortDivs, divisions = sorted(divDict), []
    afcTeams, nfcTeams = [], []
    for i in range(len(sortDivs)):
        ###i is an index in sortDivs. sortDivs[i] gets the division name. divDict[...] gets you the teams
        thisDiv = divDict[sortDivs[i]]
        divisions.append(thisDiv)
        if("AFC" in sortDivs[i]):
            afcTeams.extend(thisDiv)
        else:
            nfcTeams.extend(thisDiv)
    return divisions, afcTeams, nfcTeams

def getLoser(winner, teams):
    return teams[0] if winner == teams[1] else teams[1]

def replace(teams, full=False, rate=None, seas=None):
    """Replaces a team from all records (but not from the files)
teams is a dictionary of teams[oldTeam] = newTeam"""
    for oldTeam in teams:
        newTeam = teams[oldTeam]
        if(rate):
            rate[newTeam] = rate[oldTeam]
            del rate[oldTeam]
        else:
            TEAM_RATINGS[newTeam] = TEAM_RATINGS[oldTeam]
            del TEAM_RATINGS[oldTeam]

        if(seas):
            seas[newTeam] = seas[oldTeam]
            del seas[oldTeam]
        else:
            SEASON_RATINGS[newTeam] = SEASON_RATINGS[oldTeam]
            del SEASON_RATINGS[oldTeam]

        TEAM_ABBRS[newTeam] = TEAM_ABBRS[oldTeam]
        if(full):
            replaceConference(oldTeam, newTeam)

def replaceConference(oldTeam, newTeam):
    if(oldTeam in AFC):
        AFC[AFC.index(oldTeam)] = newTeam
    if(oldTeam in NFC):
        NFC[NFC.index(oldTeam)] = newTeam

    for i in range(len(DIVISIONS)):
        if(oldTeam in DIVISIONS[i]):
            DIVISIONS[i][DIVISIONS[i].index(oldTeam)] = newTeam

        

###Constants about the NFL (and teams)
teams = getAllRatings()
TEAM_RATINGS, SEASON_RATINGS = teams[0], teams[1]
DIVISIONS, AFC, NFC = getDivisions(teams[2])
TEAM_ABBRS = teams[3]
RATE_CHANGE, SEAS_CHANGE = teams[4], teams[5]

warnings.simplefilter(action='default', category=UserWarning)
warnings.simplefilter(action='default', category=FutureWarning)
