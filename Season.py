from NFL_Model import Ratings, Train
from NFL_Model import nflPredict as Base
import random

print("New point function is {}".format("0.1(0.92^x)"))

AFC_COUNT = 0
NFC_COUNT = 0

class Season:
    """Class to simulate season. startWeek is 0 for preseason. If
startWeek > 0, records is a dictionary with Team Name, number of wins pairs.
games is the list of games to sim, oldGames is a list of games played.
sixTeam=True for a six/12 team playoff, else seven/14"""
    def __init__(self, startWeek, year, allRate, seasRate, records={},
                 searchFor={}, games=[], oldGames=[], sixTeam=False):
        self.searchFor = searchFor
        self.startWeek = startWeek
        self.year = year
        self.sixTeam = sixTeam

        self.records, self.startRecords = records, records
        ###The ratings it started at, and the ratings to use
        ###self.allRate and seasRate can and will change
        self.ALL_START, self.SEAS_START = allRate.copy(), seasRate.copy()
        self.allRate, self.seasRate = allRate.copy(), seasRate.copy()
        ###Games that were already played. It is for tiebreakers
        self.oldGames = oldGames
        ###These record what happens in the sim
        self.leagueSched = oldGames
        self.champ, self.inSB, self.wonDiv, self.inPlay = {}, {}, {}, {}
        self.winAvg = {}
        self.initResults()
        self._startSeason()
        ###Assigns data to ALL_WEEKS
        ###startWeek is the last week played, you want the next week
        if(games):
            self.ALL_WEEKS = games.copy()
        else:
            self.ALL_WEEKS = loadGames(self.startWeek, self.year)

    def findSpecial(self):
        """Finds something special in the season (like one simulation)"""
        ###Finds one simulation in the season and returns it
        if("sim" in self.searchFor):
            i = 0
            ###Can choose what sim you want (ex. 1776)
            while(i < int(self.searchFor["sim"])):
                ###_simSeason() only updates the results for the reg. Season
                ###For the entire season, you have to sim reg. season, then post seasn
                self._startSeason()
                self._regSeason()
                ###Update records to get tiebreakers for post season
                for j in self.leagueSched:
                    self.records[j[0]] += 1
                ###Get champions and results
                afcRes, nfcRes = self._postSeason(True)
                afcChamp, afcSched, nfcChamp, nfcSched = afcRes[0], afcRes[1], nfcRes[0], nfcRes[1]
                ###Add wildcards from both confs, then divs, then championship
                self.leagueSched.extend(afcSched[:2]); self.leagueSched.extend(nfcSched[:2])
                self.leagueSched.extend(afcSched[2:4]); self.leagueSched.extend(nfcSched[2:4])
                self.leagueSched.append(afcSched[4]); self.leagueSched.append(nfcSched[4])
                sbChamp = self._sim(afcChamp, nfcChamp, homeField=False)
                sbLose = Base.getLoser(sbChamp, [afcChamp, nfcChamp])
                self.leagueSched.append([sbChamp, sbLose])
                i += 1
            return self.leagueSched

        if("playoffs" in self.searchFor):
            seeds = self.searchFor["playoffs"]
            if(self.sixTeam): afcSeeds, nfcSeeds = seeds[:6], seeds[6:]
            else: afcSeeds, nfcSeeds = seeds[:7], seeds[7:]
            for i in range(Base.SIM_NUM):
                if(i%100 == 0):
                    print(i, end=' ')
                afcChamp = self._toSB(afcSeeds)
                nfcChamp = self._toSB(nfcSeeds)
                afcName = '. '.join(afcChamp.split('. ')[1:])
                nfcName = '. '.join(nfcChamp.split('. ')[1:])
                sbChamp = self._sim(afcName, nfcName, homeField=False)
                self.champ[sbChamp] += 1
                self.inSB[afcName] += 1; self.inSB[nfcName] += 1
            for i in range(len(afcSeeds)):
                ###All of these teams were in the playoffs
                if(i <= 3):
                    self.wonDiv[afcSeeds[i]] = Base.SIM_NUM
                    self.wonDiv[nfcSeeds[i]] = Base.SIM_NUM
                self.inPlay[afcSeeds[i]] = Base.SIM_NUM
                self.inPlay[nfcSeeds[i]] = Base.SIM_NUM
                
            return

    def getData(self):
        """Returns a list, with each teams chances, as integers"""
        data = []
        for i in sorted(self.allRate):
            won = round(self.champ[i]/(Base.SIM_NUM/100), 1)
            confWon = round(self.inSB[i]/(Base.SIM_NUM/100), 1)
            divWon = round(self.wonDiv[i]/(Base.SIM_NUM/100), 1)
            post = round(self.inPlay[i]/(Base.SIM_NUM/100), 1)
            numWin = round(self.winAvg[i]/Base.SIM_NUM, 1)
            data.append([i, won, confWon, divWon, post, numWin])

        return data

    def getSimData(self, sched):
        """Gets the data as a list of lists"""
        sched = self._splitWeek(sched)
        ###Get afc, nfc seeds (sched[-1] is the playoffs, sched[-1][-1] is the SB)
        afc = [i for i in sched[-1][:-1] if i[0] in Base.AFC]
        nfc = [i for i in sched[-1][:-1] if i[0] in Base.NFC]

        ###Get all teams that played
        afcSeeds, nfcSeeds = [i[0] for i in afc], [i[0] for i in nfc]
        afcSeeds.extend([i[1] for i in afc]); nfcSeeds.extend([i[1] for i in nfc])

        ###Split them to sort them by seed
        afcSeeds = sorted([i.split('. ') for i in afcSeeds], key=lambda x:x[0])
        nfcSeeds = sorted([i.split('. ') for i in nfcSeeds], key=lambda x:x[0])
        ###Make them into sets because there are repeats
        afcSeeds, nfcSeeds = list(set(afcSeeds)), list(set(nfcSeeds))
        ###Get win totals
        realData = []
        nfcData = []
        for i in range(len(afcSeeds)):
            ###Each element is a (seed, name) tuple.
            afcWins, nfcWins = self.records['. '.join(afcSeeds[i][1])], self.records['. '.join(nfcSeeds[i][1])]
            afcLoss, nfcLoss = 16-afcWins, 16-nfcWins
            ###Add (team, wins, losses) to the list
            realData.append([afcSeeds[i][1], afcWins, afcLoss])
            nfcData.append([nfcSeeds[i][1], nfcWins, nfcLoss])

        realData.extend(nfcData)

        for i in sched[-1]:
            win, lose = i[0], i[1]
            realData.append([win, lose])

        ###Starts with [team, wins, losses], sorted by seed.
        ###Then [winner, loser] of all the games
        return realData

    def initResults(self):
        """Initialize the results dicts, so they each contain all teams"""
        for i in self.allRate:
            self.champ[i] = 0
            self.inSB[i] = 0
            self.wonDiv[i] = 0
            self.inPlay[i] = 0
            self.winAvg[i] = 0

    def outputChances(self):
        """Return, in chart like form, the chances for each team for the next season"""
        print()
        length = len(max(self.allRate, key=lambda x:len(x)))+2
        print("%-{}s %8s %8s %8s %8s %8s".format(length) % ("Team Name", "Won SB", "Made SB", "Won Div.", "Made Post.", "Avg Wins"))
        for i in sorted(self.allRate, key=lambda x:self.champ[x], reverse=True):
            ###This only sorts the keys, so we get all the teams sorted by name
            winSB = str(round(self.champ[i]/(Base.SIM_NUM/100), 1)) + "%"
            madeSB = str(round(self.inSB[i]/(Base.SIM_NUM/100), 1)) + "%"
            divWin = str(round(self.wonDiv[i]/(Base.SIM_NUM/100), 1)) + "%"
            madePlay = str(round(self.inPlay[i]/(Base.SIM_NUM/100), 1)) + "%"
            ###This one isn't a percent, so divide by 2,000
            wins = str(round(self.winAvg[i]/Base.SIM_NUM, 1))
            print("%-{}s %8s %8s %8s %8s %8s".format(length) % (i, winSB, madeSB, divWin, madePlay, wins))

    def outputSched(self, sched):
        """Formats the rest of the year and outputs it"""
        sched = self._splitWeek(sched)
        gameIndex = 0
        ###Output regular season
        for i in range(len(sched)-1):
            print("Week " + str(i+self.startWeek+1) + ".")
            for j in sched[i]:
                print("\t" + j[0] + ' beat the ' + j[1])

        ###Output post season. First find the seeds
        ###Split into afc and nfc playoffs, without super bowl
        afc = [i for i in sched[-1][:-1] if i[0] in Base.AFC]
        nfc = [i for i in sched[-1][:-1] if i[0] in Base.NFC]

        ###Get all teams that played
        afcSeeds, nfcSeeds = [i[0] for i in afc], [i[0] for i in nfc]
        afcSeeds.extend([i[1] for i in afc]); nfcSeeds.extend([i[1] for i in nfc])

        ###Split them to sort them by seed
        afcSeeds = sorted([i.split('. ') for i in afcSeeds], key=lambda x:x[0])
        nfcSeeds = sorted([i.split('. ') for i in nfcSeeds], key=lambda x:x[0])
        ###Make them into sets because there are repeats
        afcSeeds, nfcSeeds = list(set(afcSeeds)), list(set(nfcSeeds))

        ###Print the playoff seeds, formatted
        print("%1s %13s %13s" % ("#", "AFC", "NFC"))
        for i in range(len(afcSeeds)):
            ###Each element is a (seed, tuple) pair
            afcWins = self.records['. '.join(afcSeeds[i][1:])]
            nfcWins = self.records['. '.join(nfcSeeds[i][1:])]
            afcLoss, nfcLoss = 16-afcWins, 16-nfcWins
            afcTeam = afcSeeds[i][1] + " (" + str(afcWins) + "-" + str(afcLoss) + ")"
            nfcTeam = nfcSeeds[i][1] + " (" + str(nfcWins) + "-" + str(nfcLoss) + ")"
            ###i+1 is afcSeeds[i][0], but without '. '
            print("%1s %17s %17s" % (str(i+1), afcTeam, nfcTeam))

        ###Print the postseason schedule, lightly formatted
        print("Wildcard Round. ")
        for i in range(len(sched[-1])):
            ###4 Games per round, so each round is a multiple of 4
            if(i == 4):
                print("Divisional Round. ")
            if(i == 8):
                print("Conference Championship. ")
            if(i == 10):
                print("Super Bowl. ")
            j = sched[-1][i]
            win, lose = j[0], j[1]

            print("\t" + win + " beat the " + lose)

    def _postSeason(self, results=False):
        """Finds the two conference champions"""
        league = (self.records, self.leagueSched)
        afcPlayoffs, nfcPlayoffs = seeding(league, self.sixTeam)
        afcChamp, nfcChamp = self._toSB(afcPlayoffs, results), self._toSB(nfcPlayoffs, results)
        return afcChamp, nfcChamp

    def _predictRating(self, games, week):
        """Uses Season._randomWinner() to predict the winner of games based only on rating"""
        ###Turn each game into a list that can go into RATING_ONLY
        ###games are [away, home], so this is done from the Home's Point of View
        rates = [[self.allRate[i[1]]-self.allRate[i[0]], self.seasRate[i[1]]-self.seasRate[i[1]]]
                 for i in games]
        ###Predict, and add HFA, since it's from Home's POV
        rates = [[1,week]+i+[0 for j in range(12)] for i in rates]
        allProbs = []
        for i in range(len(rates)):
            allProbs.append(getResult(games[i][1], games[i][0], rates[i]))
        ###Get a [winner, loser] list
        resultList = [[allProbs[i][0], Base.getLoser(allProbs[i][0], games[i][:2])]
                       for i in range(len(allProbs))]
        
        for i in range(len(resultList)):
            self.leagueSched.append(resultList[i])
            self._ratingChange(resultList[i][0], resultList[i][1], allProbs[i][1])

    def predictSeason(self):
        """Runs the _simSeason() 2000 times, and updates the season end stats"""
        for i in range(Base.SIM_NUM):
            ###The numbers show how much longer it takes
            if(i%100 == 0):
                print(i, end=' ')
            if(i%1500 == 0):
                print()
            seasonEnd = self._simSeason()
            ###seasonEnd[0] is the super bowl champ, add one to their wins
            self.champ[seasonEnd[0]] += 1
            ###seasonEnd[1] is the teams that made the super bowl, add to their stats
            self.inSB[seasonEnd[1][0]] += 1; self.inSB[seasonEnd[1][1]] += 1
            ###The first four in each playoff won their division
            for j in range(len(seasonEnd[2])):
                if(j <= 3):
                    ###Get the first four teams from each conference, and add to their stats
                    self.wonDiv[seasonEnd[2][j]] += 1; self.wonDiv[seasonEnd[3][j]] += 1
                self.inPlay[seasonEnd[2][j]] += 1; self.inPlay[seasonEnd[3][j]] += 1

            for j in self.records:
                self.winAvg[j] += self.records[j]

    def _ratingChange(self, win, lose, points):
        """Changes the rating for both teams. """
        ###Find each team's rating
        winRate, loseRate = self.allRate[win], self.allRate[lose]
        winSeas, loseSeas = self.seasRate[win], self.seasRate[lose]
        ###Change ratings
        self.allRate = Ratings.changeWeekRatings([(win, lose, points, '')], self.allRate)
        self.seasRate = Ratings.changeWeekRatings([(win, lose, points, '')], self.seasRate)

    def _regSeason(self):
        """Predicts the regular season, and changes the records dictionary"""
        ###self.ALL_WEEKS start at self.startWeek
        for i in range(self.startWeek, 17):
            ###predictRating add them to the list anyway
            week = self.ALL_WEEKS[i-self.startWeek]
            
            self._predictRating(week, i+1)

    def _rewriteRatings(self):
        self.allRate = self.ALL_START.copy()
        self.seasRate = self.SEAS_START.copy()

    def _sim(self, home, away, num=100, homeField=True, sb=False):
        """Sims a game for the postseason. (For the regular season, it only randomizes once)
    home is False for the Super Bowl, when there is no HFA"""
        ###Win totals for both team
        expect, notExpect = 0, 0
        ###Home's Point of View
        allDiff = (self.allRate[home] - self.allRate[away])
        seasDiff = (self.seasRate[home] - self.seasRate[away])
        
        line = [1, 17, allDiff, seasDiff] + [0 for i in range(12)]
        if(not(homeField) or sb):
            line[0] = 0.5
        result = getResult(home, away, line, times=num)
        self._ratingChange(result[0], Base.getLoser(result[0], [home, away]), result[1])

        return result[0]

    def _simSeason(self):
        """Sims one season, and returns the sb winner, a list of sb teams, a list of
    teams in the afc playoffs, and a list of teams in the nfc playoffs"""
        ###Reset all lists, sim through the regular season
        self._startSeason()
        self._regSeason()
        ###Update records/wins dict
        for i in self.leagueSched:
            self.records[i[0]] += 1
        ###Get conf champions.
        ###Can't use self._postSeason() here because it needs the playoff seeds
        afcPlayoffs, nfcPlayoffs = seeding((self.records, self.leagueSched), self.sixTeam)
        afcChamp, nfcChamp = self._toSB(afcPlayoffs), self._toSB(nfcPlayoffs)
        afcName = '. '.join(afcChamp.split('. ')[1:])
        nfcName = '. '.join(nfcChamp.split('. ')[1:])
        sb = [afcName, nfcName]
        sbChamp = self._sim(afcName, nfcName, homeField=False, sb=True)
        return sbChamp, sb, afcPlayoffs, nfcPlayoffs

    def _splitWeek(self, sched):
        """Returns a list where each element is a list of games for that week"""
        newSched = []
        gameIndex = 0
        ###Loop through for every week simmed
        for i in range(self.startWeek+1, 18):
            ###i-(self.startWeek+1) is the iterations, if startWeek=7, 
            numGames = len(self.ALL_WEEKS[i-(self.startWeek+1)])
            newSched.append(sched[gameIndex:gameIndex+numGames])
            gameIndex += numGames
        ###This only does the regular season, add the rest as another week
        newSched.append(sched[gameIndex:])
        return newSched
        
    def _startSeason(self):
        ###Start with only played games
        self.leagueSched = self.oldGames.copy()
        ###Use original ratings for the season. It will change through the season
        self._rewriteRatings()
        ###When starting in the preseason, all  teams have zero wins
        if(self.startWeek == 0):
            for i in self.allRate:                
                self.records[i] = 0
        else:
            ###Otherwise, it resets to what was passed when initializing the class
            self.records = self.startRecords.copy()

    def _toSB(self, playoff, sched=False):
        """Returns the conference winner, where playoff is a list of teams in the
playoffs for one conference, sorted by seed (1 to 6). Returns the results of each game if
sched = True"""
        results = []
        ###1, 2 seeds get bye and advance to div round. 1 seed advance with 7 teams
        divRound = [playoff[0], playoff[1]] if self.sixTeam else [playoff[0]]

        if(not(self.sixTeam)):
            ###2v7
            divRound.append(self._sim(playoff[1], playoff[6], num=1))
        ###Sim 3 vs 6 and 4 vs 5, complete divRound teams
        divRound.append(self._sim(playoff[2], playoff[5], num=1))
        divRound.append(self._sim(playoff[3], playoff[4], num=1))

        if(not(self.sixTeam)):
            moreLose = Base.getLoser(divRound[1], [playoff[1], playoff[6]])
            ###Add seed to the team name. 
            winName = str(playoff.index(divRound[1])+1) + '. ' + divRound[1]
            moreLose = str(playoff.index(moreLose)+1) + '. ' + moreLose
            results.append([winName, moreLose])
            
        ###divRound[2] is the 3v6 winner. Find the loser and add to the results
        firstLose = Base.getLoser(divRound[2], [playoff[2], playoff[5]])
        secLose = Base.getLoser(divRound[3], [playoff[3], playoff[4]])
        ###More seeds to the names
        winName = str(playoff.index(divRound[2])+1) + '. ' + divRound[2]
        firstLose = str(playoff.index(firstLose)+1) + '. ' + firstLose
        results.append([winName, firstLose])

        winName = str(playoff.index(divRound[3])+1) + '. ' + divRound[3]
        secLose = str(playoff.index(secLose)+1) + '. ' + secLose
        results.append([winName, secLose])

        ###Sort teams by seed so 1 vs lower, 2 vs higher can be set up
        ###1 seed is first in playoff, so index is 0, and is first in divRound
        divRound = sorted(divRound, key=lambda x:playoff.index(x))
        lowWin = self._sim(divRound[0], divRound[3], num=1)
        highWin = self._sim(divRound[1], divRound[2], num=1)

        ###Get losers to add to the list
        lowLose = Base.getLoser(lowWin, [divRound[0], divRound[3]])
        highLose = Base.getLoser(highWin, [divRound[1], divRound[2]])
        ###Seeding
        lowName = str(playoff.index(lowWin)+1) + '. ' + lowWin
        lowLose = str(playoff.index(lowLose)+1) + '. ' + lowLose
        highName = str(playoff.index(highWin)+1) + '. ' + highWin
        highLose = str(playoff.index(highLose)+1) + '. ' + highLose
        results.append([lowName, lowLose]); results.append([highName, highLose])

        ###Sort remaining teams by seed (for HFA)
        lowWin, highWin = sorted([lowWin, highWin], key=lambda x:playoff.index(x))
        champ = self._sim(lowWin, highWin, num=1)
        runnerUp = Base.getLoser(champ, [lowWin, highWin])
        ###Seeding
        champ = str(playoff.index(champ)+1) + '. ' + champ
        runnerUp = str(playoff.index(runnerUp)+1) + '. ' + runnerUp
        results.append([champ, runnerUp])
        if(sched):
            return champ, results
        ###Winners play in conference championship, return winner
        return champ

