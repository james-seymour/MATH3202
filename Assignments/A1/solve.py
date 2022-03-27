from collections import defaultdict
from typing import Generator, Tuple, Union
from gurobipy import Model, GRB, TempConstr, Var, tupledict, quicksum, max_, min_
from itertools import product, chain
from vaccine import (
    # Var definitions
    weeks,
    IDs,
    LVCs,
    CCDs,

    # Cost definitions
    ID_costs,
    IDtoLVC_costs,
    CCDtoLVC_costs,

    # Constraint definitions
    CCD_pops,

    # Communication constraint constants
    COMM2_ID_MAX,
    COMM2_LVC_MAX,
    COMM3_LVC_MAX,
    COMM4_DELAY_COST,
    COMM5_RATIO_TOLERANCE,
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

## Communication 1 

### Variable definitions

# For Communication 1 and 2, we are agnostic of which week we are in because we don't have a notion of weeks yet.
# Therefore, instead of writing all of the code twice, we sum the gurobi vars over weeks, 
# effectively removing the week dimension by grouping by it and aggregating with quicksum()

week_agnostic_ID_vars = { ID: quicksum(ID_vars[week, ID] for week in weeks) for ID in IDs }
week_agnostic_IDtoLVC_vars = { (ID, LVC): quicksum(IDtoLVC_vars[week, ID, LVC] for week in weeks) for ID, LVC in product(IDs, LVCs) }
week_agnostic_CCDtoLVC_vars = { (CCD, LVC): quicksum(CCDtoLVC_vars[week, CCD, LVC] for week in weeks) for CCD, LVC in product(CCDs, LVCs) }

### Contraint definitions

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


### Apply contraints

comm1_base_constraint_generator = chain(
    base_ID_constraints(week_agnostic_ID_vars, week_agnostic_IDtoLVC_vars), 
    base_LVC_constraints(week_agnostic_CCDtoLVC_vars, week_agnostic_IDtoLVC_vars), 
    base_CCD_constraints(week_agnostic_CCDtoLVC_vars)
)

for constraint in comm1_base_constraint_generator:
    model.addConstr(constraint)

model.optimize()

## Communication 2

### Constraint definitions

def maximum_ID_constraints(ID_vars: Gurobi_DecisionVar_Dict, maximum: int) -> Gurobi_Constraint_Gen:
    """
        For each ID, limit the total vaccine supply to that ID by the given maximum
    """

    for ID in IDs:
        total_vaccines_supplied_to_ID = ID_vars[ID]
        yield total_vaccines_supplied_to_ID <= maximum

def maximum_LVC_constraints(IDtoLVC_vars: Gurobi_DecisionVar_Dict, maximum: int) -> Gurobi_Constraint_Gen:
    """
        For each LVC, limit the total vaccine supply to that LVC by the given maximum
    """

    for LVC in LVCs:
        total_vaccines_supplied_to_LVC = quicksum(IDtoLVC_vars[ID, LVC] for ID in IDs)
        yield total_vaccines_supplied_to_LVC <= maximum

### Apply constraints

comm2_max_constraint_generator = chain(
    maximum_ID_constraints(week_agnostic_ID_vars, maximum=COMM2_ID_MAX), 
    maximum_LVC_constraints(week_agnostic_IDtoLVC_vars, maximum=COMM2_LVC_MAX), 
)


for constraint in comm2_max_constraint_generator:
    model.addConstr(constraint)

model.optimize()

## Communication 3

### Constraint definitions

def maximum_LVC_weekly_constraints(IDtoLVC_vars: Gurobi_DecisionVar_Dict, maximum: int) -> Gurobi_Constraint_Gen:
    """
        For each week, limit the number of weekly doses supplied to this LVC by the given maximum, using the IDtoLVC constraint generator above
    """

    for week in weeks:
        this_weeks_IDtoLVC_vars = { (ID, LVC): IDtoLVC_vars[week, ID, LVC] for ID, LVC in product(IDs, LVCs) }
        yield from maximum_LVC_constraints(this_weeks_IDtoLVC_vars, maximum)

def base_weekly_ID_constraints(ID_vars: Gurobi_DecisionVar_Dict, IDtoLVC_vars: Gurobi_DecisionVar_Dict) -> Gurobi_Constraint_Gen:
    """
        Generate the same constraints built into the problem for IDs, but on a weekly basis, using the base_ID_constraints generator above
    """
    for week in weeks:
        this_weeks_ID_vars = { ID: ID_vars[week, ID] for ID in IDs }
        this_weeks_IDtoLVC_vars = { (ID, LVC): IDtoLVC_vars[week, ID, LVC] for ID, LVC in product(IDs, LVCs) }
        yield from base_ID_constraints(this_weeks_ID_vars, this_weeks_IDtoLVC_vars)

def base_weekly_LVC_constraints(CCDtoLVC_vars: Gurobi_DecisionVar_Dict, IDtoLVC_vars: Gurobi_DecisionVar_Dict) -> Gurobi_Constraint_Gen:
    """
        Generate the same constraints built into the problem for IDtoLVCs, but on a weekly basis, using the base_LVC_constraints generator above
    """
    for week in weeks:
        this_weeks_IDtoLVC_vars = { (ID, LVC): IDtoLVC_vars[week, ID, LVC] for ID, LVC in product(IDs, LVCs) }
        this_weeks_CCDtoLVC_vars = { (CCD, LVC): CCDtoLVC_vars[week, CCD, LVC] for CCD, LVC in product(CCDs, LVCs) }
        yield from base_LVC_constraints(this_weeks_CCDtoLVC_vars, this_weeks_IDtoLVC_vars)

### Apply constraints

comm3_base_weekly_constraint_generator = chain(
    base_weekly_ID_constraints(ID_vars, IDtoLVC_vars), 
    base_weekly_LVC_constraints(CCDtoLVC_vars, IDtoLVC_vars)
)

for constraint in comm3_base_weekly_constraint_generator:
    model.addConstr(constraint)

comm3_max_weekly_constraint_generator = maximum_LVC_weekly_constraints(IDtoLVC_vars, maximum=COMM3_LVC_MAX)

for constraint in comm3_max_weekly_constraint_generator:
    model.addConstr(constraint)

model.optimize()

## Communication 4

### Cost definitions

CCDtoLVC_costs_with_delay = { (week, CCD, LVC): cost + COMM4_DELAY_COST * int(week[-1]) for (week, CCD, LVC), cost in CCDtoLVC_costs.items() }

total_CCDtoLVC_cost_with_delay = quicksum(CCDtoLVC_costs_with_delay[var_key] * gurobi_var for var_key, gurobi_var in CCDtoLVC_vars.items())

comm4_total_cost_with_delay = total_ID_cost + total_IDtoLVC_cost + total_CCDtoLVC_cost_with_delay

model.setObjective(comm4_total_cost_with_delay, GRB.MINIMIZE)

model.optimize()

## Communication 5

### Auxiliary variable definitions

CCD_vaccination_ratio_vars = model.addVars(weeks, CCDs)
min_ratio_vars = model.addVars(weeks)
max_ratio_vars = model.addVars(weeks)

### Constraint definitions

def distribution_tolerance_constraints(CCDtoLVC_vars: Gurobi_DecisionVar_Dict, max_ratio_tolerance: float) -> Gurobi_Constraint_Gen:
    """
        For each week, calculate the proportion of the population which is due to get vaccinated for each CCD, and assign this value to the ratio_vars auxiliary variables.
        Then, find the min and max of these auxiliary variables over each CCD, for each week, and assign these values to the min_ratio_vars and max_ratio_vars.
        Then, we can calculate the difference between these min and max ratios for each week, and ensure that the tolerance is less than the given max tolerance.
    """
    for week in weeks:

        for CCD in CCDs:
            CCD_population_vaccinated_this_week = quicksum(CCDtoLVC_vars[week, CCD, LVC] for LVC in LVCs)
            CCD_population = CCD_pops[CCD]
            yield CCD_vaccination_ratio_vars[week, CCD] == CCD_population_vaccinated_this_week / CCD_population

        min_ratio_vaccinated_this_week, max_ratio_vaccinated_this_week = min_(CCD_vaccination_ratio_vars[week, CCD] for CCD in CCDs), max_(CCD_vaccination_ratio_vars[week, CCD] for CCD in CCDs)
        yield min_ratio_vars[week] == min_ratio_vaccinated_this_week
        yield max_ratio_vars[week] == max_ratio_vaccinated_this_week
        
        yield max_ratio_vars[week] - min_ratio_vars[week] <= max_ratio_tolerance

### Apply constraints

comm5_distribution_tolerance_constraints = distribution_tolerance_constraints(CCDtoLVC_vars, max_ratio_tolerance=COMM5_RATIO_TOLERANCE)

for constraint in comm5_distribution_tolerance_constraints:
    model.addConstr(constraint)

model.optimize()

