# NFL Model
####About
This program predicts NFL games, as well as other things related to NFL games.
### Game
Game.py has methods that have to do with NFL games during the game. It includes getting the data, and predicting. It uses regB. 
### Injury
Injury.py has methods that have to do with getting injury data. It is not used to predict anything.
### nflPredict
nflPredict.py has constants and other things like that. 
### Plays
Plays.py has methods that have to do with finding the best play type for a certain play. It uses regH and regI
### Prediction
Prediction.py predicts games before they start, using team ratings and injuries. It uses regD.
### Ratings
Ratings.py has methods that read and write to the ratings file, and calculate the new ratings for teams after a game.
### Season
Season.py has methods that simulate and predict division winners, conference winners, and Super Bowl winners for the entire season.
### Train
Train.py has methods for training new models. It is used to get game data. 
### Update
Update.py has methods to update after a week. It updates the team ratings

#### Running
Running Update.py gives you access to all other files. Otherwise you will need to import them. 


#### Regression_Models.pkl
There are 5 models in the Regression_Models.pkl
## regE 
Inputs: All-Time Difference,Season Difference 
Outputs: Win/Loss (and `.predict_proba` to get win percentage)
Neural Network (MLP Classifier)   
~66% accurate

## regD:
Inputs: All-Time Difference, Season Difference, Difference of injury for each position
Outputs: Win Percentage
Injuries used are: QB, RB, WR, TE, T, G, C, DT, DE, LB, CB, S
Bayesian Ridge Regression  
~67.5% accurate

## regB:
Inputs: All-Time Difference, Season Difference, Seconds Left, Start Yard, Point Difference
Outputs: Win/Lose, (and `.predict_proba` for percent chance)
Seconds Left starts at 3600 and goes to 0 (and negative in overtime)
Neural Network (MLP Classifier)

## regH:
Inputs: Home/Away, Down, To Go, Yard, Away Points, Home Points
Outputs: Finds best play type for the next play (as in most realistic)
Neural Network (MLP Classifier) 
~70% accurate (70% of the time it chose the play type that was actually chosen, not necessarily the best one)

## regI:
Inputs: Seconds Passed, Down, To Go, Yard, Team Score, Opp. Score, Pass?, Run?, FG?, PAT?, 2PT?
Outpts: Finds Yards Gained and Points Gained
Pass, Run, FG, PAT, 2PT give the play type. One of them is 1, the others are 0
Ridge Regression. (85.9 Mean squared error for Yards, 1.07 Mean Squared Error for Points)

#### Old Models
The first model predicted a point margin, with a simple linear model.
* RATING_COEF = 4.73
* INJURY_COEF = -3.26
  * Calculating the injury value was different too (fourth bullet)
* INTERCEPT = -0.67
* To Calculate the injury value, the number of injuries were multiplied by special values
  * Each Position had a special number
  * QB: 4, LB: 3,
  * CB and WR: 2, and everything else was 1
  * The numbers were random, and the injury values were substracted.
  * A bigger injury value means that team had more injuries than the other
* RATING_PERCENT = 1.6468
  * Turns the points into a percentage. It didn't work too well. 
* SEASON_PERCENT = 1.2798
* INJURY_PERCENT = 1.2

 - [ ] Create a model that predicts how good a game is going to be (using attendance, or tv ratings)
   - It would take in team ratings, the week/playoff round, and other things
 - [ ] Use Season to Season roster changes to change team ratings