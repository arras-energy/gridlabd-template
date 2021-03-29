import matplotlib.pyplot as plt
import os
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import pandapower.networks as nw
import numpy as np
import pylab
import random
import gurobipy as gp
from gurobipy import GRB

def network_create():
	# for IEEE 9-Bus system
	# create empty net
	net = pp.create_empty_network() 

	#create bus elements
	b1 = pp.create_bus(net, vn_kv=16.5, name="bus_1", geodata=(-2.913407, -0.643875), zone=1, max_vm_pu=1.1, min_vm_pu=0.9)
	b2 = pp.create_bus(net, vn_kv=18.0, name="bus_2", geodata=(0.936991, -0.117367), zone=2, max_vm_pu=1.1, min_vm_pu=0.9)
	b3 = pp.create_bus(net, vn_kv=13.8, name="bus_3", geodata=(-1.451821, 2.940568), zone=3, max_vm_pu=1.1, min_vm_pu=0.9)
	b4 = pp.create_bus(net, vn_kv=230.0, name="bus_4", geodata=(-2.054941, 0.009793), zone=1, max_vm_pu=1.1, min_vm_pu=0.9)
	b5 = pp.create_bus(net, vn_kv=230.0, name="bus_5", geodata=(-0.983023, -0.394095), zone=1, max_vm_pu=1.1, min_vm_pu=0.9)
	b6 = pp.create_bus(net, vn_kv=230.0, name="bus_6", geodata=(-2.178906, 1.148920), zone=3, max_vm_pu=1.1, min_vm_pu=0.9)
	b7 = pp.create_bus(net, vn_kv=230.0, name="bus_7", geodata=(-0.063903, 0.285821), zone=2, max_vm_pu=1.1, min_vm_pu=0.9)
	b8 = pp.create_bus(net, vn_kv=230.0, name="bus_8", geodata=(-0.243500, 1.416604), zone=2, max_vm_pu=1.1, min_vm_pu=0.9)
	b9 = pp.create_bus(net, vn_kv=230.0, name="bus_9", geodata=(-1.294398, 1.871889), zone=3, max_vm_pu=1.1, min_vm_pu=0.9)

	#create generator elements
	pp.create_ext_grid(net, bus=b1, vn_kv=16.5, vm_pu=1.04, va_degree=0, name="grid_connect",
		min_p_mw=-1000, max_p_mw=1000, controllable=True)
	pp.create_gen(net, bus=b2, p_mw=163.0, vn_kv=18.0, vm_pu=1.025, name="generator_1",
		min_p_mw=0, max_p_mw=1000, controllable=True) 
	pp.create_gen(net, bus=b3, p_mw=85.0, vn_kv=13.8, vm_pu=1.022, name="generator_2",
		min_p_mw=0, max_p_mw=1000, controllable=True)

	costeg = pp.create_poly_cost(net, 0, 'ext_grid', cp1_eur_per_mw=1)
	costgen_1 = pp.create_poly_cost(net, 0, 'gen', cp1_eur_per_mw=1)
	costgen_2 = pp.create_poly_cost(net, 1, 'gen', cp1_eur_per_mw=1)

	#create load elements
	pp.create_load(net, bus=b5, p_mw=125.0, q_mvar=50, name="load_1", controllable=False)
	pp.create_load(net, bus=b6, p_mw=90.0, q_mvar=30, name="load_2", controllable=False)
	pp.create_load(net, bus=b8, p_mw=100.0, q_mvar=35, name="load_3", controllable=False)

	#create branch elements
	pp.create_transformer_from_parameters(net, hv_bus=b4, lv_bus=b1, i0_percent=0.038, pfe_kw=11.6,
		vkr_percent=0.322, sn_mva=400.0, vn_lv_kv=16.5, vn_hv_kv=230.0, vk_percent=17.8, name="trafo_1")
	pp.create_transformer_from_parameters(net, hv_bus=b7, lv_bus=b2, i0_percent=0.038, pfe_kw=11.6,
		vkr_percent=0.322, sn_mva=400.0, vn_lv_kv=18.0, vn_hv_kv=230.0, vk_percent=17.8, name="trafo_2")
	pp.create_transformer_from_parameters(net, hv_bus=b9, lv_bus=b3, i0_percent=0.038, pfe_kw=11.6,
		vkr_percent=0.322, sn_mva=400.0, vn_lv_kv=13.8, vn_hv_kv=230.0, vk_percent=17.8, name="trafo_3")

	pp.create_line(net, from_bus=b7, to_bus=b8, length_km=1.0, name="line_7_8",std_type="NAYY 4x120 SE") # line 1
	pp.create_line(net, from_bus=b8, to_bus=b9, length_km=1.0, name="line_8_9",std_type="NAYY 4x120 SE") # line 2
	pp.create_line(net, from_bus=b9, to_bus=b6, length_km=1.0, name="line_9_6",std_type="NAYY 4x120 SE") # line 3
	pp.create_line(net, from_bus=b6, to_bus=b4, length_km=1.0, name="line_6_4",std_type="NAYY 4x120 SE") # line 4
	pp.create_line(net, from_bus=b4, to_bus=b5, length_km=1.0, name="line_4_5",std_type="NAYY 4x120 SE") # line 5
	pp.create_line(net, from_bus=b5, to_bus=b7, length_km=1.0, name="line_5_7",std_type="NAYY 4x120 SE") # line 6
	
	return net

