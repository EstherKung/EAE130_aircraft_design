# %%
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from fuel_fraction import fuel_fraction
from functools import partial
from constraint_equations import *

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "mathtext.fontset": "stix",
    "font.size": 12
})

# %%

payload_mass = {
    'W_crew' : 200,
    "W_aim9x"   : 190,  # Weight AIM-9X, LBS
    "W_aim120"  : 360,  # Weight AIM-190C, LBS
    "W_mk83"    : 1000, # Weight MK-83 JDAM, LBS
    "W_avionics"  : 2500,    # Avionics weight, LBS
}

payload_config = {
    'combat': {
        'n_aim9x': 2,
        'n_aim120': 6,
        'n_mk83':0},
    'strike': {
        'n_aim9x': 2,
        'n_aim120': 0,
        'n_mk83': 4
    }
}

def fixed_payload(W_crew, n_aim9x, n_mk83, n_aim120, W_aim9x, W_aim120, W_mk83, W_avionics, store=1.0):
    W_payload = (n_aim9x * W_aim9x) + (n_mk83 * W_mk83) + (n_aim120 * W_aim120) * store
    W_crew_payload = W_crew + W_payload + W_avionics
    return W_crew_payload
    
W_fixed_payload = {
    'combat': fixed_payload(**payload_mass, **payload_config['combat']),
    'strike': fixed_payload(**payload_mass, **payload_config['strike']),
    'end': fixed_payload(**payload_mass, **payload_config['strike'], store=0.5)
}
# %%
def empty_weight(S: dict, T_0, TOGW):

    Engine_parts = {
        'dry': 0.521 * T_0**0.9,
        'oil': 0.082 * T_0**0.65,
        'rev': 0.034 * T_0,
        'control': 0.26 * T_0**0.5,
    }

    W_pneumatics = 9.33 * (Engine_parts['dry']/1000)**1.078
    W_engine = sum(Engine_parts.values()) + W_pneumatics

    Weight = {
        'wing': 9 * S['wing'],
        'htail':  4 * S['htail'],
        'vtail': 5.3 * S['vtail'], 
        'fuse': 4.8 * S['fuse_wet'], 
        'landing_gear': 0.045 * TOGW,
        'installed_engine': 1.3 * W_engine,
        'misc': 0.17 * TOGW
    }
    
    W_empty = sum(Weight.values())
    return W_empty

# %% [markdown]
# ## Inner Loop
# %% 
def weight_fraction(TOGW, fuel_fraction=0):
    used_fuel_weight = TOGW * fuel_fraction # how much fuel has been used

    weight_frac =  (TOGW - used_fuel_weight)/TOGW
    return weight_frac
# %%
def weight_convergence(W_guess, T_0, S,
                       mission,
                       W_fixed_payload=W_fixed_payload, fuel_fraction=fuel_fraction,
                       weight_fraction=weight_fraction,
                       tol=1e-6, iter=200):

    delta = np.inf 
    i = 0
    converge_history = []

    while delta > tol and i < iter:
        W_fuel = W_guess * fuel_fraction[mission]
        W_empty = empty_weight(S, T_0, TOGW=W_guess)
        W_total = W_fixed_payload[mission] + W_fuel + W_empty

        delta = abs(W_total - W_guess) / max(abs(W_total), 1e-9)
        converge_history.append((i, W_total))
        W_guess = W_total
        i +=1
    converged = (delta <= tol)
    print(W_total, W_empty, W_fuel)
    if not converged:
        print('asdlkgj??')
    W = W_guess * weight_fraction(W_guess)
    return W, converged, converge_history

# %% [markdown]
# ## Outer Loop

# %%
def thrust_from_wing_area(W_guess, S_wing, T_0, segment_function, mission, relax=1.0, tol =1e-3, max_iter=200):
    
    S = {'wing': S_wing, 'htail': 123.10441485216471, 'vtail': 107.19521577810403, 'fuse_wet': 702.3,}
    T_total = T_0

    for k in range(max_iter):
        W, _, _ = weight_convergence(W_guess, T_0, S, mission)

        W = W
        WS = W / S_wing
        TW = segment_function(WS)
        T_req = TW * W

        # Store history
        # T_hist.append(T_total)

        # Check outer convergence
        if abs(T_req - T_total) / max(abs(T_total), 1e-9) < tol:
            T_total = T_req
            break

        # Update thrust (optionally relaxed damping)
        T_total = (1 - relax) * T_total + relax * T_req
    return T_total

# %%
def TS_line(S_guess, W_guess, T_0, segment_function, mission, plot_styling={}, fill=False):
    T = [thrust_from_wing_area(W_guess, S_wing=S, T_0=T_0, segment_function=segment_function, mission=mission,)[0] for S in S_guess]

    if fill:
        plt.plot(S_guess, T, **plot_styling)
        plt.fill_between(S_guess, T, 0, color='gainsboro')
    else:
        return plt.plot(S_guess, T, **plot_styling)
# %%

def WS_line(W_guess, T_0, segment_function, mission, 
            weight_fraction=partial(weight_fraction, fuel_fraction=fuel_fraction['strike_end_mission']), # landing after fuel consumed from combat (sufficient for loiter & land) 
            unloaded_weight=W_fixed_payload['end'], # landing constraint  
            S_wing = 300, plot_styling={}, fill=False):

    S_guess = {'wing': S_wing,  'htail': 123.10441485216471, 'vtail': 107.19521577810403, 'fuse_wet': 702.3,}

    WL = segment_function
    W = [weight_convergence(W_guess=W_guess, T_0=T_0, S=S_guess, mission=mission)[0] - unloaded_weight for T_0 in T_0]
        
    S = [W_0 * weight_fraction(W_0)/WL for W_0 in W]
    
    if fill: 
        plt.plot(S, T_0, **plot_styling)
        plt.fill_between(S, T_0, 1e6, color='gainsboro')
    else:
        return plt.plot(S, T_0, **plot_styling)