def commonGames(teams, leagueSched):
    """Returns the ones from teams that win the common games tiebreaker"""
    games, opps = findCommonGames(teams, leagueSched)
    ###Only get the the teams in opps that are common for all tied teams
    newOpps = []
    ###This part isn't so efficient
    ###Goes through the opponents for each team
    ###Then checks if that team is in every other teams common list
    for i in opps:
        for j in i:
            if(not(False in [j in k for k in opps]) and not(j in newOpps)):
                newOpps.append(j)
    ###Common games only works for teams >= 4
    if(len(newOpps) < 4): return teams

    ###Only the wins matter
    games = [i[0] for i in games if i[1] in newOpps]
    scores = [games.count(i) for i in teams]
    return [teams[i] for i in range(len(scores)) if scores[i] == max(scores)]

def divisionWinners(league):
    """Returns a list, winners, of division winners. winners[:4] is afc, winners[4:] in nfc"""
    winners = []
    records = league[0]
    for div in Base.DIVISIONS:
        divRecs = [records[i] for i in div]
        if(divRecs.count(max(divRecs)) == 1):
            winners.append(max(div, key=lambda x:records[x]))
        else:
            win = tiebreaker(getAllWinners(divRecs, div), league, div)
            winners.append(win)
            
    return winners

def findCommonGames(teams, leagueSched):
    """Returns a list of teams that win with a common games tiebreaker"""
    opps = [[] for i in range(len(teams))]
    games = []
    for i in leagueSched:
        ###Exclude is the team that isn't tied
        if(i[0] in teams): include, exclude = i[0], i[1]
        elif(i[1] in teams): include, exclude = i[1], i[0]
        ###Else means neither team in this game is in the tiebreaker
        else: continue
        ###If exclude is also tied, then it is a head to head game; doesn't count
        if(exclude in teams): continue
        opps[teams.index(include)].append(exclude)
        games.append(i)

    return games, opps

