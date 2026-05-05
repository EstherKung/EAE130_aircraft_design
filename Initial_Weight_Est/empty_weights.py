import pandas as pd
import numpy as np

def weights(consts, TOGW, W_en=None, T_0=29160, W_dg=None):

    #Import Constants
    weight_const_df = pd.read_csv(consts)
    weight_const_df['Value'] = weight_const_df['Value'].astype(str).str.replace(',', '').astype(float)
    coeffs = dict(zip(weight_const_df['Weights Parameter'], weight_const_df['Value']))
    #display(coeffs, weight_const_df)

    #Assign Variables
    # W_dg = coeffs.get('W_dg', 0)

    if W_dg is not None:
        W_dg = W_dg
    else:
        W_dg = TOGW * 0.85
    N_z = coeffs.get('N_z', 0)
    L = coeffs.get("L", 0)
    D = coeffs.get("D", 0)
    W = coeffs.get("W", 0)
    W_l = coeffs.get("W_l", 0)
    N_l = coeffs.get("N_l", 0)
    L_m = coeffs.get("L_m", 0)
    L_n = coeffs.get("L_n", 0)
    N_nw = coeffs.get("N_nw", 0)
    K_vg = coeffs.get("K_vg", 0)
    L_d = coeffs.get("L_d", 0)
    K_d = coeffs.get("K_d", 0)
    N_en = coeffs.get("N_en", 0)
    L_s = coeffs.get("L_s", 0)
    L_d = coeffs.get("L_d", 0)
    D_e = coeffs.get("D_e", 0)
    V_t = coeffs.get("V_t", 0)
    V_i = coeffs.get("V_i", 0)
    V_p = coeffs.get("V_p", 0)
    N_t = coeffs.get("N_t", 0)
    S_fw = coeffs.get("S_fw", 0)
    # T = coeffs.get("T", 0)
    T = T_0
    SFC = coeffs.get("SFC", 0)
    if W_en is None:
        W_en = coeffs.get("W_en", 0)
    E_instl = coeffs.get("E_instl", 0)
    S_cs = coeffs.get("S_cs", 0)
    N_s = coeffs.get("N_s", 0)
    N_c = coeffs.get("N_c", 0)
    M = coeffs.get("M", 0)
    N_u = coeffs.get("N_u", 0)
    R_kva = coeffs.get("R_kva", 0)
    L_a = coeffs.get("L_a", 0)
    N_gen = coeffs.get("N_gen", 0)
    Ff_car = coeffs.get("Ff_car", 0)
    N_ci = coeffs.get("N_ci", 0) #number of crew equivalents where 1.0 if single pilot
    W_uav = coeffs.get("W_uav", 0) #uninstalled avionics weight typically between 800-1400
    L_tp = coeffs.get("L_tp", 0)
    L_sh = coeffs.get("L_sh", 0)


    comp_weights = {}

    #Fuselage
    comp_weights['W_fuse'] = Ff_car * 0.499 * W_dg**(0.35) * N_z**(0.25) * L**(0.5) * D**(0.849) * W**(0.685)

    #Main Landing Gear
    comp_weights["W_mlg"] = Ff_car * (W_l * N_l)**(0.25) * L_m**(0.973)

    #Nose Landing Gear
    comp_weights["W_nlg"] = Ff_car * (W_l * N_l)**(0.290) * L_n**(0.5) * (N_nw)**(0.525)

    #Engine Mounts
    comp_weights["W_eng_mount"] = 0.013 * N_en**(0.795) * T**(0.579) * N_z

    #Firewall 
    comp_weights["W_fire"] = 1.13 * S_fw 

    #Engine Section 
    comp_weights["W_eng_sec"] = 0.01 * W_en**(0.717) * N_en * N_z

    #Air induction system
    comp_weights["W_air_induc"] = 13.29 * K_vg * L_d**(0.643) * K_d**(0.182) * N_en**(1.498) * (L_s / L_d)**(-0.373) * D_e

    #Tailpipe
    comp_weights["W_tailpipe"] = 3.5 * D_e * L_tp * N_en 

    #Engine Cooling
    comp_weights["W_eng_cool"] = 4.55 * D_e * L_sh * N_en 

    #Oil Cooling 
    comp_weights["W_oil_cool"] = 37.82 * N_en**(1.023)

    #Starter 
    comp_weights["W_starter"] = 0.025 * T**(0.760) * N_en**(0.72)

    #Fuel System & Tanks
    comp_weights["W_fuel_systems"] = 7.45 * V_t**(0.47) * (1 + V_i / V_t)**(-0.095) * (1 + V_p / V_t) * N_t**(0.066) * N_en**(0.052) * ((T * SFC) / 1000)**(0.249)

    #Engine Installation
    comp_weights["W_eng_instl"] = W_en * E_instl

    #Flight Controls
    comp_weights["W_flight_cntrl"] = 36.28 * M**(0.003) * S_cs**(0.489) * N_s**(0.484) * N_c**(0.127)

    #Instruments
    comp_weights["W_instruments"] = 8.0 + 36.37 * N_en**(0.676) * N_t**(0.237) + 26.4*(1 + N_ci)**1.356

    #Hydraulics
    comp_weights["W_hydraulics"] = 37.23 * N_u**(0.664)

    #Electrical
    comp_weights["W_electrical"] = 172.2 * 1.45 * R_kva**(0.152) * N_c**(0.10) * L_a**(0.10) * N_gen**(0.091)

    #Avionics 
    comp_weights["W_avionic"] = 2.117 * W_uav**(0.933)

    #Furnishings 
    comp_weights["W_furn"] = 217.6 * N_c 

    #AC and anti-ice
    comp_weights["W_ac"] = 201.6 * ((W_uav + 200*N_c)/1000)**0.735

    #Handling
    comp_weights["W_hand"] = (3.2*10**(-4)) * W_dg


    # We add Flight Controls, Electrical, and Hydraulics to the fuselage weight, to get W_Fuse_NET
    weights_net = {}

    weights_net["W_fuse_net"] = comp_weights["W_fuse"] + comp_weights["W_flight_cntrl"] + comp_weights["W_hydraulics"] + comp_weights["W_electrical"] + comp_weights["W_instruments"] + comp_weights["W_hand"] + comp_weights["W_fire"] + comp_weights['W_air_induc']
    weights_net["W_pilot_space"] = comp_weights["W_ac"] + comp_weights["W_furn"] + comp_weights["W_avionic"]  
    weights_net["W_mlg"] = comp_weights["W_mlg"]
    weights_net["W_nlg"] = comp_weights["W_nlg"]
    weights_net["W_engine_net"] = comp_weights["W_eng_mount"] + comp_weights["W_eng_instl"] + comp_weights["W_eng_sec"] + comp_weights["W_eng_cool"] + comp_weights["W_oil_cool"] + comp_weights["W_starter"] + comp_weights["W_tailpipe"]
    weights_net["W_fuel_sys"] = comp_weights["W_fuel_systems"]

    # display(comp_weights, weights_net)

    #Totals
    total_sum = sum(comp_weights.values())
    total_sum2 = sum(weights_net.values())

    # print(weights_net)
    # for item, value in comp_weights.items():
    #     print(f"{item}: {value:.2f} lbs")
    # print(total_sum, total_sum2)
    return total_sum

#weights(consts="w_params.csv", TOGW=41508.866313)
