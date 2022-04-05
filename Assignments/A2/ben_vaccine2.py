IDtoLVC = [[61.2, 27.8, 26.6, 5.8, 64.0, 83.2, 51.0, 62.0],
           [61.3, 33.1, 69.2, 62.0, 86.3, 59.6, 9.0, 19.9],
           [6.6, 54.9, 47.9, 72.8, 28.2, 28.0, 62.9, 49.3]]

CCDPop = [
    3770, 4138, 3152, 4052, 5465, 5388, 5290, 4021, 4761, 4338, 5275, 5346,
    3874, 3431, 3483, 5894, 3837, 5405, 6144, 4249, 3790, 5747, 5680, 4611,
    4156
]

CCDtoLVC = [[0, 0, 39.6, 12.8, 0, 0, 0, 0], [0, 25.1, 0, 5.9, 0, 0, 0, 0],
            [0, 18.8, 0, 0, 0, 0, 23.1, 0], [0, 27.2, 0, 0, 0, 0, 11.4, 0],
            [0, 0, 0, 0, 0, 0, 19.9, 30.2], [0, 0, 24.1, 15.3, 0, 0, 0, 0],
            [0, 24.2, 15.6, 19.6, 0, 0, 0,
             0], [0, 11.8, 0, 0, 0, 0, 26.0, 28.5],
            [0, 19.2, 0, 0, 0, 0, 14.5, 15.5], [0, 0, 0, 0, 0, 0, 21.2, 10.3],
            [0, 0, 7.4, 0, 31.5, 0, 0, 0], [26.0, 29.4, 19.9, 0, 0, 0, 0, 0],
            [20.5, 28.9, 0, 0, 0, 0, 0, 28.0],
            [24.5, 0, 0, 0, 0, 26.9, 0, 19.7], [0, 0, 0, 0, 0, 34.7, 0, 19.9],
            [0, 0, 29.7, 0, 11.0, 0, 0, 0], [17.5, 0, 0, 0, 14.8, 0, 0, 0],
            [9.1, 0, 0, 0, 0, 25.9, 0, 0], [26.6, 0, 0, 0, 0, 15.3, 0, 25.0],
            [0, 0, 0, 0, 0, 10.3, 0, 33.9], [0, 0, 49.2, 0, 21.0, 0, 0, 0],
            [29.1, 0, 0, 0, 14.2, 0, 0, 0], [11.2, 0, 0, 0, 23.7, 0, 0, 0],
            [27.6, 0, 0, 0, 0, 6.8, 0, 0], [48.0, 0, 0, 0, 0, 20.6, 0, 0]]
LVCUCost = [
    1501000, 1054000, 1909000, 1875000, 1960000, 1592000, 1821000, 1262000
]

ID_import_cost_per_dose = [169, 170, 144]
IDtoLVC_cost_per_dose = [[0.2 * distance for distance in ID] for ID in IDtoLVC]
CCDtoLVC_cost_per_dose = CCDtoLVC

# Exports

weeks = [f"WEEK{i}" for i in range(6)]
IDs = ["ID-A", "ID-B", "ID-C"]
LVCs = [f"LVC{i}" for i in range(8)]
CCDs = [f"CCD{i}" for i in range(25)]

ID_costs = {(week, ID): ID_import_cost_per_dose[ID_i]
            for week in weeks for ID_i, ID in enumerate(IDs)}

IDtoLVC_costs = {(week, ID, LVC): IDtoLVC_cost_per_dose[ID_i][LVC_i]
                 for week in weeks for LVC_i, LVC in enumerate(LVCs)
                 for ID_i, ID in enumerate(IDs)}

CCDtoLVC_costs = {(week, CCD, LVC): CCDtoLVC_cost_per_dose[CCD_i][LVC_i]
                  for week in weeks for LVC_i, LVC in enumerate(LVCs)
                  for CCD_i, CCD in enumerate(CCDs)}

LVC_upgrade_costs = {LVC: LVCUCost[LVC_i] for LVC_i, LVC in enumerate(LVCs)}

CCD_pops = {CCD: CCDPop[CCD_i] for CCD_i, CCD in enumerate(CCDs)}

COMM6_ID_MAX = 47000
COMM6_LVC_MAX = 14000
