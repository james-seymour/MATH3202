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
    LVC_upgrade_costs,

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
# LVC_upgrade_vars: Gurobi_DecisionVar_Dict = model.addVars(weeks, LVCs, vtype=GRB.BINARY) # Binary decision variables to upgrade the LVC
LVC_upgrade_vars: Gurobi_DecisionVar_Dict = model.addVars(LVCs, vtype=GRB.BINARY)

total_ID_cost = quicksum(ID_costs[var_key] * gurobi_var for var_key, gurobi_var in ID_vars.items())
total_IDtoLVC_cost = quicksum(IDtoLVC_costs[var_key] * gurobi_var for var_key, gurobi_var in IDtoLVC_vars.items())
total_CCDtoLVC_cost = quicksum(CCDtoLVC_costs[var_key] * gurobi_var for var_key, gurobi_var in CCDtoLVC_vars.items())

total_upgrade_cost = quicksum(LVC_upgrade_costs[var_key] * gurobi_var for var_key, gurobi_var in LVC_upgrade_vars.items())

total_cost = total_ID_cost + total_IDtoLVC_cost + total_CCDtoLVC_cost + total_upgrade_cost

model.setObjective(total_cost, GRB.MINIMIZE)

### Base constraints

week_agnostic_ID_vars = { ID: quicksum(ID_vars[week, ID] for week in weeks) for ID in IDs }
week_agnostic_IDtoLVC_vars = { (ID, LVC): quicksum(IDtoLVC_vars[week, ID, LVC] for week in weeks) for ID, LVC in product(IDs, LVCs) }
week_agnostic_CCDtoLVC_vars = { (CCD, LVC): quicksum(CCDtoLVC_vars[week, CCD, LVC] for week in weeks) for CCD, LVC in product(CCDs, LVCs) }
# week_agnostic_LVC_upgrade_vars = { LVC: quicksum(LVC_upgrade_vars[week, LVC] for week in weeks) for LVC in LVCs }

def base_CCD_constraints(CCDtoLVC_vars: Gurobi_DecisionVar_Dict) -> Gurobi_Constraint_Gen:
    """
        Main row-based constraint for the CCDtoLVC table.\n
        For each CCD, the relevant LVCs that can be accessed from this CCD must supply a total number of vaccines that is greater than or equal to population of that CCD.
    """

    for CCD in CCDs:
        total_vaccine_supply_for_accessible_LVCs = quicksum(CCDtoLVC_vars[CCD, LVC] for LVC in LVCs)
        CCD_population = CCD_pops[CCD]
        yield total_vaccine_supply_for_accessible_LVCs >= CCD_population

def base_LVC_constraints(CCDtoLVC_vars: Gurobi_DecisionVar_Dict, IDtoLVC_vars: Gurobi_DecisionVar_Dict) -> Gurobi_Constraint_Gen:
    """
        Main col-based constraint between the CCDtoLVC and IDtoLVC tables.\n
        For each LVC, the number of people who attend this LVC must be less than or equal to the number of vaccines supplied to this LVC.
    """

    for LVC in LVCs:
        total_LVC_attendance = quicksum(CCDtoLVC_vars[CCD, LVC] for CCD in CCDs)
        total_vaccines_supplied_to_LVC = quicksum(IDtoLVC_vars[ID, LVC] for ID in IDs)
        yield total_LVC_attendance <= total_vaccines_supplied_to_LVC

def base_ID_constraints(ID_vars: Gurobi_DecisionVar_Dict, IDtoLVC_vars: Gurobi_DecisionVar_Dict) -> Gurobi_Constraint_Gen:
    """
        Main row-based constraint between the ID and IDtoLVC tables.\n
        For each ID, the number of vaccines that this ID supplies to each of its LVCs is less than or equal to its total vaccine supply.
    """

    for ID in IDs:
        total_vaccines_supplied_to_ID = ID_vars[ID]
        total_vaccines_supplied_to_LVCs = quicksum(IDtoLVC_vars[ID, LVC] for LVC in LVCs)
        yield total_vaccines_supplied_to_LVCs <= total_vaccines_supplied_to_ID

def maximum_ID_constraints(ID_vars: Gurobi_DecisionVar_Dict, maximum: int) -> Gurobi_Constraint_Gen:
    """
        For each ID, limit the total vaccine supply to that ID by the given maximum
    """

    for ID in IDs:
        total_vaccines_supplied_to_ID = ID_vars[ID]
        yield total_vaccines_supplied_to_ID <= maximum

def maximum_LVC_constraints(IDtoLVC_vars: Gurobi_DecisionVar_Dict, LVC_upgrade_vars: Gurobi_DecisionVar_Dict, maximum: int) -> Gurobi_Constraint_Gen:
    """
        For each LVC, limit the total vaccine supply to that LVC by the given maximum (with LVC upgrades included)
    """

    for LVC in LVCs:
        total_vaccines_supplied_to_LVC = quicksum(IDtoLVC_vars[ID, LVC] for ID in IDs)
        yield total_vaccines_supplied_to_LVC <= maximum + LVC_upgrade_vars[LVC] * 7500

### Apply contraints

comm6_base_constraint_generator = chain(
    base_ID_constraints(week_agnostic_ID_vars, week_agnostic_IDtoLVC_vars),
    base_LVC_constraints(week_agnostic_CCDtoLVC_vars, week_agnostic_IDtoLVC_vars),
    base_CCD_constraints(week_agnostic_CCDtoLVC_vars),

    maximum_ID_constraints(week_agnostic_ID_vars, COMM6_ID_MAX),
    maximum_LVC_constraints(week_agnostic_IDtoLVC_vars, LVC_upgrade_vars, COMM6_LVC_MAX), 
)

for constraint in comm6_base_constraint_generator:
    model.addConstr(constraint)

model.optimize()













