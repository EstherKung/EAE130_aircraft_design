# %%
import numpy as np
# Ryuya Iwase
# %%
performance = {
    "M_cruise"  : 0.85,     # Cruise mach speed
    "h_cruise"  : 35000,    # Cruise altitude, FT
    "a_cruise"  : 972.6,    # Speed of sound at cruise, FT/s
    "R_cruise"  : 700,      # Cruise distance (Combat Radius), Nautical Miles
    "E_loiter"  : 20,       # Loiter time, min
    "M_dash"    : 0.85,     # Dash mach speed
    "a_dash"    : 1116,     # Speed of sound at SL, FT/s
    "R_dash"    : 100,      # Dash distnace, Nautical Miles
    "C_cruise"  : 0.72,      # Engine SFC in Cruise, 1/hr
    "C_dash"    : 0.76,      # Engine SFC in Dash (Max-non-afterburning), 1/hr
    "C_loiter"  : 0.81,      # Engine SFC in Loiter, 1/hr
    "C_after"   : 1.94,      # Engine SFC with Afterburner, 1/hr
    "E_combat"  : 2,        # Combat time, min
    "AR"        : 3.5,        # Estimated Aspect Ratio
    "Swet_Sref" : 3.79,        # Guess of Wetted Area Ratio
    "K_LD"      : 14,       # Factor in calculating L/D_max
}

# %%
mission_sequence = {
    'strike': [1, 2, 3, 4, 5, 2, 3, 4, 7, 8], 
    # ^ TO, Climb, Cruise, Descent, SL Dash, Climb, Cruise, Descent, Loiter, Land. (The Strike mission)
    'strike_mid_mission': [1, 2, 3, 4, 5],
    'strike_end_mission': [1, 2, 3, 4, 5, 2, 3, 4],
    
    'combat': [1, 2, 3, 6, 3, 4, 7, 8],
    # ^ TO, Cimb, Cruise, Combat, Cruise, Descent, Loiter, Land. (Combat Mission)
    'combat_mid_mission': [1, 2, 3,],
    'combat_end_mission': [1, 2, 3, 6, 3, 4, 7],

    'off_mission': [1, 2, 4, 2, 4, 2, 7, 4, 8]
    # ^ TO, Climb, Descent, Climb, Descent, Climb, Loiter, Descent, Land
}

empty_statistic = {
    "A": 2.34,
    "C": -0.13,
    "MTOW_guess": 53200 
}

