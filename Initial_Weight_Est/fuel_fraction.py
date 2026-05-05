import numpy as np

# Performance Parameters
p = {
    "AR": 3.5,        
    "Swet_Sref": 4.3,
    "Sref": 465,       
    "MTOW": 41508.866313,
}

mission_sequence = {
    'strike': [1, 2, 3, 4, 5, 2, 3, 4, 7, 8],
    'strike_mid_mission': [1, 2, 3, 4, 5],
    'strike_end_mission': [1, 2, 3, 4, 5, 2, 3, 4],
    'combat': [1, 2, 3, 6, 3, 4, 7, 8],
    'combat_mid_mission': [1, 2, 3],
    'combat_end_mission': [1, 2, 3, 6, 3, 4, 7],
    'off_mission': [1, 2, 4, 2, 4, 2, 7, 4, 8]
}

def isa_atmosphere(h_ft):
    T0, rho_sl, L, h_tp, T_tp, R, g, gam = 518.67, 0.002377, 0.003566, 36089.0, 389.97, 1716.49, 32.174, 1.4
    if h_ft <= h_tp:
        T = T0 - L * h_ft
        sigma = (T / T0) ** 4.2561
    else:
        T = T_tp
        sigma = 0.29707 * np.exp(-g / (R * T_tp) * (h_ft - h_tp))
    theta = T / T0
    return sigma * rho_sl, np.sqrt(gam * R * T), sigma, theta