def risk_fire(factor,risk,status):
	if len(factor) != len(risk) or len(risk) != len(status) or len(factor) != len(status):
		return -1
	else:
		r_fire = 0.0
		std_fire = 0.0
		num = len(factor)
		for k in range(num):
			r_fire += factor[k]*risk[k]*status[k]
			std_fire += factor[k]*risk[k]
		return r_fire, std_fire

def networrk_show(net):
	cmap_list=[(0, "grey"), (20, "green"), (50, "yellow"), (100, "red")]
	cmap, norm = plot.cmap_continuous(cmap_list)
	lc = plot.create_line_collection(net, net.line.index, zorder=1, cmap=cmap, norm=norm, linewidths=2)

	cmap_list=[(0.95, "blue"), (1.0, "green"), (1.05, "red")]
	cmap, norm = plot.cmap_continuous(cmap_list)
	bc = plot.create_bus_collection(net, net.bus.index, size=0.1, zorder=2, cmap=cmap, norm=norm)

	cmap_list=[(0, "grey"), (20, "green"), (50, "yellow"), (100, "red")]
	cmap, norm = plot.cmap_continuous(cmap_list)
	tc = plot.create_trafo_collection(net, net.trafo.index, size=0.1, zorder=3, cmap=cmap, norm=norm)

	colors = ["b", "g", "r", "c", "y"]
	buses = net.bus.index.tolist() # list of all bus indices
	coords = zip(net.bus_geodata.x.loc[buses].values+0.1, net.bus_geodata.y.loc[buses].values+0.1) # tuples of all bus coords
	bic = plot.create_annotation_collection(size=0.2, texts=np.char.mod('%d', buses), coords=coords, zorder=4, color=colors[0])
	plot.draw_collections([lc, bc, tc, bic], figsize=(8,6)) # plot lines, buses and bus indices

	pylab.show()

def setup_risk(length_element):
	# randomly generate the risk and factor
	random_factor = []
	random_risk = []
	for _ in range(length_element):
		random_factor.append(random.uniform(0.5, 1.5))
		random_risk.append(random.uniform(1.0, 10.0))
	return random_factor, random_risk
net = network_create()
pp.runpp(net, numba=False)
networrk_show(net)

alpha = 0.3
random.seed(5)
pool_size = 20
max_iteration = 100
num_load = len(net.load.index)
num_gen = len(net.gen.index)
num_line = len(net.line.index)
num_bus = len(net.bus.index)
num_device = num_load + num_gen + num_line + num_bus

