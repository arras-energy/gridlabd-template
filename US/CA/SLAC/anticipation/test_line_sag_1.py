############################################
# Assumption 1: conductor is tied or fixed at the rigid support insulators
# Assumption 2: wind load parallel to transmission line direction is ignored
# Assumption 3: solar radiation angle is ignored

from math import *
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate

def air_material_constant(temp):
	# calculate the constant parameters
	# reference: http://home.eng.iastate.edu/~jdm/wind/TransmissionLineLoadingDesignCriteriaAndHTS.pdf
	temp_x = np.arange(0.0, 110.0, 10) # unit: DegC
	specific_mass = [1.29, 1.25, 1.20, 1.17, 1.13, 1.09, 1.06, 1.03, 1.0, 0.97, 0.95] # unit: kg/m3
	thermal_conductivity = [0.0243, 0.025, 0.0257, 0.0265, 0.0272, 0.028, 0.0287,0.0294, 0.0301, 0.0309, 0.0316] # unit: W/(m*DegC)
	dynamic_viscosity = [0.175e-4, 0.18e-4, 0.184e-4, 0.189e-4, 0.194e-4, 0.199e-4, 0.203e-4, 0.208e-4, 0.213e-4, 0.217e-4, 0.222e-4] # unit: N*s/m2
	
	f_specific_mass = interpolate.interp1d(temp_x, specific_mass, fill_value = "extrapolate")
	specific_mass_temp = f_specific_mass(temp)

	f_thermal_conductivity = interpolate.interp1d(temp_x, thermal_conductivity, fill_value = "extrapolate")
	thermal_conductivity_temp = f_thermal_conductivity(temp)

	f_dynamic_viscosity = interpolate.interp1d(temp_x, dynamic_viscosity, fill_value = "extrapolate")
	dynamic_viscosity_temp = f_dynamic_viscosity(temp)
	
	return specific_mass_temp, thermal_conductivity_temp, dynamic_viscosity_temp

############################################
# define conductor data
conductor_type = 1
if conductor_type == 1: 			# "Name": "403 mm2 37 AAC",
	outside_diameter = 26.1e-3 		# "Outside Diameter": 26.1e-3, # unit: m
	conductor_unit_weight = 10.89 	# "Conductor Unit Weight": 10.89, # unit: N/m
	rts = 8.18e4 					# "Rated Tensile Strength": 81800.0, # unit: N
	module_elasticity = 58.9e9 		# "Modulus of Elasticity": 58.9e9, # unit: Pa
	coeff_thermal = 2.3e-5			# "Coefficient of Thermal Expansion": 2.3e-5, # unit: /DegC
	conductor_area = 402.6e-6		# "Total Conductor Area": 402.6e-6, # unit: m2
	coeff_temp_Al = 0.0039			# "Resistance temperature coefficient for Aluminium": 0.0039, # unit:/DegC
	R_20C = 2.65e-8					# "Resistance at 20 DegC": 2.65e-8 # unit: ohm/m
	temp_init = 15					# "Initial Temperature": 15 # unit: DegC

elif conductor_type == 2:			# "Name": "795MCM ACSR",
	outside_diameter = 27.76e-3		# "Outside Diameter": 27.76e-3, # unit: m
	conductor_unit_weight = 14.96	# "Conductor Unit Weight": 14.96, # unit: N/m
	rts = 126954.1					# "Rated Tensile Strength": 126954.1, # unit: N
	module_elasticity = 58.9e9		# "Modulus of Elasticity": 59.0e9, # unit: Pa
	coeff_thermal = 1.93e-5			# "Coefficient of Thermal Expansion": 0.0000193, # unit: /DegC
	conductor_area = 454.8e-6		# "Total Conductor Area": 454.8 # unit: m2
	coeff_temp_Al = 0.0039			# "Resistance temperature coefficient for Aluminium": 0.0039, # unit:/DegC
	R_20C = 2.65e-8					# "Resistance at 20 DegC": 2.65e-8 # unit: ohm/m	
	temp_init = 15

############################################
# define pole coordinate
pole_1_x = 0.0
pole_1_y = 0.0
pole_1_z = 0.0

pole_2_x = 350.0
pole_2_y = 0.0
pole_2_z = 32.0