def getAllWinners(records, teams):
    """Returns all teams from list teams that have the highest record"""
    winners = []
    for i in range(len(records)):
        if(records[i] == max(records)):
            winners.append(teams[i])
    return winners

def pointFunc(x):
    return 0.1*(0.92**x)

def getBounds(chance):
    """Finds the chance that a game ends with different point differences."""
    leftVals, rightVals = [], []
    leftNum, rightNum = 0, 0
    leftBound, rightBound = chance, 1-chance
    for i in range(1, 26):
        if(leftNum >= leftBound and rightNum >= rightBound):
            break
        leftPerc = pointFunc(i)/2
        rightPerc = leftPerc
        leftWall = max(chance-(leftNum+leftPerc), 0)
        rightWall = min(chance+(rightNum+rightPerc), 1)
        if(leftNum < leftBound):
            leftVals.append([leftPerc, leftWall, i])
        if(rightNum < rightBound):
            rightVals.append([rightPerc, rightWall, i])
        leftNum += leftPerc
        rightNum += rightPerc

    leftVals = scaleBounds(leftNum, leftBound, leftVals)
    rightVals = scaleBounds(rightNum, rightBound, rightVals)
    return leftVals, rightVals

def scaleBounds(number, maxNum, values):
    scalePercs = lambda bound,perc,ratio:bound-((bound-perc)*ratio)
    if(number < maxNum):
        ratio = maxNum/(maxNum-values[-1][1])
        values = [[i[0], scalePercs(maxNum, i[1], ratio), i[2]] for i in values]
    return values

