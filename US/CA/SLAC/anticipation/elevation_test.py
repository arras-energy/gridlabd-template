"""Global elevation data acquisition
REQUIREMENTS
Requires the elevation module (https://pypi.org/project/elevation/)
and the GDAL package (http://www.gdal.org).
"""
import os, subprocess
import pandas as pd
import numpy as np
import math
from PIL import Image
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, interp2d
from math import *

file_folder = "/Users/fxie2/Desktop/PSPS/vegetation"
def air_material_constant(temp):
    # calculate the constant parameters
    # reference: http://home.eng.iastate.edu/~jdm/wind/TransmissionLineLoadingDesignCriteriaAndHTS.pdf
    temp_x = np.arange(0.0, 110.0, 10) # unit: DegC
    specific_mass = [1.29, 1.25, 1.20, 1.17, 1.13, 1.09, 1.06, 1.03, 1.0, 0.97, 0.95] # unit: kg/m3
    thermal_conductivity = [0.0243, 0.025, 0.0257, 0.0265, 0.0272, 0.028, 0.0287,0.0294, 0.0301, 0.0309, 0.0316] # unit: W/(m*DegC)
    dynamic_viscosity = [0.175e-4, 0.18e-4, 0.184e-4, 0.189e-4, 0.194e-4, 0.199e-4, 0.203e-4, 0.208e-4, 0.213e-4, 0.217e-4, 0.222e-4] # unit: N*s/m2
    
    f_specific_mass = interp1d(temp_x, specific_mass, fill_value = "extrapolate")
    specific_mass_temp = f_specific_mass(temp)

    f_thermal_conductivity = interp1d(temp_x, thermal_conductivity, fill_value = "extrapolate")
    thermal_conductivity_temp = f_thermal_conductivity(temp)

    f_dynamic_viscosity = interp1d(temp_x, dynamic_viscosity, fill_value = "extrapolate")
    dynamic_viscosity_temp = f_dynamic_viscosity(temp)
    
    return specific_mass_temp, thermal_conductivity_temp, dynamic_viscosity_temp

