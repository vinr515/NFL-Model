import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import random
import matplotlib.pyplot as plt
import optimizeAlpha as alpha
import seaborn as sns
import pickle
from copy import deepcopy

LEARNING_RATE = 0.01
MOMENTUM = 0
EPOCHS = 100
BATCH_SIZE = 100

data = alpha.getRows()
ratingsList = alpha.findRatings(data)
finalData = alpha.addRatings(data, ratingsList)
finalData = alpha.doubleData(finalData)
train, validate, test = alpha.splitData(finalData)

total = train + validate
random.seed(50)
random.shuffle(total)
train, validate = total[:-1024], total[-1024:]

trainX, trainY = alpha.xyData(train)
valX, valY = alpha.xyData(validate)
testX, testY = alpha.xyData(test)

trainX, valX, testX = torch.Tensor(trainX), torch.Tensor(valX), torch.Tensor(testX)
trainY, valY = torch.Tensor(trainY).view(-1, 1), torch.Tensor(valY).view(-1, 1)
testY = torch.Tensor(testY).view(-1, 1)

SIZE = trainX.size(0)

class Net(nn.Module):
    def __init__(self, input_dim = 14, output_dim=1):
        super(Net, self).__init__()
        self.lin1 = nn.Linear(input_dim, 20)
        self.lin2 = nn.Linear(20, output_dim)

    def forward(self, x):
        x = self.lin1(x)
        x = torch.sigmoid(x)
        x = self.lin2(x)
        return x

with open('BestModel.pkl', 'rb') as f:
    allObjects = pickle.load(f)

oldPercs = [i for i in allObjects if (type(i) == int or type(i) == float)]
oldWorst = min(oldPercs)
if(oldWorst < 1):
    oldWorst *= 100
HOLD_MODELS = []

def zeroWeights(model):
    for i in model.modules():
        if(isinstance(i, nn.Linear)):
            i.weight.data.normal_(0, 1)

def accuracy(model, X, Y):
    score = 0
    valSteps = X.size(0)
    for i in range(valSteps):
        xVal, yVal = Variable(X[i], requires_grad=False), Variable(Y[i], requires_grad=False)
        yPred = model(xVal)
        if((yPred > 0.5) == (yVal > 0.5)):
            score += 1

    return score/valSteps

def writeModels(modList):
    with open('BestModel.pkl', 'wb') as f:
        pickle.dump(modList, f)

def plotAccuracy(trainAcc, valAcc):
    xVals = [i for i in range(EPOCHS) if i%5 == 0][:len(trainAcc)]
    sns.regplot(xVals, trainAcc, color='blue', label='Training Accuracy', lowess=True)
    sns.regplot(xVals, valAcc, color='green', label='Validation Accuracy', lowess=True)
    plt.legend()
    plt.title('Model Accuracy')
    plt.xlabel('Epoch Number')
    plt.ylabel('% Correct')
    plt.show()

def startModel(model, lossFunction, optimizer):
    bestModel, bestAcc = None, 0.0
    note = int(EPOCHS/10)

    #allTrain, allVal = [], []
    for i in range(EPOCHS):
        model = trainModel(BATCH_SIZE, model, optimizer, lossFunction)
        if(i%5 == 0):
            trainAcc, valAcc = accuracy(model, trainX, trainY), accuracy(model, valX, valY)
            if(valAcc > bestAcc):
                bestAcc = deepcopy(valAcc)
                bestModel = deepcopy(model)
            #allTrain.append(trainAcc)
            #allVal.append(valAcc)
        if(i%note == 1):
            print('.', end='')
    print()
    #plotAccuracy(allTrain, allVal)

    return bestModel, bestAcc

def trainModel(batchSize, model, optimizer, lossFunction):
    for i in range(batchSize):
        index = np.random.randint(SIZE)
        xVar = Variable(trainX[index], requires_grad=False)
        yVar = Variable(trainY[index], requires_grad=False)

        optimizer.zero_grad()
        yPred = model(xVar)
        loss = lossFunction.forward(yPred, yVar)
        loss.backward()
        optimizer.step()

    return model
        

model = Net()
zeroWeights(model)

