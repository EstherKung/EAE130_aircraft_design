# %%
import numpy as np

# Basic performance inputs
performance = {
    "M_cruise": 0.85,
    "h_cruise": 35000,
    "a_cruise": 972.6,
    "R_cruise": 700,
    "E_loiter": 20,
    "M_dash": 0.85,
    "a_dash": 1116,
    "R_dash": 100,
    "C_cruise": 0.8,
    "C_dash": 1.0,
    "C_loiter": 0.7,
    "C_after": 1.8,
    "C_climb": 0.9,
    "C_taxi": 0.3,
    "C_to": 1.0,
    "E_combat": 2,
    "AR": 2.85,
    "Swet_Sref": 4.3,
    "K_LD": 14,
    "CD0": 0.015,
    "e_oswald": 0.85,
    "WS": 70,
    "TW": 1.0,
    "n_climb": 10,
    "n_cruise": 10,
}

# Mission sequences
mission_sequence = {
    'strike': [1, 2, 3, 4, 5, 2, 3, 4, 7, 8],
    'strike_mid_mission': [1, 2, 3, 4, 5],
    'strike_end_mission': [1, 2, 3, 4, 5, 2, 3, 4],
    'combat': [1, 2, 3, 6, 3, 4, 7, 8],
    'combat_mid_mission': [1, 2, 3],
    'combat_end_mission': [1, 2, 3, 6, 3, 4, 7],
}

empty_statistic = {
    "A": 2.34,
    "C": -0.13,
    "MTOW_guess": 40000
}

# %%
def isa_atmosphere(h_ft):
    T0, rho0 = 518.67, 0.002377
    L, h_tp = 0.003566, 36089.0
    T_tp = 389.97
    R, g, gam = 1716.49, 32.174, 1.4

    if h_ft <= h_tp:
        T = T0 - L * h_ft
        sigma = (T / T0) ** 4.2561
    else:
        sigma_tp = (T_tp / T0) ** 4.2561
        T = T_tp
        sigma = sigma_tp * np.exp(-g / (R * T_tp) * (h_ft - h_tp))

    rho = sigma * rho0
    a = np.sqrt(gam * R * T)
    return rho, a

# %%
def fuel_frac(mission_sequence, A, C, MTOW_guess):

    p = performance

    k = 1.0 / (np.pi * p["AR"] * p["e_oswald"])
    Sref = MTOW_guess / p["WS"]
    g = 32.174

    V_cruise = p["M_cruise"] * p["a_cruise"]
    V_dash = p["M_dash"] * p["a_dash"]

    rho_sl, _ = isa_atmosphere(0.0)
    rho_cruise, _ = isa_atmosphere(p["h_cruise"])

    LD_max = p["K_LD"] * np.sqrt(p["AR"] / p["Swet_Sref"])

    # takeoff (taxi + TO burn)
    ff_takeoff = (1 - (15*60)*(p["C_taxi"]/3600)*(0.05*p["TW"])) * \
                 (1 - (60)*(p["C_to"]/3600)*(p["TW"]))

    def compute_climb(W_start_frac):
        h_steps = np.linspace(0, p["h_cruise"], p["n_climb"] + 1)
        W_frac, x_total = 1.0, 0.0

        for i in range(len(h_steps) - 1):
            h_lo, h_hi = h_steps[i], h_steps[i+1]
            h_mid = 0.5*(h_lo + h_hi)
            dh = h_hi - h_lo

            W_curr = MTOW_guess * W_start_frac * W_frac
            rho_mid, _ = isa_atmosphere(h_mid)

            TW_alt = p["TW"] * (rho_mid / rho_sl)

            disc = TW_alt**2 + 12*p["CD0"]*k
            V_sq = (W_curr/Sref)/(3*rho_mid*p["CD0"]) * (TW_alt + np.sqrt(max(disc,0)))
            V = np.sqrt(max(V_sq, 1.0))

            CL = 2*W_curr/(rho_mid*V**2*Sref)
            CD = p["CD0"] + k*CL**2
            D = 0.5*rho_mid*V**2*Sref*CD

            DoverT = D/(TW_alt*W_curr)
            one_minus = max(1 - DoverT, 1e-3)

            dhe = dh  # simplified energy height change
            ff = np.exp(-(p["C_climb"]/3600)*dhe/(V*one_minus))
            W_frac *= ff

            excess = TW_alt - D/W_curr
            if excess > 1e-6:
                x_total += dh / excess

        return W_frac, x_total

    def compute_cruise(W_start_frac, R_nm, x_credit=0.0):
        R_ft = max(R_nm*6076.12 - x_credit, 0.0)
        dR = R_ft / p["n_cruise"]
        C_s = p["C_cruise"]/3600
        W_frac = 1.0

        for _ in range(p["n_cruise"]):
            W_curr = MTOW_guess * W_start_frac * W_frac
            CL = 2*W_curr/(rho_cruise*V_cruise**2*Sref)
            CD = p["CD0"] + k*CL**2
            LD = CL/CD
            W_frac *= np.exp(-dR*C_s/(V_cruise*LD))

        return W_frac

    # other phases
    ff_dash = np.exp(-(p["R_dash"]*6076.12*p["C_dash"]/3600)/(V_dash*(0.7*LD_max)))
    ff_combat = np.exp(-(p["E_combat"]*60*p["C_after"]/3600)/(0.2*LD_max))
    ff_loiter = np.exp(-(p["E_loiter"]*60*p["C_loiter"]/3600)/(LD_max))

    ff_descent = 0.99
    ff_land = 0.995

    CFF = 1.0
    x_credit = 0.0

    for m in mission_sequence:
        if m == 1:
            CFF *= ff_takeoff
        elif m == 2:
            ff, x = compute_climb(CFF)
            CFF *= ff
            x_credit = x
        elif m == 3:
            CFF *= compute_cruise(CFF, p["R_cruise"], x_credit)
            x_credit = 0.0
        elif m == 4:
            CFF *= ff_descent
        elif m == 5:
            CFF *= ff_dash
        elif m == 6:
            CFF *= ff_combat
        elif m == 7:
            CFF *= ff_loiter
        elif m == 8:
            CFF *= ff_land

    return 1.06 * (1 - CFF)

# %%
fuel_fraction = {
    k: fuel_frac(v, **empty_statistic)
    for k, v in mission_sequence.items()
}

# %%
print("Fuel Fractions:")
for k, v in fuel_fraction.items():
    print(f"{k:25s}: {v:.4f}")