load_factor, load_risk = setup_risk(num_load)
gen_factor, gen_risk = setup_risk(num_gen)
line_factor, line_risk = setup_risk(num_line)
bus_factor, bus_risk = setup_risk(num_bus-1)
# overall solution
best_object_score = []
best_solution = []

# Create a new model
m = gp.Model()

# Create variables
z_load_1 = m.addVar(vtype=GRB.BINARY, name="z_load_1")
z_load_2 = m.addVar(vtype=GRB.BINARY, name="z_load_2")
z_load_3 = m.addVar(vtype=GRB.BINARY, name="z_load_3")

z_trafo_1 = m.addVar(vtype=GRB.BINARY, name="z_trafo_1")
z_trafo_2 = m.addVar(vtype=GRB.BINARY, name="z_trafo_2")
z_trafo_3 = m.addVar(vtype=GRB.BINARY, name="z_trafo_3")

z_gen_1 = m.addVar(vtype=GRB.BINARY, name="z_gen_1")
z_gen_2 = m.addVar(vtype=GRB.BINARY, name="z_gen_2")

z_line_1 = m.addVar(vtype=GRB.BINARY, name="z_line_1") # line_7_8
z_line_2 = m.addVar(vtype=GRB.BINARY, name="z_line_2") # line_8_9
z_line_3 = m.addVar(vtype=GRB.BINARY, name="z_line_3") # line_9_6
z_line_4 = m.addVar(vtype=GRB.BINARY, name="z_line_4") # line_6_4
z_line_5 = m.addVar(vtype=GRB.BINARY, name="z_line_5") # line_4_5
z_line_6 = m.addVar(vtype=GRB.BINARY, name="z_line_6") # line_5_7

z_bus_2 = m.addVar(vtype=GRB.BINARY, name="z_bus_2")
z_bus_3 = m.addVar(vtype=GRB.BINARY, name="z_bus_3")
z_bus_4 = m.addVar(vtype=GRB.BINARY, name="z_bus_4")
z_bus_5 = m.addVar(vtype=GRB.BINARY, name="z_bus_5")
z_bus_6 = m.addVar(vtype=GRB.BINARY, name="z_bus_6")
z_bus_7 = m.addVar(vtype=GRB.BINARY, name="z_bus_7")
z_bus_8 = m.addVar(vtype=GRB.BINARY, name="z_bus_8")
z_bus_9 = m.addVar(vtype=GRB.BINARY, name="z_bus_9")

P_gen_1 = m.addVar(lb=0.0, name="P_gen_1")
P_gen_2 = m.addVar(lb=0.0, name="P_gen_2")
P_ext_grid = m.addVar(ub=1000.0, name="P_ext_grid")

P_load_1 = m.addVar(ub=125.0, lb=0.0, name="P_load_1") # active power for load 1
P_load_2 = m.addVar(ub=90.0, lb=0.0, name="P_load_2") # active power for load 2
P_load_3 = m.addVar(ub=100.0, lb=0.0, name="P_load_3") # active power for load 3

P_4_5 = m.addVar(name="P_4_5")
P_5_7 = m.addVar(name="P_5_7")
P_7_8 = m.addVar(name="P_7_8")
P_8_9 = m.addVar(name="P_8_9")
P_9_6 = m.addVar(name="P_9_6")
P_6_4 = m.addVar(name="P_6_4")

# Add constraints
m.addConstr(z_bus_2 >= z_gen_1, "c_bus2_1") # for generator
m.addConstr(z_bus_2 >= z_trafo_2, "c_bus2_2") # for transformer

m.addConstr(z_bus_3 >= z_gen_2, "c_bus3_1") # for generator
m.addConstr(z_bus_3 >= z_trafo_3, "c_bus3_2") # for transformer

