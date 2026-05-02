### HAVE empty_weights.py, w_params.csv, fuel_fraction.py
### then do from weights import weight_convergence

from functools import partial
from empty_weights import *
from fuel_fraction import *
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
def empty_weight(S: dict, T_0, TOGW, W_fuel, W_empty, 
weights = partial(weights, consts="w_params.csv"), consts={}, fuse=False):

    Engine_parts = {
        'dry': 0.521 * T_0**0.9,
        'oil': 0.082 * T_0**0.65,
        'rev': 0.034 * T_0,
        'control': 0.26 * T_0**0.5,
    }

    W_pneumatics = 9.33 * (Engine_parts['dry']/1000)**1.078
    W_engine = sum(Engine_parts.values()) + W_pneumatics

    W_dg = W_empty + W_fuel*0.5

    N_z = 10.5
    L_t = 15.5
    S_r2 = 25.03
    lam_VT = 0.4
    Lam_25mac = 0.612
    A_VT = 1.35
    M = 1.6

    F_w = 7
    B_h = 17.187
    A = 3.5
    tc_rt = 0.06
    lam_w = 0.5585
    S_csw = 144 
    Weight = {
        # 'wing': 9 * S['wing'],
        'wing': 0.0103 * (W_dg * N_z)**(0.5) * S['wing']**(0.622) * A**(0.785) * tc_rt**(-0.4) * (1 + lam_w)**(0.05) * (np.cos(Lam_25mac))**(-1.0) * (S_csw*S['wing']/625)**(0.04),
        # 'htail':  4 * S['htail'],
        'htail': 3.316 * (1 + F_w / B_h)**(-2.0) * ((W_dg * N_z) / 1000)**(0.260) * S['htail']**(0.806),
        # 'vtail': 5.3 * S['vtail'], 
        'vtail':  0.452 * (1 + 0)**(0.5) * (W_dg * N_z)**(0.488) * S['vtail']**(0.718) * M**(0.341) \
            * L_t**(-1) * (1 + S_r2 / S['vtail'])**(0.348) * A_VT**(0.223) * (1 + lam_VT)**(0.25) * (np.cos(Lam_25mac))**(-0.323),
        # 'fuse': 4.8 * S['fuse_wet'], 
        'else': weights(TOGW=TOGW, W_en=W_engine, T_0=T_0, W_dg=W_dg),
        # 'landing_gear': 0.045 * TOGW,
        # 'installed_engine': 1.3 * W_engine,
        # 'misc': 0.17 * TOGW
    }
    
    W_empty = sum(Weight.values())
    if fuse:
        return W_empty, Weight['else']
    else:
        return W_empty

def weight_fraction(TOGW, fuel_fraction=0):
    used_fuel_weight = TOGW * fuel_fraction # how much fuel has been used

    weight_frac =  (TOGW - used_fuel_weight)/TOGW
    return weight_frac

def weight_convergence(S, AR=3.5, M_cruise=0.85, Swet_Sref=4.3, 
                       mission='strike', T_0 = 29160, W_guess=50000, 
                       W_fixed_payload=W_fixed_payload, fuel_frac_refined=fuel_frac_refined,
                       tol=1e-6, iter=200, loud=False):

    delta = np.inf 
    i = 0
    converge_history = []
    W_empty = 0.6*W_guess
    while delta > tol and i < iter:
        W_fuel = W_guess * fuel_frac_refined(W_guess, mission_list=mission_sequence[mission],
                                             AR=AR,  S_ref = S['wing'], Swet_Sref = Swet_Sref, M_cruise = M_cruise)
        W_empty, W_fuse_empty = empty_weight(S, T_0, TOGW=W_guess, W_empty=W_empty, W_fuel=W_fuel, fuse=True)
        W_total = W_fixed_payload[mission] + W_fuel + W_empty

        delta = abs(W_total - W_guess) / max(abs(W_total), 1e-9)
        converge_history.append((i, W_total))
        W_guess = W_total
        i +=1
    converged = (delta <= tol)
    if loud:
        print(f"Converged MTOW: {W_total:.0f} lbs, Empty weight {W_empty:.0f} lbs, Fuel weight {W_fuel :.0f} lbs")
    if not converged:
        print('weight not converged!')
    W = W_guess
    W_dg = W_empty + 0.5*W_fuel
    return W, W_empty, W_fuel, W_dg, W_fuse_empty


for m in np.linspace(0.85, 1, 10):
    test = weight_convergence(S = {'wing': 465, 'htail': 123.10441485216471, 'vtail': 107.19521577810403, 'fuse_wet': 702.3,}, 
                            AR=3.5, M_cruise=m, Swet_Sref=4.3, 
                            mission='strike')
    print(test)