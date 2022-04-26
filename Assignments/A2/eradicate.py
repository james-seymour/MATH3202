from gurobipy import *
from functools import reduce
import operator

Probs = [0.95,0.975,0.99,0.995]

ECost = [
[57000,136000,226000,454000],
[55000,127000,252000,412000],
[64000,102000,214000,472000],
[68000,113000,202000,470000],
[64000,136000,201000,454000],
[67000,114000,231000,401000],
[58000,109000,257000,473000],
[52000,138000,231000,480000],
[65000,123000,245000,413000],
[62000,134000,246000,426000],
[54000,117000,222000,471000],
[54000,103000,201000,426000],
[59000,140000,206000,447000],
[50000,136000,227000,428000],
[70000,136000,229000,414000],
[68000,103000,228000,413000],
[55000,116000,248000,459000],
[57000,140000,218000,454000],
[69000,114000,213000,449000],
[58000,121000,252000,416000],
[70000,139000,260000,459000],
[69000,105000,213000,439000],
[64000,136000,246000,411000],
[59000,124000,242000,404000],
[62000,127000,212000,475000]
]

C = range(25)
O = range(4)

model = Model()
model.params.NonConvex = 2

X = model.addVars(C, O, vtype=GRB.BINARY)

model.setObjective(quicksum(ECost[c][o] * X[c, o] for c in C for o in O))

# Only one option picked
for c in C:
   model.addConstr(quicksum(X[c, o] for o in O) == 1) 

model.optimize()


prob_vars = model.addVars(C) # Set each chosen prob to an auxiliary var
for c in C:
    prob = quicksum(X[c, o] * Probs[o] for o in O)
    model.addConstr(prob_vars[c] == prob)

def cumulative_multiply(current_var, next_prob):
    next_var = model.addVar()
    model.addConstr(next_var == current_var * next_prob)
    return next_var

final_prob_var = reduce(cumulative_multiply, prob_vars.values())
model.addConstr(final_prob_var >= 0.8)

model.optimize()

