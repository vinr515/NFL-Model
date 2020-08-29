from . import Game
from . import nflPredict as Base
import os
Comment = Base.Comment

thisPath = os.path.dirname(__file__)
folderPath = thisPath[:thisPath.index("NFL_Model")]+"NFL_Model\\"

FINAL_DATA_HEAD = ['Home/Away', 'Seconds', 'Down', 'To Go', 'Yard', 'Play Type',
                   'Away Score', 'Home Score', 'Penalty', 'Yards', 'Points']

def addScore(finalData):
    for i in range(1, len(finalData)):
        ###Index of that teams points. If it's away posession, it's a zero
        index = int(finalData[i-1][0])
        ###Sometimes the points column is blank and has to be skipped
        if(finalData[i][index+6] == '' or finalData[i-1][index+6] == ''):
            continue

        ###Difference of points. If it's home ball, i[0] is 1, and home points
        ###are in 1+6=7. If it's away, i[0]=0, away points are in 0+6=6
        diff = int(finalData[i][index+6])-int(finalData[i-1][index+6])
        ###Add points to the end
        finalData[i].append(str(diff))

    return finalData

def baseDrives(soupObj, awayAbbr, homeAbbr):
    """Returns all drives in the game, after chaning the time to seconds passed"""
    awayDrives, homeDrives = Game.getDriveBase(soup=soupObj)
    awayDrives, homeDrives = Game.getDrives(awayDrives), Game.getDrives(homeDrives)
    allDrives = []
    awayDrives = changeDriveYard(awayDrives, awayAbbr, homeAbbr)
    homeDrives = changeDriveYard(homeDrives, homeAbbr, awayAbbr)
    allDrives.extend(awayDrives)
    allDrives.extend(homeDrives)

    for i in range(len(allDrives)):
        ###i[2] is a 5:13 time left in the quarter
        minutes, secs = list(map(int, allDrives[i][2].split(':')))
        ###i[5] is a 5:13 how long the drive took
        lengthMinutes, lengthSecs = list(map(int, allDrives[i][5].split(':')))
        ###This makes the time into seconds since the start of the quarter
        quarter = 900-(minutes*60+secs)
        ###i[1] is the quarter, this makes it second passed since the start of the game
        if(allDrives[i][1] == 'OT'):
            quarterNum = 5
        else:
            quarterNum = int(allDrives[i][1])
        startTime = (quarterNum-1)*15*60 + quarter
        ###This finds when the drive ended, not how long it took
        endTime = startTime+lengthMinutes*60+lengthSecs
        allDrives[i][1] = startTime
        allDrives[i][5] = endTime
        ###We don't need the quarter and the time
        del allDrives[i][2]

    return allDrives, len(awayDrives)

def changeDriveYard(drives, abbr, notAbbr):
    """Changes the yard in the list of drives to numbers (45 -> 55)"""
    for i in range(len(drives)):
        ###i[3] is a string (like 'CLT 45'), i[3][4:] gets the number
        index, notIndex = len(abbr)+1, len(notAbbr)+1
        if(abbr in drives[i][3]):
            yard = drives[i][3][index:]
            drives[i][3] = yard
        elif(notAbbr in drives[i][3]):
            yard = 100-int(drives[i][3][notIndex:])
            drives[i][3] = str(yard)
        else:
            given = '(%s, %s)' % (abbr, notAbbr)
            real = drives[i][3]
            raise ValueError('Given: ' + given + ', Real Abbreviations include ' + real)

    return drives
    

def cleanText(string):
    """Gets the text in all tags (including nested tags)"""
    i = 0
    ret_s = ""
    has_sign = False
    while(i < len(string)):
        ###< is the start of the tag, so there's no text
        if(string[i] == '<'):
            has_sign = True
        ###> means the end of the tag, so take out the flag
        elif(string[i] == '>'):
            has_sign = False

        if(not(has_sign) and string[i] != '>'):
            ###> and < aren't part of the tag
            ret_s += string[i]
        i += 1
        
    return ret_s

def combineData(drives, plays):
    """Combines the drives and the plays"""
    combined = []
    ###The drives are sorted by time, so the plays and drives go in order
    index = 0
    for i in range(len(plays)):
        thisPlay = plays[i].copy()
        thisDrive = drives[index]
        #thisPlay[0] >= thisDrive[2] and 
        ###When the play is after the end of this drive, you go to the next drive
        if(not(thisPlay[0] < thisDrive[5])):
            index += 1
            if(index >= len(drives) and i != len(plays)-1):
                raise IndexError("Not Enough Drives")
            ###This happens when the last play goes to 0:00
            ###Since 3600 is not < than 3600, it looks for the next drive
            ###This reset back to this drive
            if(index >= len(drives) and i == len(plays)-1):
                index -= 1
            
            thisDrive = drives[index]
        ###The only thing from the drive that's important is the posession
        newLine = [thisDrive[0]] + thisPlay[:7]
        combined.append(newLine)

    return combined