m.addConstr(z_bus_4 >= z_line_4, "c_bus4_1") # for line
m.addConstr(z_bus_4 >= z_line_5, "c_bus4_2") # for line
m.addConstr(z_bus_4 >= z_trafo_1, "c_bus4_3") # for transformer
m.addConstr(P_ext_grid*z_trafo_1+P_6_4*z_line_4 == P_4_5*z_line_5, "c_bus4_4") # for power balance

m.addConstr(z_bus_5 >= z_line_5, "c_bus5_1") # for line
m.addConstr(z_bus_5 >= z_line_6, "c_bus5_2") # for line
m.addConstr(z_bus_5 >= z_load_1, "c_bus5_3") # for load
m.addConstr(P_load_1*z_load_1+P_5_7*z_line_6 == P_4_5*z_line_5, "c_bus5_4") # for power balance

m.addConstr(z_bus_6 >= z_line_3, "c_bus6_1") # for line
m.addConstr(z_bus_6 >= z_line_4, "c_bus6_2") # for line
m.addConstr(z_bus_6 >= z_load_2, "c_bus6_3") # for load
m.addConstr(P_load_2*z_load_2+P_6_4*z_line_4 == P_9_6*z_line_3, "c_bus6_4") # for power balance 

m.addConstr(z_bus_7 >= z_line_1, "c_bus7_1") # for line
m.addConstr(z_bus_7 >= z_line_6, "c_bus7_2") # for line
m.addConstr(z_bus_7 >= z_trafo_2, "c_bus7_3") # for transformer
m.addConstr(P_gen_1*z_gen_1+P_5_7*z_line_6 == P_7_8*z_line_1, "c_bus7_4") # for power balance

m.addConstr(z_bus_8 >= z_line_1, "c_bus8_1") # for line
m.addConstr(z_bus_8 >= z_line_2, "c_bus8_2") # for line
m.addConstr(z_bus_8 >= z_load_3, "c_bus8_3") # for load
m.addConstr(P_load_3*z_load_3+P_8_9*z_line_2 == P_7_8*z_line_1, "c_bus8_4") # for power balance

m.addConstr(z_bus_9 >= z_line_2, "c_bus9_1") # for line
m.addConstr(z_bus_9 >= z_line_3, "c_bus9_2") # for line
m.addConstr(z_bus_9 >= z_trafo_3, "c_bus9_3") # for transformer
m.addConstr(P_gen_2*z_gen_2+P_8_9*z_line_2 == P_9_6*z_line_3, "c_bus9_4") # for power balance

# m.addConstr(P_ext_grid+P_gen_1+P_gen_2-P_load_1-P_load_2-P_load_3 == 0, "c_power") # for transformer

# Set objective
risk_load_sum = load_factor[0]*load_risk[0]*z_load_1 + load_factor[1]*load_risk[1]*z_load_2 + load_factor[2]*load_risk[2]*z_load_3
risk_gen_sum = gen_factor[0]*gen_risk[0]*z_gen_1 + gen_factor[1]*gen_risk[1]*z_gen_2
risk_line_sum = line_factor[0]*line_risk[0]*z_line_1+line_factor[1]*line_risk[1]*z_line_2+line_factor[2]*line_risk[2]*z_line_3+line_factor[3]*line_risk[3]*z_line_4+line_factor[4]*line_risk[4]*z_line_5+line_factor[5]*line_risk[5]*z_line_6
risk_bus_sum = bus_factor[0]*bus_risk[0]*z_bus_2+bus_factor[1]*bus_risk[1]*z_bus_3+bus_factor[2]*bus_risk[2]*z_bus_4+bus_factor[3]*bus_risk[3]*z_bus_5+bus_factor[4]*bus_risk[4]*z_bus_6+bus_factor[5]*bus_risk[5]*z_bus_7+bus_factor[6]*bus_risk[6]*z_bus_8+bus_factor[7]*bus_risk[7]*z_bus_9