def fuel_frac_refined(MTOW_initial, mission_list, AR = 3.5,  S_ref = 465, Swet_Sref =4.3, M_cruise = 0.85,
                      reserve=False, 
                      params={"h_cruise": 35000, "a_cruise": 972.6, "R_cruise": 700,
                                        "h_loiter": 30000, "M_loiter": 0.6, "a_loiter": 994.8, "E_loiter": 20,
                                        "M_dash": 0.85, "a_dash": 1116, "R_dash": 100, "C_cruise": 0.8, "C_dash": 1.0,
                                        "C_loiter": 0.7, "C_after": 1.8, "C_climb": 0.9, "C_taxi": 0.3, "C_to": 1.0, 
                                        "E_combat": 2, "T_sl_max": 29160, "T_sl_nom": 17800, "e_oswald": 0.825,
                                        "n_steps": 100, "K_LD": 14, "CD0": 0.01130449,}):
    
    k = 1.0 / (np.pi * AR * params["e_oswald"])
    g = 32.174
    
    # 1. Warm-up and Taxi
    ff_taxi = (1 - (15/60)*(params["C_taxi"]*(0.05 * params["T_sl_max"] / MTOW_initial)))
    W_exec = MTOW_initial * ff_taxi
    # 2. Takeoff
    ff_takeoff = 1 - (1.0 * (1/60) * (params["T_sl_max"] / W_exec))
    W_exec *= ff_takeoff
    
    x_climb_credit = 0.0

    def compute_climb(W_start):
        h_steps = np.linspace(0, params["h_cruise"], params["n_steps"] + 1)
        W = W_start
        dist_ft = 0.0
        for i in range(len(h_steps)-1):
            h1, h2 = h_steps[i], h_steps[i+1]
            rho1, _, sigma1, _ = isa_atmosphere(h1)
            rho2, _, sigma2, _ = isa_atmosphere(h2)
            
            # Velocities at start/end of step to calculate Delta Energy Height
            T1, T2 = params["T_sl_max"] * (sigma1**0.9), params["T_sl_max"] * (sigma2**0.9)
            V1 = np.sqrt(((W/S_ref)/(3*rho1*params["CD0"])) * ((T1/W) + np.sqrt(max((T1/W)**2 + 12*params["CD0"]*k, 0))))
            V2 = np.sqrt(((W/S_ref)/(3*rho2*params["CD0"])) * ((T2/W) + np.sqrt(max((T2/W)**2 + 12*params["CD0"]*k, 0))))
            
            # dhe = delta(h + V^2/2g)
            dhe = (h2 - h1) + (V2**2 - V1**2) / (2 * g)
            
            # Mid-point performance
            h_mid = (h1 + h2) / 2
            rho_m, _, sigma_m, theta_m = isa_atmosphere(h_mid)
            V_m = (V1 + V2) / 2
            CL = np.sqrt((params["CD0"]) / (3*k))
            CD = params["CD0"] + k * CL**2
            SFC = params["C_climb"]
            Ps = V_m * ((params["T_sl_max"] * sigma_m**0.9 / W) - (CD/CL)) 
            
            W *= np.exp(-((SFC/3600) * dhe) / Ps)
            dist_ft += (V_m / Ps) * dhe
        return W / W_start, dist_ft / 6076.12

    def compute_cruise_analytical(W_start, R_nm, x_credit):
        R_actual = max(R_nm - x_credit, 0) * 6076.12
        dR = R_actual / params["n_steps"]
        V = M_cruise * params["a_cruise"]
        rho, _, _, theta = isa_atmosphere(params["h_cruise"])
        SFC_s = (params["C_cruise"]) / 3600
        W = W_start
        for _ in range(params["n_steps"]):
            CL = (2 * W) / (rho * V**2 * S_ref) # Current weight
            CD = params["CD0"] + (k * CL**2)
            LD = CL / CD
            W *= np.exp(-(dR * SFC_s) / (V * LD)) # Discrete exponential
        return W / W_start

    def compute_loiter_iterative(W_start, E_min):
        dt = (E_min * 60) / params["n_steps"]
        rho, _, _, theta = isa_atmosphere(params["h_loiter"])
        SFC_s = (params["C_loiter"] / 3600)
        W = W_start
        for _ in range(params["n_steps"]):
            CL = np.sqrt(params["CD0"] / k) 
            CD = params["CD0"] + k * CL**2
            LD = CL / CD
            W *= np.exp(-(SFC_s * dt) / LD)
        return W / W_start 

    for m in mission_list:
        if m == 1: continue 
        elif m == 2: # Climb
            ratio, x_climb_credit = compute_climb(W_exec)
            W_exec *= ratio
        elif m == 3: # Cruise
            W_exec *= compute_cruise_analytical(W_exec, params["R_cruise"], x_climb_credit)
            x_climb_credit = 0.0 
        elif m == 4: # Descent
            W_exec *= 0.99 
        elif m == 5: # Dash
            V_d = params["M_dash"] * params["a_dash"]
            LD_d = 0.7 * (params["K_LD"] * np.sqrt(AR /Swet_Sref))
            W_exec *= np.exp(-(params["R_dash"]*6076.12*(params["C_dash"]/3600))/(V_d * LD_d))
        elif m == 6: # Combat
            LD_c = 0.2 * (params["K_LD"] * np.sqrt(AR / Swet_Sref))
            W_exec *= np.exp(-(params["E_combat"]*60*(params["C_after"]/3600))/LD_c)
        elif m == 7: # Loiter
            W_exec *= compute_loiter_iterative(W_exec, params["E_loiter"])
        elif m == 8: # Landing/Taxi
            W_exec *= 0.995 
    if reserve:
        return 1.06 * (1-(W_exec/MTOW_initial))
    else:
        return (1 - (W_exec / MTOW_initial))

# print(f"{'Mission Profile':<25} | {'Fuel Fraction'}")
# print("-" * 55)
# for name, sequence in mission_sequence.items():
    # res = fuel_frac_refined(sequence, p["MTOW"])
    # print(f"{name:<25} | {res:.4f}")

fuel_fraction = {
    'strike': fuel_frac_refined(mission_list=mission_sequence['strike'],  MTOW_initial=p["MTOW"]),
    'strike_mid_mission': fuel_frac_refined(mission_list=mission_sequence['strike_mid_mission'], MTOW_initial=p["MTOW"], reserve=False),
    'combat': fuel_frac_refined(mission_list=mission_sequence['combat'], MTOW_initial=p["MTOW"]),
    'combat_mid_mission': fuel_frac_refined(mission_list=mission_sequence['combat_mid_mission'], MTOW_initial=p["MTOW"], reserve=False),
    'strike_end_mission': fuel_frac_refined(mission_list=mission_sequence['strike_end_mission'], MTOW_initial=p["MTOW"], reserve=False),
    'combat_end_mission': fuel_frac_refined(mission_list=mission_sequence['combat_end_mission'], MTOW_initial=p["MTOW"], reserve=False),
}