lossFunction = nn.MSELoss()
#optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=MOMENTUM)
hyperParams = [(0.1, 0, 500, optim.SGD(model.parameters(),lr=0.1), nn.MSELoss()),
(0.01, 0, 500, optim.SGD(model.parameters(),lr=0.01), nn.MSELoss()),
(0.001, 0, 500, optim.SGD(model.parameters(),lr=0.001), nn.MSELoss()),
(0.0001, 0, 500, optim.SGD(model.parameters(),lr=0.0001), nn.MSELoss()),
(0.00001, 0, 500, optim.SGD(model.parameters(),lr=0.00001), nn.MSELoss()),
(0.1, 0.5, 500, optim.SGD(model.parameters(),lr=0.1,momentum=0.5), nn.MSELoss()),
(0.01, 0.5, 500, optim.SGD(model.parameters(),lr=0.01,momentum=0.5), nn.MSELoss()),
(0.001, 0.5, 500, optim.SGD(model.parameters(),lr=0.001,momentum=0.5), nn.MSELoss()),
(0.0001, 0.5, 500, optim.SGD(model.parameters(),lr=0.0001,momentum=0.5), nn.MSELoss()),
(0.00001, 0.5, 500, optim.SGD(model.parameters(),lr=0.00001,momentum=0.5), nn.MSELoss()),
(0.1, 0.9, 500, optim.SGD(model.parameters(),lr=0.1,momentum=0.9), nn.MSELoss()),
(0.01, 0.9, 500, optim.SGD(model.parameters(),lr=0.01,momentum=0.9), nn.MSELoss()),
(0.001, 0.9, 500, optim.SGD(model.parameters(),lr=0.001,momentum=0.9), nn.MSELoss()),
(0.0001, 0.9, 500, optim.SGD(model.parameters(),lr=0.0001,momentum=0.9), nn.MSELoss()),
(0.00001, 0.9, 500, optim.SGD(model.parameters(),lr=0.00001,momentum=0.9), nn.MSELoss()),
(0.00001, 0.99, 500, optim.SGD(model.parameters(), lr=0.00001, momentum=0.99), nn.MSELoss())]


for i in hyperParams:
    LEARNING_RATE = i[0]
    MOMENTUM = i[1]
    EPOCHS = i[2]
    optimizer = i[3]
    lossFunction = i[4]
    bestModel, bestAcc = startModel(model, lossFunction, optimizer)
    newAcc = accuracy(bestModel, trainX, trainY)
    
    print("{}% and {}%".format(bestAcc*100, newAcc*100), end='  ')
    if(bestAcc >= oldWorst):
        print("Better")
    else:
        print("Worse")
    HOLD_MODELS.append((bestModel, bestAcc, newAcc))
    

    

print()
for i in range(0, len(allObjects), 2):
    print('Previous Accuracy: {}%  '.format(allObjects[i+1]*100))
    
print('Current Accuracy: {}%  '.format(bestAcc*100))