obj = -(1-alpha)*(z_load_1*P_load_1+z_load_2*P_load_2+z_load_3*P_load_3) + alpha*(risk_load_sum+risk_gen_sum+risk_line_sum+risk_bus_sum)
m.setObjective(obj)

# solve the problem
m.optimize()

for v in m.getVars():
    print('%s %g' % (v.varName, v.x))
print('Obj: %g' % obj.getValue())

# constrants
constrs = m.getConstrs()
print(constrs)
qconstrs = m.getQConstrs()
print(qconstrs)

# # solution
# solution = m.getVars()

# # load
# if solution[0].X > 0.5:
# 	net.load.in_service.at[0] = True
# else:
# 	net.load.in_service.at[0] = False
# if solution[1].X > 0.5:
# 	net.load.in_service.at[1] = True
# else:
# 	net.load.in_service.at[1] = False
# if solution[2].X > 0.5:
# 	net.load.in_service.at[2] = True
# else:
# 	net.load.in_service.at[2] = False

# # transformer
# if solution[3].X > 0.5:
# 	net.trafo.in_service.at[0] = True
# else:
# 	net.trafo.in_service.at[0] = False
# if solution[4].X > 0.5:
# 	net.trafo.in_service.at[1] = True
# else:
# 	net.trafo.in_service.at[1] = False
# if solution[5].X > 0.5:
# 	net.trafo.in_service.at[2] = True
# else:
# 	net.trafo.in_service.at[2] = False

# # generator
# if solution[6].X > 0.5:
# 	net.gen.in_service.at[0] = True
# else:
# 	net.gen.in_service.at[0] = False
# if solution[7].X > 0.5:
# 	net.gen.in_service.at[1] = True
# else:
# 	net.gen.in_service.at[1] = False

# # line
# if solution[8].X > 0.5:
# 	net.line.in_service.at[0] = True
# else:
# 	net.line.in_service.at[0] = False
# if solution[9].X > 0.5:
# 	net.line.in_service.at[1] = True
# else:
# 	net.line.in_service.at[1] = False
# if solution[10].X > 0.5:
# 	net.line.in_service.at[2] = True
# else:
# 	net.line.in_service.at[2] = False
# if solution[11].X > 0.5:
# 	net.line.in_service.at[3] = True
# else:
# 	net.line.in_service.at[3] = False
# if solution[12].X > 0.5:
# 	net.line.in_service.at[4] = True
# else:
# 	net.line.in_service.at[4] = False
# if solution[13].X > 0.5:
# 	net.line.in_service.at[5] = True
# else:
# 	net.line.in_service.at[5] = False

# # bus
# if solution[14].X > 0.5:
# 	net.bus.in_service.at[1] = True
# else:
# 	net.bus.in_service.at[1] = False
# if solution[15].X > 0.5:
# 	net.bus.in_service.at[2] = True
# else:
# 	net.bus.in_service.at[2] = False
# if solution[16].X > 0.5:
# 	net.bus.in_service.at[3] = True
# else:
# 	net.bus.in_service.at[3] = False
# if solution[17].X > 0.5:
# 	net.bus.in_service.at[4] = True
# else:
# 	net.bus.in_service.at[4] = False
# if solution[18].X > 0.5:
# 	net.bus.in_service.at[5] = True
# else:
# 	net.bus.in_service.at[5] = False
# if solution[19].X > 0.5:
# 	net.bus.in_service.at[6] = True
# else:
# 	net.bus.in_service.at[6] = False
# if solution[20].X > 0.5:
# 	net.bus.in_service.at[7] = True
# else:
# 	net.bus.in_service.at[7] = False
# if solution[21].X > 0.5:
# 	net.bus.in_service.at[8] = True
# else:
# 	net.bus.in_service.at[8] = False



# try:
# 	pp.runpp(net, numba=False)
# except:
# 	print("-1000")

# networrk_show(net)
# print(net.res_bus)
# print(net.res_load)
# print(net.res_line)
# print(net.res_ext_grid)
# print(net.res_gen)


