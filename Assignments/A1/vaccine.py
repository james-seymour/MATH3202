IDtoLVC = [
[43.3,83.2,7.8,63.4,60.3,59.3,44.7,37.0],
[80.6,64.5,52.7,77.2,5.0,41.5,15.3,58.1],
[42.4,23.4,61.9,16.2,71.6,26.0,61.8,30.5]
]

CCDPop = [3425,2487,4820,4974,4562,4495,3240,4473,3336,4071,2049,3423,2680,2423,2864,3829,3297,2531,3306,4110,2654,3299,2595,2116,3598]

CCDtoLVC = [
[0,0,17.7,0,0,0,0,48.9],
[0,0,11.6,0,0,0,29.0,0],
[0,0,22.2,0,0,0,21.2,0],
[0,0,0,0,11.0,0,9.2,0],
[0,0,0,0,10.9,0,24.2,0],
[37.5,0,22.7,0,0,0,0,0],
[0,0,8.0,0,0,0,0,25.7],
[0,0,24.1,0,0,29.3,21.9,25.0],
[0,0,0,0,20.8,25.9,14.4,0],
[0,0,0,0,17.8,0,27.2,0],
[10.8,0,0,0,0,0,0,23.2],
[15.2,0,0,28.9,0,0,0,8.9],
[0,0,0,0,0,12.4,0,23.0],
[0,0,0,0,0,12.9,33.0,0],
[0,0,0,0,35.3,21.0,0,0],
[5.4,0,0,0,0,0,0,28.7],
[24.2,0,0,17.4,0,30.0,0,10.3],
[0,27.2,0,20.5,0,18.3,0,22.5],
[0,11.5,0,30.9,0,17.9,0,0],
[0,16.3,0,0,0,23.9,0,0],
[23.0,0,0,19.3,0,0,0,0],
[0,0,0,6.2,0,0,0,33.5],
[0,27.8,0,20.5,0,0,0,0],
[0,9.5,0,0,0,36.2,0,0],
[0,14.4,0,0,0,35.6,0,0]
]

ID_import_cost_per_dose = [109, 160, 168]
IDtoLVC_cost_per_dose = [[0.2 * distance for distance in ID] for ID in IDtoLVC]
CCDtoLVC_cost_per_dose = CCDtoLVC

# Exports

weeks = [f"WEEK{i}" for i in range(6)]
IDs = ["ID-A", "ID-B", "ID-C"]
LVCs = [f"LVC{i}" for i in range(8)]
CCDs = [f"CCD{i}" for i in range(25)]

ID_costs = { (week, ID): ID_import_cost_per_dose[ID_i]  for week in weeks for ID_i, ID in enumerate(IDs) }
IDtoLVC_costs = { (week, ID, LVC): IDtoLVC_cost_per_dose[ID_i][LVC_i] for week in weeks for LVC_i, LVC in enumerate(LVCs) for ID_i, ID in enumerate(IDs) }
CCDtoLVC_costs = { (week, CCD, LVC): CCDtoLVC_cost_per_dose[CCD_i][LVC_i] for week in weeks for LVC_i, LVC in enumerate(LVCs) for CCD_i, CCD in enumerate(CCDs) }

CCD_pops = { CCD: CCDPop[CCD_i] for CCD_i, CCD in enumerate(CCDs) }

COMM2_ID_MAX = 34000
COMM2_LVC_MAX = 15000
COMM3_LVC_MAX = 2100
COMM4_DELAY_COST = 10
COMM5_RATIO_TOLERANCE = 0.1