############################################
# define transmission line configuration
Vll_rated = 13e3 # line rated voltage
P_rated = 16.5e6 # power flow through the line

H_init = rts*0.25 # initial horizontal tension is 25% of Rated Tensile Strength

############################################
# define weather conditions
temp_a = 30.0 # ambient temperature, unit: DegC
wind_speed = 10.0 # unit: m/s
wind_angle = 180.0 # 360° for north; 0° for undefined
ice_thickness = 0.0; # unit: m

############################################
# initial sag at no load, no wind condition
pole_span = sqrt((pole_1_x - pole_2_x)**2 + (pole_1_y - pole_2_y)**2 + (pole_1_z - pole_2_z)**2)
horizontal_distance = sqrt((pole_1_x - pole_2_x)**2 + (pole_1_y - pole_2_y)**2)
vertical_distance = abs(pole_1_z - pole_2_z)

sag_init = conductor_unit_weight*pole_span*pole_span/(8*H_init)

# the lowest point is closer to pole 1 because the pole is at a lower elevation
lowest_to_pole_1 = horizontal_distance/2 - horizontal_distance*vertical_distance/(8*sag_init)
lowest_to_pole_2 = horizontal_distance/2 + horizontal_distance*vertical_distance/(8*sag_init)

line_length = horizontal_distance + (lowest_to_pole_1**3 + lowest_to_pole_2**3)*(conductor_unit_weight**2/(6*H_init**2))

sag_init_pole_1 = conductor_unit_weight * lowest_to_pole_1**2 / (2*H_init)
sag_init_pole_2 = conductor_unit_weight * lowest_to_pole_2**2 / (2*H_init)
print("sag_init:", sag_init)


############################################
# calculate conductor temperature tamp_load
Irms = 	P_rated/(sqrt(3)*Vll_rated)

# Q_R + Q_C = Q_S + Q_I
# Radiant Heat Loss: Q_R = k_s * k_e * D * pi * (tamp_load^4 - tamp_a^4)
# Convective Heat Loss: Q_C = k_angle * (1.01 + 1.35*Nre^0.52) * k_f * (tamp_load - tamp_a)
# Solar Heat Gain: Q_S = D * k_a * solar_radiation
# Current Heat Loss: Q_I = I^2 * R

# /////////////////////////
# for Q_I
Q_I_coeff_first = Irms*Irms*R_20C*coeff_temp_Al
Q_I_coeff_constant = Irms*Irms*R_20C*(1-coeff_temp_Al*(20.0+273.0))

# for Q_S
k_a = 0.5 # absorption coefficient
solar_radiation = 1000 # unit: W/m2
Q_S_constant = k_a * (outside_diameter + 2*ice_thickness) * solar_radiation

# for Q_C
line_angle = 180 * atan((pole_2_x-pole_1_x) / (pole_2_y - pole_1_y + 1e-8))/np.pi

if abs(line_angle - wind_angle) <= 90:
	phi = abs(line_angle - wind_angle)
elif abs(line_angle - wind_angle) <= 180:
	phi = 180 - abs(line_angle - wind_angle)
elif abs(line_angle - wind_angle) <= 270:
	phi = abs(line_angle - wind_angle) - 180
else:
	phi = 360 - abs(line_angle - wind_angle)
phi = np.pi * phi/180

k_angle = 1.194 - cos(phi) + 0.194*cos(2*phi) + 0.368*sin(2*phi)
air_mass, k_f, air_viscosity = air_material_constant(temp_a)
Nre = wind_speed * (outside_diameter + 2*ice_thickness) * air_mass / air_viscosity
if wind_speed > 1.1:
	Q_C_coeff_first = k_angle*(1.01+1.35*Nre**0.52)*k_f
	Q_C_constant = -k_angle*(1.01+1.35*Nre**0.52)*k_f*(temp_a+273.0)
else:
	Q_C_coeff_first = k_angle*0.754*(Nre**0.6)*k_f
	Q_C_constant = -k_angle*0.754*(Nre**0.6)*k_f*(temp_a+273.0)