# %%
def fuel_frac(mission_sequence, A, C, MTOW_guess):
    # Fixed Fuel Fractions
    ff_to = 0.970
    ff_climb = 0.985
    ff_descent = 0.99
    ff_land = 0.995


    # Cruise Fuel Fraction
    def cruise_wf(M_cruise, h_cruise, a_cruise, R_cruise, E_loiter, M_dash, a_dash, R_dash, C_cruise, C_dash, C_loiter, C_after, E_combat,
               AR, Swet_Sref, K_LD):
        R_cruise_ft = R_cruise * 6076.12
        V_cruise = M_cruise * a_cruise

        LD_max = K_LD * np.sqrt(AR / Swet_Sref)
        LD_cruise = 0.866 * LD_max

        C_cruise_s = C_cruise / 3600

        wf_cruise = np.exp((-R_cruise_ft * C_cruise_s) / (V_cruise * LD_cruise))
        
        # print(wf_cruise)
        return wf_cruise
    
    ff_cruise = cruise_wf(**performance)


    # Dash Fuel Fraction
    def dash_wf(M_cruise, h_cruise, a_cruise, R_cruise, E_loiter, M_dash, a_dash, R_dash, C_cruise, C_dash, C_loiter, C_after, E_combat,
             AR, Swet_Sref, K_LD):
        V_dash = M_dash * a_dash
        R_dash_ft = R_dash * 6076.12
        C_dash_s = C_dash / 3600
        
        LD_max = K_LD * np.sqrt(AR / Swet_Sref)
        LD_dash = 0.700 * LD_max

        wf_dash = np.exp((-R_dash_ft * C_dash_s) / (V_dash * LD_dash))    
        # print(f"dash:{wf_dash}")

        return wf_dash
    
    ff_dash = dash_wf(**performance)


    # Loiter Fuel Fraction
    def loiter_wf(M_cruise, h_cruise, a_cruise, R_cruise, E_loiter, M_dash, a_dash, R_dash, C_cruise, C_dash, C_loiter, C_after, E_combat,
               AR, Swet_Sref, K_LD):
        E_loiter_s = E_loiter * 60
        LD_max = K_LD * np.sqrt(AR / Swet_Sref)
        C_loiter_s = C_loiter / 3600

        wf_loiter = np.exp((-E_loiter_s * C_loiter_s) / LD_max)

        # print(f"loiter: {wf_loiter}")
        return wf_loiter
    
    ff_loiter = loiter_wf(**performance)


    # Combat Fuel Fraction
    def combat_wf(M_cruise, h_cruise, a_cruise, R_cruise, E_loiter, M_dash, a_dash, R_dash, C_cruise, C_dash, C_loiter, C_after, E_combat,
               AR, Swet_Sref, K_LD):
        E_combat_s = E_combat * 60
        C_after_s = C_after / 3600
        LD_max = K_LD * np.sqrt(AR / Swet_Sref)
        LD_combat = LD_max * 0.2

        wf_combat = np.exp((-E_combat_s * C_after_s) / LD_combat)
        # print(f"combat: {wf_combat}")
        return wf_combat
    
    ff_combat = combat_wf(**performance)

    # mid mission fuel fraction keeps track of the fuel fraction mid-mission, after descent stages
    MMF = np.empty(2)

    ## Combined Mission Fuel Fraction
    CFF = 0
    counter = 0
    for i, m_seq in enumerate(mission_sequence):
        if m_seq == 1:
            #print(f"Takeoff Fuel Fraction is: {ff_to}")
            CFF = ff_to
        if m_seq == 2:
            #print(f"Climb Fuel Fraction is: {ff_climb}")
            CFF = CFF * ff_climb
        if m_seq == 3:
            #print(f"Cruise Fuel Fraction is: {np.round(ff_cruise, 3)}")
            CFF = CFF * ff_cruise
            MMF[counter] = CFF
            counter = counter + 1
            #print(f"Mid mission fuel fraction is: {np.round(MMF, 3)}")
        if m_seq == 4:
            #print(f"Descent Fuel Fraction is: {ff_descent}")
            CFF = CFF * ff_descent
        if m_seq == 5:
            #print(f"SL Dash Fuel Fraction is: {np.round(ff_dash, 3)}")
            CFF = CFF * ff_dash
        if m_seq == 6:
            #print(f"Combat Fuel Fraction is: {np.round(ff_combat, 3)}")
            CFF = CFF * ff_combat
        if m_seq == 7:
            #print(f"Loiter Fuel Fraction is: {np.round(ff_loiter, 3)}")
            CFF = CFF * ff_loiter
        if m_seq == 8:
            #print(f"Landing Fuel Fraction is: {ff_land}")
            CFF = CFF * ff_land

        TFF = 1.06 * (1 - CFF)

    return TFF

# %%
fuel_fraction = {
    'strike': fuel_frac(mission_sequence=mission_sequence['strike'], **empty_statistic),
    'strike_mid_mission': fuel_frac(mission_sequence=mission_sequence['strike_mid_mission'], **empty_statistic),
    'combat': fuel_frac(mission_sequence=mission_sequence['combat'], **empty_statistic),
    'combat_mid_mission': fuel_frac(mission_sequence=mission_sequence['combat_mid_mission'], **empty_statistic),
    'strike_end_mission': fuel_frac(mission_sequence=mission_sequence['strike_end_mission'], **empty_statistic),
    'combat_end_mission': fuel_frac(mission_sequence=mission_sequence['combat_end_mission'], **empty_statistic),
}
# %%
# print(fuel_fraction)
print(f"{'Mission Profile':<25} | {'Fuel Fraction'}")
print("-" * 55)
for name, sequence in mission_sequence.items():
    res = fuel_frac(sequence, **empty_statistic)
    print(f"{name:<25} | {res:.4f}")