def get_sag(p0, p1, orig):
    lon_p0 = p0[0]
    lat_p0 = p0[1]
    z_p0 = p0[2]
    lon_p1 = p1[0]
    lat_p1 = p1[1]
    z_p1 = p1[2]

    diameter = 34.2e-3 # "Outside Diameter": 26.1e-3, # unit: m
    unit_weight = 21.56 # "Conductor Unit Weight": 10.89, # unit: N/m
    rts = 7.2e4 # "Rated Tensile Strength": 81800.0, # unit: N
    elasticity = 7.18e10 # "Modulus of Elasticity": 58.9e9, # unit: Pa
    coef_thermal = 2.06e-5 # "Coefficient of Thermal Expansion": 2.3e-5, # unit: /DegC
    area = 691.8e-6 # "Total Conductor Area": 402.6e-6, # unit: m2
    coeff_Al = 0.0039 # "Resistance temperature coefficient for Aluminium": 0.0039, # unit:/DegC
    R_20C = 4.58e-5 # "Resistance at 20 DegC": 2.65e-8 # unit: ohm/m
    temp_init = 15 # "Initial Temperature": 15 # unit: DegC
    # H_init = rts*0.25 # initial horizontal tension is 25% of Rated Tensile Strength

    Vll_rated = 230e3 # line rated voltage
    P_rated = 50e6 # power flow through the line
    temp_a = 30.0 # ambient temperature, unit: DegC
    wind_speed = 0.0 # unit: m/s
    wind_angle = 180.0 # 360° for north; 0° for undefined
    ice_thickness = 0.0; # unit: m
    ice_mass = 915 # unit: kg/m3
    g = 9.81 # Gravity of Earth, unit: m/s2

    d_hori = get_distance([lat_p0,lon_p0],[lat_p1,lon_p1])
    d_vert = abs(z_p0-z_p1)
    span = sqrt(d_hori*d_hori + d_vert*d_vert)
    
    if d_hori > 400:
        k_init = 0.35
    elif d_hori > 350:
        k_init = 0.33
    elif d_hori > 300:
        k_init = 0.31
    elif d_hori > 250:
        k_init = 0.29
    elif d_hori > 200:
        k_init = 0.27
    elif d_hori > 150:
        k_init = 0.25
    elif d_hori > 100:
        k_init = 0.23
    else:
        k_init = 0.21
    print("k_init first:", k_init)
    print("d_vert:",d_vert)
    if d_vert > 30:
        k_init = min(k_init, unit_weight*span*span/(2*d_vert*rts))

    print(k_init)
    H_init = rts*k_init
    
    sag_init = unit_weight*span*span/(8*H_init)
    Irms =  P_rated/(sqrt(3)*Vll_rated)

    # for Q_I
    Q_I_coeff_first = Irms*Irms*R_20C*coeff_Al
    Q_I_coeff_constant = Irms*Irms*R_20C*(1-coeff_Al*(20.0+273.0))
    # for Q_S
    k_a = 0.5 # absorption coefficient
    GHI = 1000 # unit: W/m2
    k_g = 0.3 # ground reflect
    Q_S_constant = k_a*(diameter+2*ice_thickness)*(1+k_g)*GHI
    # for Q_C
    line_angle = 180*atan((lon_p1-lon_p0)/(lat_p1-lat_p0+1e-8))/np.pi
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
    Nre = wind_speed * (diameter + 2*ice_thickness) * air_mass / air_viscosity
    if wind_speed > 1.1:
        Q_C_coeff_first = k_angle*(1.01+1.35*Nre**0.52)*k_f
        Q_C_constant = -k_angle*(1.01+1.35*Nre**0.52)*k_f*(temp_a+273.0)
    else:
        Q_C_coeff_first = k_angle*0.754*(Nre**0.6)*k_f
        Q_C_constant = -k_angle*0.754*(Nre**0.6)*k_f*(temp_a+273.0)
    # for Q_R
    k_e = 0.6
    k_s = 5.6704e-8
    Q_R_constant = -5.6704e-8*k_e*(diameter+2.0*ice_thickness)*(temp_a+273.0)**4
    Q_R_coeff_fourth = 5.6704e-8*k_e*(diameter+2.0*ice_thickness)
    # for new conductor temp under loading
    coef_sag = [-Q_R_coeff_fourth,0.0,0.0,Q_I_coeff_first-Q_C_coeff_first,Q_I_coeff_constant+Q_S_constant-Q_C_constant-Q_R_constant]
    r = np.roots(coef_sag)
    r = r[~np.iscomplex(r)]
    temp_load = np.absolute(r[r > 0.0]) # unit: K
    temp_load = temp_load - 273.0 # unit: DegC
    # calculate the new line sag at loaded condition
    ice_unit_weight = ice_mass*np.pi*ice_thickness*(diameter+ice_thickness)*g
    wind_unit_weight = 0.5*air_mass*(wind_speed*sin(phi))**2 *(diameter+2*ice_thickness)
    total_unit_weight = sqrt(wind_unit_weight**2+(unit_weight+ice_unit_weight)**2)

    H_load_second = (unit_weight*d_hori)**2 *area*elasticity/(24*H_init**2)-H_init+(temp_load-temp_init)*coef_thermal*area*elasticity
    H_load_constant = -(total_unit_weight*d_hori)**2 *area*elasticity/24

    coef_H = [1, H_load_second, 0.0, H_load_constant]
    r = np.roots(coef_H)
    r = r[~np.iscomplex(r)]
    H_load = np.absolute(r[r > 0.0])

    sag_load = total_unit_weight*span*span/(8*H_load)
    sag_angle = atan(wind_unit_weight/(ice_unit_weight+unit_weight))

    if z_p0 > z_p1:
        d0_hori = d_hori*(1+d_vert/(4*sag_load))/2
        d1_hori = d_hori - d0_hori
        sag1 = total_unit_weight*d1_hori**2 /(2*H_load)
        sag_elevation = z_p1-sag1*cos(sag_angle)
        dt = get_distance(orig,[lat_p0+d0_hori*(lat_p1-lat_p0)/d_hori,lon_p0+d0_hori*(lon_p1-lon_p0)/d_hori])
        print("d_vert:",d_vert)
        print("d_hori:",d_hori)
        print("sag_load:",sag_load)
        print("sag1:",sag1)
        print("sag_angle:",sag_angle)
        print("sag_elevation:",sag_elevation)
        print("total_unit_weight:",total_unit_weight)
        print("H_load:",H_load)

        print("dt:",dt)
        print("d0_hori:",d0_hori)
        print("d1_hori:",d1_hori)
        print("lon_p0:",lon_p0)
        print("lat_p0:",lat_p0)
        print("z_p0:",z_p0)
        print("lon_p1:",lon_p1)
        print("lat_p1:",lat_p1)
        print("z_p1:",z_p1)
        print("00000")
        return dt, sag_elevation 
    else:
        d0_hori = d_hori*(1-d_vert/(4*sag_load))/2
        d1_hori = d_hori - d0_hori
        sag0 = total_unit_weight*d0_hori**2 /(2*H_load)
        sag_elevation = z_p0-sag0*cos(sag_angle)
        dt = get_distance(orig,[lat_p0+d0_hori*(lat_p1-lat_p0)/d_hori,lon_p0+d0_hori*(lon_p1-lon_p0)/d_hori])
        print("d_vert:",d_vert)
        print("d_hori:",d_hori)
        print("sag_load:",sag_load)
        print("sag0:",sag0)
        print("sag_angle:",sag_angle)
        print("sag_elevation:",sag_elevation)
        print("total_unit_weight:",total_unit_weight)
        print("H_load:",H_load)
        print("dt:",dt)
        print("d0_hori:",d0_hori)
        print("d1_hori:",d1_hori)
        print("lon_p0:",lon_p0)
        print("lat_p0:",lat_p0)
        print("z_p0:",z_p0)
        print("lon_p1:",lon_p1)
        print("lat_p1:",lat_p1)
        print("z_p1:",z_p1)
        print("11111")
        return dt, sag_elevation