def getPoints(leftVals, rightVals, chance, home, away):
    num = random.randint(0, 100)/100
    if(num < chance):
        choose = leftVals
        winner = home
    else:
        choose = rightVals
        winner = away
    line = choose[-1][-1]
    for i in choose:
        if(num > min(chance, i[1]) and num < max(chance, i[1])):
            line = i[-1]
            break
        chance = i[1]
	
    return winner, line

def getResult(home, away, line, times=1):
    winners = []
    num = float(Base.RATING_AND_INJURY.predict([line]))
    leftVals, rightVals = getBounds(num)
    for i in range(times):
        winners.append(getPoints(leftVals, rightVals, num, home, away))

    winNames = [i[0] for i in winners]
    winnerName = max(winNames, key=lambda x:winNames.count(x))
    points, corrects = 0, 0
    for i in winners:
        if(i[0] == winnerName):
            points += i[1]
            corrects += 1

    return winnerName, int(points/corrects)

def inDivWins(teams, division, sched):
    """Finds the team from a list of teams that had the most wins in the division"""
    divGames = [i for i in sched if i[0] in division and i[1] in division]
    divGames = [i for i in divGames if i[0] in teams or i[1] in teams]
    ###teamWins[ team name ] is the number of division wins
    teamWins = dict([(i, 0) for i in teams])
    for i in divGames:
        if(i[0] in teams):
            teamWins[i[0]] += 1
    ###Teams with the most division wins
    stillIns = [i for i in teamWins if teamWins[i] == max(teamWins.values())]            
    return stillIns