def falsePlays(entireGame):
    """Takes out false plays like Challenges, that don't take up a play"""
    newGame = []
    for i in range(len(entireGame)):
        ###False plays don't have a time of play
        if(entireGame[i][1] == ''):
            continue
        
        line = entireGame[i]
        ###Turn the time into seconds passed
        minutes, secs = list(map(int, line[1].split(':')))
        quarter = 900-(minutes*60+secs)
        if(line[0] == 'OT'):
            quarterNum = 5
        else:
            quarterNum = int(line[0])
        time = (quarterNum-1)*15*60 + quarter
        line[1] = time
        del line[0]
        ###Only real plays are added
        newGame.append(line.copy())

    return newGame

def fillDrives(drives, allPlays):
    """Adds missing drives from the game, if necessary"""
    drives = sorted(drives, key=lambda x:x[2])
    sortedDrives = []
    for i in range(len(drives)-1):
        ###Usually, the next drive starts when the last drive ends
        thisLine, nextLine = drives[i].copy(), drives[i+1].copy()
        ###index 5 is for the ending time, index 2 is for the starting time
        if(thisLine[5] != nextLine[2]):
            ###thisLine should be there, but there should also be a drive in the midle
            sortedDrives.append(thisLine)
            ###That drive is for the other team
            oppPos = str(1-int(thisLine[0]))
            ###The Xs don't matter, only the team, when it starts and when it ends
            ###This fills the space that was missing
            newLine = [oppPos, 'X', thisLine[5], 'X', 'X', nextLine[2], 'X', 'X']
            sortedDrives.append(newLine)
        else:
            sortedDrives.append(thisLine)
            
    sortedDrives.append(nextLine)
    oppPos = str(1-int(nextLine[0]))
    ###If it is missing the last drive, and the game didn't go into overtime
    if(nextLine[5] < 3600):
        newLine = [oppPos, 'X', nextLine[5], 'X', 'X', 3600, 'X', 'X']
        sortedDrives.append(newLine)
    ###The last drive is missing, and the game did go to overtime
    elif(nextLine[5] < allPlays[-1][0]):
        newLine = [oppPos, 'X', nextLine[5], 'X', 'X', allPlays[-1][0], 'X', 'X']
        sortedDrives.append(newLine)
        
    return sortedDrives

def finalData(plays, awayAbbr, homeAbbr):
    """Turns the plays into final data, except for the points, which has
    to be done differently"""
    final = []
    for i in plays:
        line = i.copy()
        newLine = line.copy()

        ###It needs the abbreviation for the yard line
        if(line[0] == '1'): yardAbbr = homeAbbr
        else: yardAbbr = awayAbbr

        ###Turns the yard line into one number (55, not IND 45)
        if(yardAbbr in line[4] and line[4]):
            newLine[4] = int(line[4][len(yardAbbr)+1:])
        elif(line[4]):
            newLine[4] = 100-int(line[4][len(yardAbbr)+1:])

        ###Get play type and yards gained
        playType = returnPlay(line[5])
        yards = getYardage(line[5], playType)
        ###The play type replaces the play description
        if(playType.split(',')[0] == ''):
            print(line[5], ' in finalData function, bad play type')
        newLine[5] = playType.split(',')[0]
        ###The other two go on the end
        if('Penalty' in playType):
            newLine.append(1)
        else:
            newLine.append(0)
        newLine.append(yards)
        final.append(newLine)

    final = [list(map(str, i)) for i in final]
    return final

