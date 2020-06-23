# NFL Model
"""Regression_Models.pkl
5 models in the order: regE, regD, regB, regH, regI
regE: AT Difference,Season Difference.predict_proba(x) finds Percent Chances/100
Neural Network (MLP Classifier)   ~66% accurate

regD: AT Difference, Season Difference, Difference of Injuries (all positions/12 Fields)
finds Percent Chances/100
Bayesian Ridge Regression  ~67.5% accurate

regB: AT Difference, Season Difference, Seconds Left, Start Yard, Point Difference
finds Percent Chances in game/100
Neural Network (MLP Classifier)  Accurate

regH: Home/Away, Down, To Go, Yard, Away Points, Home Points
finds Percent Chance of each play type (FG, Kickoff, Kneel, PAT, Pass, Punt, Run, 2PT)
Neural Network (MLP Classifier) ~70% accurate

regI: Seconds Passed, Down, To Go, Yard, Team Score, Opp. Score, Pass?, Run?, FG?, PAT?, 2PT?
Finds Yards Gained and Points Gained
Pass, Run, FG, PAT, 2PT give the play type. One of them is 1, the others are 0
Ridge Regression. (85.9 MSE for Yards, 1.07 MSE for Points)

(Prediction with only Rating)*RATING_PERCENT turns into a chance of winning
If Prediction is .5, .5*6.25=3.125, or 53.125%
!----->Obsolete<-----!
RATING_PERCENT = 1.6468

Like RATING_PERCENT, but for predictions with season rating
Train: 0.6131 (85% of data). Test: 1.2798 (15% of data)
!----->Obsolete<-----!
SEASON_PERCENT = 1.2798

Like RATING_PERCENT, but for predictions with injuries
!----->Obsolete<-----!
INJURY_PERCENT = 1.2

HF for Season and Rating is 0.0, 1.2
So add 0 to all-time rating, 1.2 to season rating
Percent correct is 64.3%
!----->Obsolete<-----!
HF_ADVANTAGE = 3

+5% for the home team
!----->Obsolete<-----!
RATE_HFA = 5

New coefficients. 1st docstring. Includes Injuries
!----->Obsolete<-----!
RATING_COEF = 4.73
INJURY_COEF = -3.26
INTERCEPT = -0.67
The weight each position has on injuries. Not based on anything, just picked random numbers
!----->Obsolete<-----!
POS_POINTS = {"QB":4, "RB":1, "WR":2, "TE":1, "LT":1, "T":1, "LG":1, "G":1, "C":1, "RG":1, "RT":1
              , "DT":1, "NT":1, "DE":1, "LB":3, "CB":2, "SS":1, "FS":1, "S":1}

HF_ADVANTAGE recheck
 | Try every .1, see which one works the best
 | (add .5 for home team, 1, 1.5, 2 ...)

Find how good a game is
 | Based on team ratings, week, and tv ratings/attendance
 | X: Win Percentage, Week, Rivalry, Time, Records
 | Y: Attendance, TV
 
Season to Season roster change
 | Only check the first few games. Would be like injury weights
 | (ex. 1 new QB, 1 new WR, 1 new DT: multiply by POS_POINTS, see how it affects the first few weeks

Head Coach Change
 | Like Season to Season change, but with one position
 | Could be merged with Season to Season

Rating Map
 | Based on each county
 | Depends gives each team a score based on distance to county and rating
 | The highest score gets that county
 | Color in on map


Graph every point on a all-time rating (x) season rating (y) graph 
For every x (all-time rating) value, go through the y values. 
Find the percent of games won above and below that y value. 
Find the y value for each x with  a certain percent (ex. 95% win) 
Connect the points to make line. 
Do the same for lose. 
If it is less than the lose line, they will lose
...       more ...     win line ...         win

THINGS TRIED ALREADY:
Predictions with only Season
 | No All-Time Ratings, but includes the actual rating (e.x 500)
 | Graph looked linear
 | Rating coefficient and Intercept were 0, so
 | It was only the Season Difference
 | Which predicted a win 62.5% correctly,
 | Worse than predicting with only Ratings

Predict with Rating, Season again
 | This time, make points negative, no wins
 | (Like when predicting with only Season ratings)
 | Week 1 games with no season rating difference were excluded
 | Predicted a win 63% correctly
 | Worse than predicting with only Ratings

Do one line for Rating, Season
 | Find a line y = mx + b where x is the all-time rating
 | And y is the season rating
 | If the actual season rating is higher than the predicted
 | It's a win, else lose
 | Worked, but only predicted 62% correctly
 | Worse than predicting with only Ratings

Predict with Season, Home Field
 | 61.2%
 | Season Difference Coef: 11.39930865
 | Home Field Advantage Coef: 60.75227285
 | Intercept: -30.37613642728481

Season, Home Field, and Actual rating
 | 61% regularly.
 | 1st way, used 3 regressions. 61.2%, not good enough
 | Second way, 2 regressions, tried all for the HFA
 | HFA was 0.1 but didn't make much of a difference.
 | 61.2%, but 61.9% when only looking at away teams
 | Rating Coef: -4.13017610e-04
 | Difference Coef: 1.13995152e+01
 | HFA Coef: 6.07522728e+01
 | Intercept: -30.16964298483608
 | ---------------------------------
 | Rating Coef: -9.89734633e-04
 | Difference Coef: 2.02768500e+01
 | Intercept: 0.49483045132021075
 | Add .1 to rating if Home Field 
 
Predict with Rating, Season again
 | This time, include the actual rating
 | Which means there would be four variables
 | But the ratings could go away as 0s.
 | Was reg, logistic regression
 | 63% accuracy, but no way to make it into percent

Logistic Regression
 | But with Won, Loss, Tied instead of point difference
 | Goes straight to percent
 | One with Logistic Regression did fine for wins
 | But most %s went to min or max, 23% and 78%
 | Done with Linear Regression, Actually works
 | +5% HFA for Linear Regression, 64% accuracy.
 | Good for non-injuries, used as the current regression model

Redo injury without *,+
 | Multiply each injury by POS_POINTS, subtract team injuries, plot points
 | And do stuff.
 
Redo everything with Ratings, Season Ratings, and Injuries
 | Ratings and Season Ratings could be one variable with RATE_COEF/SEASON_COEF
 | ~67.5%. Predicts percentage, but using linear model

Injury severity 
 | Not enough data

1. Load week data
2. Use pointsList and writePoints to save data to dataCollect.csv
3. Find current Power Rankings of Teams
4. Find current Season Rankings
5. Change Team Ratings
6. Change Season Ratings
7. Find new Power rankings
8. Find new Season Rankings
9. Change power file
10. Predict and find injuries with severity, using findData()
11. load severity to datacollect file (copy output onto the file)
12. Load predictions onto pickem and guiText.txt (win,lose,home,percent)
13. Load Season Predictions onto guiText.txt
14. Load results onto guiText.txt
15. Update team list below
16. Update team list below
17. SAVE TEAM RATINGS TO nflRatings.csv using Ratings.writeRatings()
18. 12
19. 13
20. 14, just in case

Won more
Cardinals,Browns,Broncos,Packers,Jaguars,Dolphins,Jets,Raiders.
Bills, Texans, Redskins tied

Took all the data from 2016 to 2018 (inclusive). With Ratings, Injuries and Points
Then went through, keeping rows with the same point difference together
Then the means of all the ratings and injuries were taken.
So there were about 80 or so rows now, one for every point difference in a game
A two line regression was done.
Intercept: -0.67
Rating Coefficient: 4.73
Injury Coefficient: -3.26
r^2 using a different test set (15 of the 83, 68 were originally used for training) was 0.743
r^2 using the same 68 rows was 0.75
Also, both of them stayed as a line from about y=-30 to y=30

In total, r^2 was .1 higher than just the rating
y = 4.73*Ratings + -3.26*Injuries - 0.67

Injuries are your injuries - their injuries. (If A has injury score of 5 and B
has 15, for A injury difference would be -10, so a smaller number is better
which is why there is a negative slope

r^2 for linear was .9557
To find the cubic function:
def makeFunc(numDiv, totDiv):
    return lambda x:((x/numDiv)**3)/totDiv

Loop through a few numbers, :
cube = makeFunc(i, 10) or makeFunc(5, i)
thisScore = r2_score(blowoutY, cube(blowoutX))

Scores added to list, highest score chosen.
r^2 was still only 0.656 though

To find an equation, all regular season games from 2000 to 2015 (inclusive)
Were plotted.  The means and medians were taken, and graphed.
There were two parts, the middle (-15 < x < 15) which was linear.
A linear regression was done, and COEF and INTERCEPT were found
For other games, the line was cubic. The equation used was:
y = ((x^3)/NUM_DIVIDE)/TOT_DIVIDE. A loop through one decimal point was used
To find which two numbers worked to get the highest r^2 score (At the bottom)

To find RATING_PERCENT
all games were taken from 2000 to 2018 inclusive.
The Rating Difference and winner were taken for each team from each game.
The Rating Difference was rounded to the nearest .5
All games with the same rating difference were grouped,
and the percent of games won with each rating difference was found:
(rating difference of -0.5 won games 49.07% of the time, for example).
Then linear regression was done to get:
coef_ = RATING_PERCENT
intercept_ = ~50

When using RATING_PERCENT, you don't need to round because it was only rounded
to make it easier.
There are more games with a rating difference of -0.5 when rounded then there
are of -0.1.

The intercept means that two evenly matched teams split their games

Rating and Season Rating Regression Done:
Plotting all the train data (7756 vs 1940 train points):
Graph was wide, but season points was steeper
Mean and median was taken of every y value (point difference) in the dataset
Plotted:
Mean looked like a line, with outliers where the point difference was very large
Median had the same slope, but was still really wide, so it was tossed out
Only using the mean now.
Remove the outliers by y value (All points with a y value < -35 or > 35 were a problem)
This way the datasets still had the same number of elements
Plot, regress, and find.

r^2 on the train data set was 0.96. r^2 on the test has no use
since it's too varied. Instead, we found that 64.3% of games were predicted right
compared to  62% of games. It still couldn't predict the actual score correctly.


Load all data from dataHold.csv
Separate into different columns
Make three columns: Difference of Rating, Difference of Season, Difference of Points
Graph
Train test split
Go through the data and take the mean and median (one each), so it would be
(x1+x2...)/number of x, y.
Graph, it should look more linear
Take out outliers, it should be more linear
Do another mean with y's if needed
Use sklearn