def project(data,box,lat,lon):
    x = int((lon-box["W"])/(box["E"]-box["W"])*data.shape[0])
    y = int((lat-box["S"])/(box["N"]-box["S"])*data.shape[1])
    return x,y

def get_distance(pos1, pos2):
    """Compute haversine distance between two locations
 
    ARGUMENTS
 
        pos1, pos2 (float tuple)   Specifies the two geographic endpoints as a
                                   (latitude,longtitude) tuple
    """
    lat1 = pos1[0]*math.pi/180
    lat2 = pos2[0]*math.pi/180
    lon1 = pos1[1]*math.pi/180
    lon2 = pos2[1]*math.pi/180
    a = math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371e3*(2*np.arctan2(np.sqrt(a),np.sqrt(1-a)))

def get_values(specs,path,res=10,box={}):

    img = Image.open(specs)
    data = np.array(img)
    pole_data = pd.read_csv("/Users/fxie2/Desktop/PSPS/vegetation/230kV_example.csv")
    y_origin = pole_data["latitude"][0]
    x_origin = pole_data["longitude"][0]
    
    bottom = math.floor(pole_data["latitude"].min())
    top = math.ceil(pole_data["latitude"].max())
    left = math.floor(pole_data["longitude"].min())
    right = math.ceil(pole_data["longitude"].max())

    xx = np.arange(left, right, 1.0/3600.0)
    yy = np.arange(top, bottom, -1.0/3600.0)
    print(xx)
    print(xx.max())
    print(xx.min())
    print(yy.max())
    print(yy.min())
    print("xx len:", len(xx))
    print("yy len:", len(yy))
    print(data.shape)
    f_data = interp2d(xx, yy, data, kind='linear')

    result = []
    k = 0
    p = {"dt":[],"zz":[],"high":[],"ground":[]}
    sags = {"dt": [], "sag": []}
    path_res = 10.0
    for line in path:
        p0 = line["p0"]
        p1 = line["p1"]
        lats_path = np.arange(p0["lat"], p1["lat"]+1e-16, (p1["lat"]-p0["lat"])/path_res)
        lons_path = np.arange(p0["lon"], p1["lon"]+1e-16, (p1["lon"]-p0["lon"])/path_res)
        print("lats_path len:", len(lats_path))
        print("lons_path len:", len(lons_path))
        zz = []
        tt = []
        for n in range(len(lats_path)):
            lat_path = lats_path[n]
            lon_path = lons_path[n]
            zz.append(f_data(lon_path,lat_path))
            tt.append(get_distance((y_origin,x_origin),(lat_path,lon_path)))
        d = get_distance((y_origin,x_origin),(lat_path,lon_path)) # distance in feet
        zz = np.array(zz).squeeze()
        t = np.array(tt).squeeze()
        z = (list(map(lambda x:float(x/res/res),list(map(interp1d(t,zz),np.arange(tt[0],tt[-1],1.0))))))
        result.append({
            "from" : p0,
            "to" :p1,
            "min":zz.min(),
            "max":zz.max(),
            "avg":np.round(zz.mean(),1),
            "std":np.round(zz.std(),1),
            "len":d,
            "t" : np.arange(tt[0],tt[-1],1.0),
            "z": np.array(z).round(3)*100,
        })
        sag_dt, sag_elevation = get_sag([p0["lon"],p0["lat"],pole_data["Height"][k]+f_data(p0["lon"],p0["lat"])],[p1["lon"],p1["lat"],pole_data["Height"][k+1]+f_data(p1["lon"],p1["lat"])],[y_origin,x_origin])
        p["dt"].append(get_distance((y_origin,x_origin),(p0["lat"],p0["lon"])))
        p["zz"].append(f_data(p0["lon"],p0["lat"]))
        p["high"].append(pole_data["Height"][k]+f_data(p0["lon"],p0["lat"]))
        p["ground"].append(pole_data["Elevation"][k])
        sags["dt"].append(sag_dt)
        sags["sag"].append(sag_elevation)
        k += 1
    p["dt"].append(get_distance((y_origin,x_origin),(p1["lat"],p1["lon"])))
    p["zz"].append(f_data(p1["lon"],p1["lat"]))
    p["high"].append(pole_data["Height"][k]+f_data(p1["lon"],p1["lat"]))
    p["ground"].append(pole_data["Elevation"][k])
    return result, p, sags