def formatTime(time):
    """Returns a formatted string of game time, where time is seconds passed"""
    quarter = (time//900)+1
    left = 900*quarter - time
    minutes = left//60
    seconds = left%60
    return "Quarter %d %d:%02d" % (quarter, minutes, seconds)

def getAllPlays(tags):
    """Gets every play from the game, with a list of tags"""
    entireGame = []
    flag = False
    for i in tags:
        ###Some tags are empty and raise errors, but don't have anything important
        try:
            thisPlay = getPlay(i)
        except ValueError:
            continue
        ###The game starts at the 1st Quarter ... 
        if(thisPlay == ['1st Quarter']):
            flag = True
        ###And ends with regulation or overtime. There is only one
        elif(thisPlay == ['End of Regulation'] or thisPlay == ['End of Overtime']):
            flag = False
            break
        ###Flag means the play is in the game. if len(thisPlay) > 1, it is an actual play
        ###not the end of a quarter
        elif(len(thisPlay) > 1 and flag):
            entireGame.append(thisPlay)

    return entireGame

def getComment(url):
    soup = Base.openWebsite(url)
    ###The play by play is in a comment under the <div id='all_pbp'> tag
    findComment = lambda text:isinstance(text, Comment)
    playByPlay = soup.find('div', attrs={'id':'all_pbp'})

    tags = str(playByPlay.find(string=findComment)).split('\n')
    return soup, tags

def getData(gameCode, awayAbbr, homeAbbr):
    """Gets data from every play for the gamecode"""
    url = 'https://www.pro-football-reference.com' + gameCode
    ###Get the soup object, and all the comments
    soup, tags = getComment(url)
    ###Get all the plays
    entireGame = getAllPlays(tags)
    ###Get all the drives
    allDrives, splitPoint = baseDrives(soup, awayAbbr, homeAbbr)
    ###Add a team field for each drive
    allDrives = teamDrives(allDrives, splitPoint)
    ###Take out false plays from the game
    newGame = falsePlays(entireGame)
    ###Sort the drives by time
    sortedDrives = fillDrives(allDrives, newGame)
    ###Combine the drives and plays
    combined = combineData(sortedDrives, newGame)
    ###Get the final data
    final = finalData(combined, awayAbbr, homeAbbr)
    final = addScore(final)
    return final

def getPlay(line):
    row = getRow(line)
    play = [cleanText(i) for i in row]
    return play

def getRow(line):
    """Breaks the line into the separate <th> and <td> tags"""
    play, index = [], 0
    while(index < len(line)):
        newString = line[index:]
        
        ###Add everything from the start of the cell to the end of the tag
        if('<th' in newString):
            startIndex, endIndex = newString.index('<th'), newString.index('</th')
        elif('<td' in newString):
            startIndex, endIndex = newString.index('<td'), newString.index('</td')
        ###Else means the end of the row
        else:
            break
        
        play.append(newString[startIndex:endIndex])
        index += endIndex + 5
        
    return play

def getYardage(play, playType):
    """Returns the yards gained on the play"""
    playType = playType.split(',')[0].lower()
    if(playType in ['field goal', 'pat', 'timeout', 'penalty']):
        return 0
    ###On plays with penalties, it only takes the description before the penalty
    if('Penalty' in play):
        realPlay = play[:play.index('Penalty')]
    else:
        realPlay = play

    yardage = realPlay.split(' ')
    if('yard' in yardage):
        ###It usually says 5 yards or 1 yard, so this finds the number before yard
        if(yardage[yardage.index('yard')-1] == 'Long'):
            print(yardage, playType)
        num = int(yardage[yardage.index('yard')-1])
    elif('yards' in yardage):
        num = int(yardage[yardage.index('yards')-1])
    else:
        ###It's else when it's "incomplete" or "no gain" or "PAT"
        num = 0

    return num
    

def returnPlay(play):
    """Finds the play type with the play description"""
    line = ''
    playString = play.lower()
    ###The play description has players and yards and other things
    if('pass' in playString):
        line += 'Pass'
    elif('punts' in playString):
        line += 'Punt'
    elif('field goal' in playString):
        line += 'Field Goal'
    elif('extra point' in playString):
        line += 'PAT'
    ###'kicks' can be in field goals and PATs, so it goes after those
    elif('kicks' in playString):
        line += 'Kickoff'
    elif('two point attempt' in playString):
        line += 'Two Point Attempt'
    ###Sacks will count as pass plays
    elif('sacked' in playString):
        line += 'Sack'
    elif('timeout' in playString or 'challenge' in playString):
        line += 'Timeout'
    elif('kneels' in playString):
        line += 'Kneel'
    elif('spikes' in playString):
        line += 'Spike'
    elif('penalty' != playString[:7]):
        ###Run plays don't special words in it, so as long as it wasn't
        ###any of the above and the play wasn't blown dead, it's a run play
        line += 'Run'
    ###Penalties can happen on any play.
    if('penalty' in playString):
        line += ',Penalty'
        
    if(line == ''):
        raise ValueError(play)
    ###This happens when a penalty blows the play dead
    ###This makes that a penalty play
    if(line[0] == ','):
        line = line[1:]

    return line

def teamDrives(drives, splitPoint):
    """Places a 1 before home team's drives, and a 0 before away team's drives"""
    ###splitPoint is where it goes from awayPoints to homePoints
    for i in range(len(drives)):
        if(i >= splitPoint):
            ###It is after the split point, so it changes to home drives
            drives[i].insert(0, '1')
        else:
            drives[i].insert(0, '0')

    return drives

