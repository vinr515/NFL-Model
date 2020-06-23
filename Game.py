from nflPredict import openWebsite, getLoser, regB, TEAM_ABBRS

def combineDrives(awayDrives, homeDrives):
    """Combines away team's drives and home team's drives, and sorts by start time
(First drive to Last Drive)"""
    allDrives =  []
    aIndex, hIndex = 0, 0
    while(aIndex < len(awayDrives) or hIndex < len(homeDrives)):
        ###Add all the away drives if there are no more home drives
        if(aIndex >= len(awayDrives)):
            allDrives.append(homeDrives[hIndex])
            hIndex += 1
            continue
        if(hIndex >= len(homeDrives)):
            allDrives.append(awayDrives[aIndex])
            aIndex += 1
            continue

        aDrive, hDrive = awayDrives[aIndex], homeDrives[hIndex]
        ###Find when each drive happened
        aTime, hTime = aDrive[1]*60+aDrive[2], hDrive[1]*60+hDrive[2]
        ###Add the drive that started earlier
        if(aTime > hTime):
            allDrives.append(aDrive)
            aIndex += 1
        else:
            allDrives.append(hDrive)
            hIndex += 1
    return allDrives

def driveData(driveList, teamAbr, home):
    """Gets the useful info from the drives: home/away, time left, start yard, length, and yards gained
driveList is a list of drives for that team
teamAbr is that team's abbreviation (from nflRatings.csv)
home is 1 for home team, 0 for away team"""
    newList = []
    for i in driveList:
        ###Turn the time into the time left in the game
        if(i[1] == 'OT'): i[1] = '5'
        quarter = (4-int(i[1]))*15
        start = i[2].split(':')
        start[0] = int(start[0]) + quarter
        start[1] = int(start[1])
        ###Sometimes the drive is at the end of the half
        ###And no plays are run, so it doesn't give a start and runs into
        ###an error here. So, it just skips this step
        if(len(i[3].split(' ')) < 2):
            continue
        ###Yards become 0-100, higher numbers are closer to the endzone
        if(i[3].split(' ')[0] == teamAbr):
            yardStart = int(i[3].split(' ')[1])
        else:
            yardStart = int(i[3].split(' ')[1]) + 50
        ###Find the end time of the drive
        minLength, secLength = i[5].split(':')
        minLength, secLength = sub(start[0],start[1],int(minLength),int(secLength))
        yards =  int(i[6])
        newList.append([home, start[0], start[1], yardStart, minLength, secLength, yards])

    return newList

def finalData(allDrives, scores, homeWin):
    """Turns the drives into the final thing,
with home/away, seconds left, possesion (1/0), start yard, point difference at the start
and points scored"""
    scoreIndex = 0
    awayScore, homeScore = 0, 0
    data = []
    for i in allDrives:
        if(scoreIndex < len(scores)): nextScore = scores[scoreIndex]
        if(i[0] == 0):
            pointDiff = awayScore - homeScore; win = 1-homeWin
        else:
            pointDiff = homeScore - awayScore; win = homeWin
        ###Seconds left, 1 and 0 for possession, start of drive, point difference and outcome
        before = [i[0], i[1]*60+i[2], 1, i[3], pointDiff, win]
        data.append(before)
        ###If score happened before the end of the drive, the score happened during that drive
        if(scoreIndex < len(scores) and i[4]*60+i[5] < nextScore[0]*60+nextScore[1]):
            awayScore = nextScore[2]
            homeScore = nextScore[3]
            scoreIndex += 1
        if(i[0] == 0): pointDiff = awayScore - homeScore;
        else: pointDiff = homeScore - awayScore;
        after = [i[0], i[4]*60+i[5], 0, 0, pointDiff, win]
        data.append(after)

    return data

def findScores(gameCode):
    """Finds all scoring plays from a game"""
    soup = openWebsite("https://www.pro-football-reference.com"+gameCode)
    ###awayScore and homeScore are for the actual scores
    awayScore = soup.find_all(attrs={"data-stat":"vis_team_score"})[1:]
    homeScore = soup.find_all(attrs={"data-stat":"home_team_score"})[1:]
    ###allScores if for the time, quarter, etc.
    allScores = soup.find_all("tr")[4:4+len(awayScore)]
    scores = []
    ###If the quarter is blank, the score happened in the last quarter
    lastQuarter = 1
    for i  in range(len(allScores)):
        score = allScores[i]
        ###The Quarter is in the <th> tag, but we want the time to the
        ###end of the game
        quarter = score.find("th").text.strip()
        if(quarter == ""): quarter = lastQuarter
        if(quarter == "OT"): quarter = '5'
        lastQuarter = quarter
        quarter = (4-int(quarter))*15
        ###Find the time of the score, and then make that and quarter
        ###the time left
        time = score.find("td").text.strip().split(":")
        time[0] = quarter+int(time[0])
        time[1] = int(time[1])
        ###Take the next value in awayScore and homeScore to find the score
        ###at that time
        aScore = awayScore[i].text.strip()
        hScore = homeScore[i].text.strip()
        scores.append([time[0], time[1], int(aScore), int(hScore)])
        
    return scores, soup