# wind_test = np.arange(0.0, 2, 0.05)
# Nu_low = []
# Nu_high = []
# for wind_test_i in wind_test:
# 	Nu_low.append(1.01+1.35*(wind_test_i * (outside_diameter + 2*ice_thickness) * air_mass / air_viscosity)**0.52)
# 	Nu_high.append(0.754*(wind_test_i * (outside_diameter + 2*ice_thickness) * air_mass / air_viscosity)**0.6)
# plt.plot(wind_test, Nu_low, label = "line 1")
# plt.plot(wind_test, Nu_high, label = "line 2")
# plt.legend()
# plt.show()

# for Q_R
k_e = 0.6
k_s = 5.6704e-8
Q_R_constant = -5.6704e-8 * k_e * (outside_diameter + 2.0*ice_thickness) * (temp_a+273.0)**4
Q_R_coeff_fourth = 5.6704e-8 * k_e * (outside_diameter + 2.0*ice_thickness)

coeff = [-Q_R_coeff_fourth, 0.0, 0.0, Q_I_coeff_first-Q_C_coeff_first, Q_I_coeff_constant+Q_S_constant
		-Q_C_constant-Q_R_constant]
r = np.roots(coeff)
r = r[~np.iscomplex(r)]
temp_load = np.absolute(r[r > 0.0]) # unit: K
temp_load = temp_load - 273.0 # unit: DegC
print("Temperature at loaded condition:", temp_load)

############################################
# calculate the new line sag at loaded condition
ice_mass = 915 # unit: kg/m3
g_constant = 9.81 # Gravity of Earth, unit: m/s2
ice_unit_weight = ice_mass * np.pi * ice_thickness * (outside_diameter + ice_thickness) * g_constant
print("ice_unit_weight:", ice_unit_weight)

wind_unit_weight = 0.5 * air_mass * (wind_speed*sin(phi))**2 * (outside_diameter + 2*ice_thickness)
print("wind_unit_weight:", wind_unit_weight)

total_unit_weight = sqrt(wind_unit_weight**2+(conductor_unit_weight+ice_unit_weight)**2)
print("conductor_unit_weight:", conductor_unit_weight)
print("total_unit_weight:", total_unit_weight)

H_load_second = (conductor_unit_weight*horizontal_distance)**2 * conductor_area*module_elasticity/(24*H_init**2)-H_init+(temp_load-temp_init)*coeff_thermal*conductor_area*module_elasticity
H_load_constant = -(total_unit_weight*horizontal_distance)**2 * conductor_area * module_elasticity / 24

coeff = [1, H_load_second, 0.0, H_load_constant]
r = np.roots(coeff)
r = r[~np.iscomplex(r)]
H_load = np.absolute(r[r > 0.0])
print("H_load:", H_load)
print("H_init:", H_init)

sag_load = total_unit_weight * pole_span*pole_span / (8*H_load)
print("sag_load:", sag_load)
print("sag_init:", sag_init)

lowest_load_to_pole_1 = horizontal_distance/2 - horizontal_distance*vertical_distance/(8*sag_load)
lowest_load_to_pole_2 = horizontal_distance/2 + horizontal_distance*vertical_distance/(8*sag_load)
print("lowest_load_to_pole_1:", lowest_load_to_pole_1)
print("lowest_load_to_pole_2:", lowest_load_to_pole_2)
print("lowest_to_pole_1:", lowest_to_pole_1)
print("lowest_to_pole_2:", lowest_to_pole_2)

sag_load_pole_1 = total_unit_weight * lowest_load_to_pole_1**2 / (2*H_load)
sag_load_pole_2 = total_unit_weight * lowest_load_to_pole_2**2 / (2*H_load)
print("sag_load_pole_1:", sag_load_pole_1)
print("sag_load_pole_2:", sag_load_pole_2)
print("sag_init_pole_1:", sag_init_pole_1)
print("sag_init_pole_2:", sag_init_pole_2)

sag_angle = atan(wind_unit_weight/(ice_unit_weight+conductor_unit_weight))
sag_load_vertical_pole_1 = sag_load_pole_1*cos(sag_angle)
sag_load_vertical_pole_2 = sag_load_pole_2*cos(sag_angle)
print("sag_load_vertical_pole_1:", sag_load_vertical_pole_1)
print("sag_load_vertical_pole_2:", sag_load_vertical_pole_2)