"""
Learn. | Moment. | Epoch | Optim. | Loss. | Layers | Layer ... | Val %
0.0001 | 0 | 500 |  SGD | MSE | 3 | 14,20,1 | 65%
0.1 | 0 | 500 | SGD | MSE | 3 | 14,20,1 | 50%
0.01 | 0 | 500 | SGD | MSE | 3 | 14,20,1 | 66.2%
0.001 | 0 | 500 | SGD | MSE | 3 | 14,20,1 | 61%
0.0001 | 0 | 500 | SGD | MSE | 3 | 14,20,1 | 61%
0.00001 | 0 | 500 | SGD | MSE | 3 | 14,20,1 | 56%
0.001 | 0.5 | 500 | SGD | MSE | 3 | 14,20,1 | 61%
0.01 | 0.5 | 500 | SGD | MSE | 3 | 14,20,1 | 64.2%
0.1 | 0.5 | 500 | SGD | MSE | 3 | 14,20,1 | 50%
0.0001 | 0.5 | 500 | SGD | MSE | 3 | 14,20,1 | 55%
0.0001 | 0.9 | 500 | SGD | MSE | 3 | 14,20,1 |65.8%
0.001 | 0.9 | 500 | SGD | MSE | 3 | 14,20,1 | 64.6%
0.01 | 0.9 | 500 | SGD | MSE | 3 | 14,20,1 | 64.0%
0.0001 | 0.99 | 500 | SGD | MSE | 3 | 14,20,1 | 66.2%
----------------------------------------------------
0.01 | 0 | 100 | SGD | MSE | 3 | 14,20,1 | 64.0%
0.01 | 0 | 200 | SGD | MSE | 3 | 14,20,1 | 62.6%
0.01 | 0 | 750 | SGD | MSE | 3 | 14,20,1 | 64.6%
0.01 | 0 | 1000 | SGD | MSE | 3 | 14,20,1 | 65.2%
0.001 | 0.5 | 100 | SGD | MSE | 3 | 14,20,1 | 64.4%
0.001 | 0.5 | 200 | SGD | MSE | 3 | 14,20,1 | 64.0%
0.001 | 0.5 | 750 | SGD | MSE | 3 | 14,20,1 | 66.0%
0.001 | 0.5 | 1000 | SGD | MSE | 3 | 14,20,1 | 64.4%
0.0001 | 0.9 | 100 | SGD | MSE | 3 | 14,20,1 | 65.2%
0.0001 | 0.9 | 200 | SGD | MSE | 3 | 14,20,1 | 63.6%
0.0001 | 0.9 | 750 | SGD | MSE | 3 | 14,20,1 | 64.2%
0.0001 | 0.9 | 1000 | SGD | MSE | 3 | 14,20,1 | 65.4%
-----------------------------------------------------
0.01 | 0 | 500 | Adadelta | MSE | 3 | 14,20,1 | 56.4%
0.01 | 0 | 500 | Adam | MSE | 3 | 14,20,1 | 65.2%
0.01 | 0 | 500 | ASGD | MSE | 3 | 14,20,1 | 66.4%
0.01 | 0 | 500 | RMSprop | MSE | 3 | 14,20,1 |  65.8%
0.001 | 0.5 | 750 | Adadelta | MSE | 3 | 14,20,1 | 62.7%
0.001 | 0.5 | 750 | Adam | MSE | 3 | 14,20,1 | 66.6%
0.001 | 0.5 | 750 | ASGD | MSE | 3 | 14,20,1 | 66.0%
0.001 | 0.5 | 750 | RMSprop | MSE | 3 | 14,20,1 |  65.8%
0.0001 | 0.9 | 500 | Adadelta | MSE | 3 | 14,20,1 | 65.0%
0.0001 | 0.9 | 500 | Adam | MSE | 3 | 14,20,1 | 64.8%
0.0001 | 0.9 | 500 | ASGD | MSE | 3 | 14,20,1 | 64.3%
0.0001 | 0.9 | 500 | RMSprop | MSE | 3 | 14,20,1 | 64.8%
-------------------------------------------------------
0.01 | 0 | 500 | ASGD | L1 | 3 | 14,20,1 | 67.2%
0.01 | 0 | 500 | SGD | L1 | 3 | 14,20,1 | 66.4%
0.001 | 0.5 | 750 | ASGD | L1 | 3 | 14,20,1 | 66.4%
0.001 | 0.5 | 750 | SGD | L1 | 3 | 14,20,1 | 66.6%
--------------------------------------------------------
0.01 | 0 | 500 | ASGD | L1 | 3 | 14,5,1 | 67.3%
0.01 | 0 | 500 | ASGD | L1 | 3 | 14,10,1 | 66%
0.01 | 0 | 500 | ASGD | L1 | 3 | 14,14,1 | 67.1%
0.01 | 0 | 500 | ASGD | L1 | 3 | 14,28,1 | 65.8%
0.001 | 0.5 | 750 | SGD | L1 | 3 | 14,5,1 | 68.5%
0.001 | 0.5 | 750 | SGD | L1 | 3 | 14,10,1 | 64.8%
0.001 | 0.5 | 750 | SGD | L1 | 3 | 14,14,1 | 63.5%
0.001 | 0.5 | 750 | SGD | L1 | 3 | 14,28,1 | 62.1%
--------------------------------------------------------
0.01 | 0 | 500 | ASGD | L1 | 2 | 14,1 | 65.4%
0.001 | 0.5 | 750 | SGD | L1 | 2 | 14,1 | 65.8%
-------------------------------------------------------
0.01 | 0 | 500 | ASGD | L1 | 3 | 14,20,1 + ReLU | 64%
0.001 | 0.5 | 750 | SGD | L1 | 3 | 14,20,1 + ReLU | 65.8%
-------------------------------------------------------
0.001 | 0.5 | 750 | SGD | L1 | 3 | 14,6,1 | 
"""