def getAllData(gameCode, awayAbr, homeAbr, homeWin):
    """Returns final data for all drives in a game
[Away, Secs, Poss., Yards, Points, Win]"""
    ###Gets the scores in the game
    scores, webSoup = findScores(gameCode)
    ###Gets the stuff for away and home drives
    awayDrives, homeDrives = getDriveBase(soup=webSoup)
    awayDrives, homeDrives = getDrives(awayDrives), getDrives(homeDrives)
    awayDrives = driveData(awayDrives, awayAbr, 0)
    homeDrives = driveData(homeDrives, homeAbr, 1)
    ###Combines away and home drives into one sorted list
    allDrives = combineDrives(awayDrives, homeDrives)
    ###Gets the final data
    allData = finalData(allDrives, scores, homeWin)
    return allData    

def getDriveBase(gameCode=None, soup=None):
    """Gets the base HTML that has the drives, from pro football reference"""
    if(not(soup)):
        soup = openWebsite("https://www.pro-football-reference.com"+gameCode)
    ###Create a soup object if it isn't given
    if(not(soup)):
        soup = openWebsite("https://www.pro-football-reference.com"+gameCode)
    ###The drives are found in a comment under a <div id="all_vis_drives"> tag
    awayDrives = soup.find(attrs={"id":"all_vis_drives"})
    homeDrives = soup.find(attrs={"id":"all_home_drives"})
    

def getDrives(drives):
    """Returns all the drives for away team, then home team. If no soup object
is given, it is created with gameCode"""
    driveList = []
    ###Get the comment under the tag
    findComment = lambda text:isinstance(text, Comment)
    comments = str(drives.find(string=findComment)).split('\n')
    ###Remove all things with nothing in them
    comments = [i.strip() for i in comments if i != '']
    ###If there's only 1 '<' and 1 '>', it is just a tag and has nothing important
    comments = [i for i in comments if(not(i.count('<') == 1 and i.count('>') == 1))]
    ###The last one is usually two tags, and has nothing in it
    comments = [i for i in comments if(not(i == ''))][:-1]
    ###Get everything about the drive for each drive.
    ###The first 10 things are just tags and don't have anything
    for i in range(10, len(comments)):
        thisDrive = comments[i].split('>')[:-1]
        thisDrive = [i[:i.index('<')] for i in thisDrive if(not(i[0] == '<'))]
        driveList.append(thisDrive)
        
    return driveList

def predict(game, homeTeam, rating, seasRating, xy=False):
    """Predicts at the start and end of all drives in a game.
game is a tuple for the game
homeTeam is 1 for percentage for the home team, 0 for the away team
rating is a All-Time Ratings dictionary
seasRating is a Season Ratings dictionary
If xy=True, it returns a list of (seconds left, % chance) pairs"""
    if(len(game) == 3): away, home = game[0], game[1]
    elif(len(game) == 5):
        away, home = game[2], getLoser(game[2], [game[1], game[0]])

    awayAbbr, homeAbbr = TEAM_ABBRS[away].upper(), TEAM_ABBRS[home].upper()
    ###Home wins is used as the y for training
    data = getAllData(game[-1], awayAbbr, homeAbbr, 0)

    rateDiff = rating[away] - rating[home]
    seasDiff = seasRating[away] - seasRating[home]
    newData = []
    ###There are some repeats. This stores the seconds of all drives
    secVals = []
    indexes = []
    for i in range(len(data)):
        j = data[i]
        if(j[1] in secVals): continue
        if(j[0] == homeTeam):
            line = [rateDiff, seasDiff, j[1], j[3], j[4]]
        else:
            line = [-rateDiff, -seasDiff, j[1], j[3], j[4]]
        secVals.append(j[1])
        newData.append(line)
        indexes.append(i)

    vals = list(regB.predict_proba(newData)[:, 1])
    finalList = []
    for i in range(len(vals)):
        ###indexes[i] is the index of the data point used
        ###data[indexes[i]] is what was used.
        ###data[indexes[i]][0] is the away/home of that data point
        ###If it is hometeam, it is for the correct team
        if(data[indexes[i]][0] == homeTeam):
            finalList.append(vals[i]*100)
        else:
            finalList.append((1-vals[i])*100)

    if(not(xy)):
        return finalList
    finalList = list(zip(secVals, finalList))
    finalList = [list(i) for i in finalList]
    return finalList
    

def sub(minutes, seconds, subMin, subSec):
    """Subtracts two times  (min:sec - min:sec)"""
    seconds -= subSec
    minutes -= subMin
    while(seconds < 0):
        minutes -= 1
        seconds += 60
    return minutes, seconds