def loadGames(startWeek, year):
    """Loads all games except startWeek"""
    print("Loading Game Data (~30s) ", end='')
    allWeeks = Train.getYear(year, True)
    print()
    return allWeeks

def randomWinner(predWin, predLose, chance):
    """Returns the winner of the game. There is a chance% chance that predWin will win"""
    ###Chance is usually rounded to the tenth, so this is too
    outcome = random.randint(0, 1000)/10
    if(outcome < chance):
        ###99.9% chance will almost always be right, since 0-99 < 99
        return [predWin, predLose]
    return [predLose, predWin]

def rankWinners(divWinners, conf, league):
    """Ranks the division winners."""
    ###Sorts them in reverse order based on their record, but doesn't do anything about ties
    sortWinners = sorted(divWinners, key=lambda x:league[0][x], reverse=True)
    rank = []
    while(len(rank) < len(divWinners)):
        nextWin = tiebreaker(sortWinners, league, division=conf)
        rank.append(nextWin)
        sortWinners.remove(nextWin)
    
    return rank

def seeding(league, sixTeam):
    """Returns the afc and nfc playoff teams sorted by seed"""
    ###Find division winners, separate by conference
    divWinners = divisionWinners(league)
    afcPlayoffs, nfcPlayoffs = divWinners[:4], divWinners[4:]
    ###Sort by seed
    afcPlayoffs = rankWinners(afcPlayoffs, Base.AFC, league)
    nfcPlayoffs = rankWinners(nfcPlayoffs, Base.NFC, league)
    ###Find wildcards and add to the end
    t = afcPlayoffs.copy()
    q = nfcPlayoffs.copy()
    afcPlayoffs.extend(wildCards(afcPlayoffs, Base.AFC, league, sixTeam))
    nfcPlayoffs.extend(wildCards(nfcPlayoffs, Base.NFC, league, sixTeam))

    return afcPlayoffs, nfcPlayoffs

