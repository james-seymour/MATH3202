from gurobipy import *

# Sets
I = range(3)
L = range(8)
C = range(25)

# Data
IDtoLVC = [[43.3, 83.2, 7.8, 63.4, 60.3, 59.3, 44.7, 37.0],
           [80.6, 64.5, 52.7, 77.2, 5.0, 41.5, 15.3, 58.1],
           [42.4, 23.4, 61.9, 16.2, 71.6, 26.0, 61.8, 30.5]]

CCDPop = [
    4426, 6527, 6821, 5566, 6164, 5002, 6377, 4747, 5992, 3517, 4602, 4135,
    4097, 4296, 5379, 4368, 4304, 4496, 5884, 4222, 5135, 4325, 3861, 5128,
    5384
]

CCDtoLVC = [[0, 0, 17.7, 0, 0, 0, 0, 48.9], [0, 0, 11.6, 0, 0, 0, 29.0, 0],
            [0, 0, 22.2, 0, 0, 0, 21.2, 0], [0, 0, 0, 0, 11.0, 0, 9.2, 0],
            [0, 0, 0, 0, 10.9, 0, 24.2, 0], [37.5, 0, 22.7, 0, 0, 0, 0, 0],
            [0, 0, 8.0, 0, 0, 0, 0, 25.7],
            [0, 0, 24.1, 0, 0, 29.3, 21.9, 25.0],
            [0, 0, 0, 0, 20.8, 25.9, 14.4, 0], [0, 0, 0, 0, 17.8, 0, 27.2, 0],
            [10.8, 0, 0, 0, 0, 0, 0, 23.2], [15.2, 0, 0, 28.9, 0, 0, 0, 8.9],
            [0, 0, 0, 0, 0, 12.4, 0, 23.0], [0, 0, 0, 0, 0, 12.9, 33.0, 0],
            [0, 0, 0, 0, 35.3, 21.0, 0, 0], [5.4, 0, 0, 0, 0, 0, 0, 28.7],
            [24.2, 0, 0, 17.4, 0, 30.0, 0, 10.3],
            [0, 27.2, 0, 20.5, 0, 18.3, 0, 22.5],
            [0, 11.5, 0, 30.9, 0, 17.9, 0, 0], [0, 16.3, 0, 0, 0, 23.9, 0, 0],
            [23.0, 0, 0, 19.3, 0, 0, 0, 0], [0, 0, 0, 6.2, 0, 0, 0, 33.5],
            [0, 27.8, 0, 20.5, 0, 0, 0, 0], [0, 9.5, 0, 0, 0, 36.2, 0, 0],
            [0, 14.4, 0, 0, 0, 35.6, 0, 0]]
LVCUCost = [
    1208000, 1770000, 1954000, 1171000, 1601000, 1736000, 1604000, 1136000
]
LVCSCost = [
    5303000, 4973000, 5558000, 4761000, 5066000, 4290000, 3048000, 5943000
]

IDCost = [109, 160, 168]
DeliveryCost = 0.2 # per km
AccessCost = 1.0 # per km

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

m = Model("Vaccine Distribution Strategy")

# Variables

# X[i,l] is amount to send from ID i to LVC l
X = { (i,l): m.addVar() for i in I for l in L}

# Y[c,l] is people for CCD c to send to LVC l
Y = { (c,l): m.addVar() for c in C for l in L}

#Binary variable for upgrading or not
u = {(l): m.addVar(vtype=GRB.BINARY, name="u") for l in L}

#Binary variables for shutting an LVC
s = {(l): m.addVar(vtype=GRB.BINARY, name="s") for l in L}

Ybin = { (c,l): m.addVar(vtype=GRB.BINARY, name="y") for c in C for l in L }

# Objective - updated for communication 7
m.setObjective(quicksum((IDCost[i] + DeliveryCost*IDtoLVC[i][l])*X[i,l] for i in I for l in L) +
	quicksum(AccessCost*CCDtoLVC[c][l]*Y[c,l] for c in C for l in L) + quicksum(LVCUCost[l]*u[l] - LVCSCost[l]*(1-s[l]) for l in L), GRB.MINIMIZE)

# Constraints

# Balance at each LVC
for l in L:
	m.addConstr(quicksum(X[i,l] for i in I) == quicksum(Y[c,l] for c in C))

# Meet population demands
for c in C:
	m.addConstr(quicksum(Ybin[c,l] * Y[c,l] for l in L) == CCDPop[c])

	
# If no connection then Y must by 0
for c in C:
	for l in L:
		if CCDtoLVC[c][l] == 0:
			m.addConstr(Y[c,l] == 0)


			
# Communication 2 - Limit capacities of IDs and LVCs (Updated with Comm 6 values)

IDMax = 50000
LVCMax = 15000

for i in I:
	m.addConstr(quicksum(X[i,l] for l in L) <= IDMax)


# Communication 6/7 - Upgrading LVC's
UpgradeCapacity = 7500



# limiting people from ccd to lvc
for l in L:
    m.addConstr(quicksum(Y[c,l] for c in C) <=  s[l]*(LVCMax + u[l]*UpgradeCapacity))

m.addConstr(quicksum(CCDPop[c] for c in C) == quicksum(quicksum(X[i,l] for l in L) for i in I))

for c in C:
    for l in L:
        m.addConstr(Y[c,l] >= 0)

#Communication 8

for c in C:
    m.addConstr(quicksum(Ybin[c,l] for l in L) == 1)

m.optimize()