def get_data(csv_file): # default resolution is 1 ft
    """Get elevation data for region around path in CSV file.
    PARAMETERS
      csv_file: path along which elevation data is desired
                latitude,longitude columns must be labeled in first row
    """
    line_data = pd.read_csv(csv_file)
    bottom = math.floor(line_data["latitude"].min())
    top = math.ceil(line_data["latitude"].max())
    left = math.floor(line_data["longitude"].min())
    right = math.ceil(line_data["longitude"].max())

    tif_file = f"{file_folder}/elevation_{left}_{bottom}_{right}_{top}_10m.tif"
    # tif_file = f"ASTGTMV003_N37W123_dem.tif"

    if not os.path.exists(tif_file):
        # unfortunately the python API call to elevation.clip does not work correctly
        result = subprocess.run(["/usr/local/bin/eio",
            "--product","SRTM1",
            "clip",
            "-o",tif_file,
            "--bounds",str(left),str(bottom),str(right),str(top)],
            capture_output=True)
        return {
            "error" : result.returncode,
            "stderr" : result.stderr,
            "stdout" : result.stdout,
        }

    lats = line_data["latitude"]
    lons = line_data["longitude"]
    start = {"lat" : lats[0], "lon" : lons[0]}
    path = []
    for line in range(1,len(lats)):
        stop = {"lat" : lats[line], "lon" : lons[line]}
        path.append({"p0":start,"p1":stop})
        start = stop
    results, poles, sags = get_values(tif_file,path,10,{"N":top,"E":right,"W":left,"S":bottom})

    data = []
    for segment in results:
        data.append(pd.DataFrame({"t":segment["t"],"z":segment["z"]}).set_index("t"))
    pd.concat(data).to_csv(csv_file.replace(".csv","_elevation.csv"))

    return {
        "filename" : tif_file,
        "left" : left,
        "bottom" : bottom,
        "right" : right,
        "top" : top,
        "elevation" : results,
        "poles" : poles,
        "sags" : sags,
        }

if __name__ == '__main__':
    results = get_data("/Users/fxie2/Desktop/PSPS/vegetation/230kV_example.csv")
    if "error" in results.keys():
        print(results["stderr"])
    else:
        img = Image.open(results["filename"])
        img.show()
    plt.figure(1,figsize=(15,5))

    elevation = results["elevation"]
    poles = results["poles"]
    sags = results["sags"]

    t = []
    z = []
    for result in elevation:
        t.extend(result["t"])
        z.extend(result["z"])
    plt.plot(t,z,"-k",label="gound elevation") # elevation data from EIO
    plt.plot(poles["dt"],poles["zz"],"or",label="pole base elevation") # elevation data for pole
    plt.plot(poles["dt"],poles["high"],"og",label="pole top elevation") # elevation data for pole highth
    plt.plot(poles["dt"],poles["ground"],"g.",label="pole ground elevation") # elevation data for pole highth
    plt.plot(sags["dt"],sags["sag"],"b.",label="line sag elevation") # elevation data for line sag
    plt.legend()
    plt.xlabel('Line location (m)')
    plt.ylabel('Elevation (m)')
    plt.grid()
    start = [round(elevation[0]["from"]["lat"],4),round(elevation[0]["from"]["lon"],4)]
    stop = [round(elevation[-1]["to"]["lat"],4),round(elevation[-1]["to"]["lon"],4)]
    plt.title(f"{results['filename']} from {start} to {stop}")
    plt.show()