def tiebreaker(teams, league, division=None):
    """Settles the tie between teams. division is the list of teams in the division/Conference for wildcards"""
    teamRecords = [league[0][i] for i in teams]
    teams = [i for i in teams if league[0][i] == max(teamRecords)] 
    if(len(teams) == 1):
        return teams[0]

    sched = league[1]
    funcs = [lambda:inDivWins(teams, teams, sched), lambda:inDivWins(teams,division, sched),
             lambda:commonGames(teams, sched)]
    for i in funcs:
        teams = i()
        if(len(teams) == 1):
            return teams[0]

    return random.choice(teams)

def wildCards(divWinners, confTeams, league, sixTeam):
    """Returns wildcard teams, ranked by seed"""
    numWilds = 2 if sixTeam else 3
    wilds = []
    for i in confTeams:
        if(not(i in divWinners)):
            wilds.append((i, league[0][i]))
    ###Wildcards are the two/three best teams
    wilds = sorted(wilds, key=lambda x:x[1], reverse=True)
    ###This only keeps teams with the same number of wins as wilds[0] or wilds[1]
    if(sixTeam): bestRecords = [wilds[0][1], wilds[1][1]]
    ###Add the third wildcard if there are seven teams
    else: bestRecords = [wilds[0][1], wilds[1][1], wilds[2][1]]
    wilds = [i[0] for i in wilds if(i[1] in bestRecords)]
    
    finalWilds = []
    t = wilds.copy()
    while(len(finalWilds) < numWilds):
        nextWin = tiebreaker(wilds, league, division=confTeams)
        finalWilds.append(nextWin)
        wilds.remove(nextWin)

    return finalWilds
