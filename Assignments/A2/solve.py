from collections import defaultdict
from typing import Generator, Tuple, Union
from gurobipy import Model, GRB, TempConstr, Var, tupledict, quicksum, max_, min_
from itertools import product, chain
from vaccine2 import (
    # Var definitions
    weeks,
    IDs,
    LVCs,
    CCDs,

    # Cost definitions
    ID_costs,
    IDtoLVC_costs,
    CCDtoLVC_costs,
    hello,

    # Constraint definitions
    CCD_pops,

    # Communication constraint constants
    COMM6_ID_MAX,
    COMM6_LVC_MAX,
)

# Type defs

Gurobi_DecisionVar_Dict = tupledict[Tuple[str, ...], Union[Var, int]]
Gurobi_Constraint_Gen = Generator[TempConstr, None, None]

## Setup model, variables and objective

model = Model()

ID_vars: Gurobi_DecisionVar_Dict = model.addVars(weeks, IDs) # Number of vaccines sent to each ID
IDtoLVC_vars: Gurobi_DecisionVar_Dict = model.addVars(weeks, IDs, LVCs) # Number of
# Use sparse variable creation here, as a 0 cost CCDtoLVC is inaccessible. Then wrap in a defaultdict to return 0 if key doesnt have val
CCDtoLVC_vars: Gurobi_DecisionVar_Dict = defaultdict(int,
    model.addVars(filter(lambda var_key: CCDtoLVC_costs[var_key] > 0, product(weeks, CCDs, LVCs)))
) # Number of people at each CCD to be vaccinated at each LVC

total_ID_cost = quicksum(ID_costs[var_key] * gurobi_var for var_key, gurobi_var in ID_vars.items())
total_IDtoLVC_cost = quicksum(IDtoLVC_costs[var_key] * gurobi_var for var_key, gurobi_var in IDtoLVC_vars.items())
total_CCDtoLVC_cost = quicksum(CCDtoLVC_costs[var_key] * gurobi_var for var_key, gurobi_var in CCDtoLVC_vars.items())

total_cost = total_ID_cost + total_IDtoLVC_cost + total_CCDtoLVC_cost

model.setObjective(total_cost, GRB.MINIMIZE)

### Communication 6



















