from . import nflPredict as Base
from bs4 import BeautifulSoup, Comment
import os

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

comment = lambda text:isinstance(text, Comment)
def getSpread(gameCode):
    soup = Base.openWebsite('https://www.pro-football-reference.com'+gameCode)
    infoTable = soup.find('div', attrs={'id':'all_game_info'})
    infoComment = infoTable.find(string=comment).split('>')

    oddLabelIndex = [i for i in range(len(infoComment)) if 'vegas' in infoComment[i].lower()]
    odd = infoComment[oddLabelIndex[0]+2]
    odd = odd[:odd.index('<')]

    odd = odd.split(' ')
    points = odd[-1]
    if('pick' in points.lower()):
        points = 0.0
    else:
        points = float(points)
    team = ' '.join(odd[:-1])

    return team, points
    
