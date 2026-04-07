# %% [markdown]
# # The Constraint Diagram

# %%
import numpy as np
import matplotlib.pyplot as plt
from ambiance import Atmosphere # this package is in metric units
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "mathtext.fontset": "stix",
    "font.size": 12
})

a = lambda h: Atmosphere(h*0.3048).speed_of_sound * 3.2808399 # converts m/s to ft/s
rho = lambda h: Atmosphere(h*0.3047).density * 0.00194 # converts from kg/m-3 to slugs/ft-3

# %%
WL_range = np.linspace(0.01, 500, 1000) # bound for plots, adjust if needed

CLmax = {
    'takeoff': 1.7,
    'approach': 2.0
}

AERO_DEF = {
    'AR' : 3.5,
    'e' : 0.825,
    'c_Do' :  0.02190,
}

# %% [markdown]
# ## The Catapult Takeoff
# bing chilling equation from Raymer (5.10)
# $$ W/S = \frac{1}{2} \rho (V_{end}+V_{wod}+\Delta V_{thrust})^2  \frac{C_{Lmax, takeoff}}{1.21} $$
# 
# RFP: "take-off on a tropical day (89.8 $^\circ$ F)"  
# | Altitude  | Density             | Speed Units|  |
# |-----------|---------------------|------------|--|
# | sea level |2.19e-3 slugs/ft-3 | knots      |--|

# %%
def takeoff(V_end, V_wod=0, V_thrust=7, rho=2.19e-3, 
            CLmax_takeoff=CLmax['takeoff'], plot_styling={},fill=True):
    
    V_end_ft = V_end * 1.6878 # convert from kts to ft/s
    V_thrust = 7 * 1.6878
    # "tropical day" density
    # engine thrust typ. 3-10 kt
    WL = 1/2 * rho * (V_end_ft + V_wod + V_thrust)**2 * CLmax_takeoff/1.21
    
    if not plot_styling:
        return WL
    else: 
        if fill:
            plt.fill_betweenx((0, 50), WL, 300, color='gainsboro')
        return plt.axvline(x=WL, label= f'catapult endspeed {V_end} kt', **plot_styling)

# %% [markdown]
# ## Stall Speed
# we all know this one it's also Raymer (5.6)
# $$W/S = \frac{1}{2}\rho V_{stall}^2 C_{Lmax} $$
# 
# | Altitude  | Density             | Speed Units|  |
# |-----------|---------------------|------------|--|
# | custom    | custom              | knots      |--|
# 

# %%
def stall(V_stall, alt, rho=rho,
          CLmax=CLmax['approach'], plot_styling={}):
    rho = rho(alt)
    V = V_stall * 1.6878 # convert from kts to ft/s
    WL = 1/2 * rho * V**2 * CLmax #/0.8
    if not plot_styling:
        return WL 
    else:
      plt.fill_betweenx((0, 50), WL, 300, color='gainsboro')
      return plt.axvline(x=WL, label=f"stall at {V_stall:.0f} kts, {alt/1000:.0f}k ft", **plot_styling)

# %% [markdown]
# ## Climb
# according to Ramyer 5.31,
# $$ T/W >= G + 2 \sqrt{\frac{c_{Do}}{\pi e \text{AR}}} $$

# %%
def climb(WL, vertical_climb_rate, V_horizontal, c_Do = AERO_DEF['c_Do'], e = AERO_DEF['e'], AR = AERO_DEF['AR'], plot_styling={}):
    V = V_horizontal * 1.6878 # convert from kts to ft/s
    V_v = vertical_climb_rate/60 # convert from ft/min to ft/s
    G = V_v/V
    TW = G + 2 * np.sqrt(c_Do/(np.pi * e *AR))

    return plt.axhline(TW, **plot_styling)

# %% [markdown]
# ## Climb (the diff eq version)
# 
# [Ref.](https://github.com/sobester/ADRpy/blob/master/docs/ADRpy/notebooks/Initial%20Scaling%20of%20an%20Aircraft%20with%20ADRpy%20-%20the%20climb%20constraint.ipynb)
# 
# $$K_\mathrm{a} = 1+ \frac{V}{g}\frac{\mathrm{d}V}{\mathrm{d}h}$$
# 
# for first-order approximation, $K_a = 1$
# 
# $$\frac{T}{W} = \frac{qC_\mathrm{Dmin}}{\left(W/S\right)}+ \frac{k}{q}\left(\frac{W}{S}\right)\left[1 - \left(\frac{\mathrm{RoC}}{V}\right)^2\right] + K_\mathrm{a}\frac{\mathrm{RoC}}{V}$$

# %%
# def climb_curve(WL, vertical_climb_rate, V_horizontal, g=32.2, c_Do = AERO_DEF['c_Do'], e = AERO_DEF['e'], AR = AERO_DEF['AR'], rho=rho, plot_styling={}):
#     V = V_horizontal * 1.6878 # convert from kts to ft/s
#     RoC = vertical_climb_rate/60 # convert from ft/min to ft/s

#     #K_a = 1 + V/g * dVdh

#     K_a = 1
    
#     q = 1/2 * rho(0) * V**2 
    
#     k = 1/(np.pi * e * AR)

#     TW = q*c_Do/WL + k/q * WL * [1 - (RoC/V)**2] + K_a * (RoC/V)
    
#     if not plot_styling:
#         return TW
#     else:
#         return plt.plot(TW, label=f"climb rate at {vertical_climb_rate} ft/min", **plot_styling)
# %%
## The climb ceiling (the previous two is not suitable for this application)

def service_ceiling(WL, RoC, 
                    C_Do = AERO_DEF['c_Do'], e = AERO_DEF['e'], AR = AERO_DEF['AR'], rho=rho, plot_styling={}):
    rho = rho(50000);
    k = 1 / (np.pi * e * AR)
    RCmax = RoC / 60 # convert from ft/min to ft/s

    TW = RCmax * (C_Do/k)**(1/4) * (rho/2)**(1/2) * (WL)**(-1/2) + 2*(k*C_Do)**(1/2)
    if not plot_styling:
        return TW
    else: 
        return plt.plot(TW, label=f'service ceiling at 50k ft, climb rate {RoC} ft/min', **plot_styling)
# %% [markdown]
# ## Sustained Turn
# from Raymer (5.17), $ \dot{\psi}$ represents turn rate in rad/sec.
# $$ \text{[deg/sec]} / 57.3 = \text{rad/sec} $$
# then by Raymer (5.19),  
# $$ n = \sqrt{(\frac{\dot{\psi}V}{g})^2+1} $$
# 
# we get this equation  
# $$ T/W = \frac{qC_{Do}}{W/S} + \frac{W}{S}(\frac{n^2}{q\pi e\text{AR}}) $$
# 
# | Altitude  | Density             |Input Speed Unit| a         |
# |-----------|---------------------|------------|-----------|
# | 20,000 ft | 1.2664e-3 slugs/ft-3| Mach       |1036.8 ft/s|
# 
# 
# RFP Specifications  
# -  **required turn rate**: 8 deg/sec  
# - desired turn rate: 10 deg/sec  
# - note: mid-mission fuel weight  
# 

# %%
def sustained_turn(WL, Ma, alt, deg=8.0, g=32.2, a=a, rho=rho,
                    AR=AERO_DEF['AR'], e=AERO_DEF['e'], c_Do=AERO_DEF['c_Do'], 
                    mid_mission_weight_fraction=1-0.1867, plot_styling={}, fill=True):
    a = a(alt); rho = rho(alt)
    V = Ma * a # ft/s
    q = 1/2 * rho * V**2 #dynamic pressure

    turn_rate = deg/57.3 # in radians/sec
    n = np.sqrt((turn_rate * V / g)**2 + 1)
    
    TW = q * c_Do/WL + WL * mid_mission_weight_fraction**2 * (n**2)/(q*np.pi*AR*e)

    if not plot_styling:
        return TW 
    else: 
        if fill == True:
            plt.fill_between(WL, TW, 0, color='gainsboro')
        return plt.plot(WL, TW, label=rf"sustained turn at {deg}$^\circ$/sec", **plot_styling)

# %% [markdown]
# ## Load Factor
# 
# Uses same equation as the sustained turn, just the load factor $n$ is now the specified vertical load factor
# 
# 
# RFP Specifications 
# - **required load factor**: 7g mid-mission
# - desired load factor: 8g

# %%
def load_factor(WL, Ma, alt, n, g=32.2, a=a, rho=rho,
                AR=AERO_DEF['AR'], e=AERO_DEF['e'], c_Do=AERO_DEF['c_Do'], 
                plot_styling={}, mid_mission_weight_fraction=0.8, fill=True):
    
    WL = WL

    a = a(alt); rho = rho(alt)
    V = Ma * a
    q = 1/2 * rho * V**2 #dynamic pressure

    load_factor = n
    TW = q * c_Do/WL + WL * mid_mission_weight_fraction**2 * (load_factor**2)/(q*np.pi*AR*e)

    if not plot_styling:
        return TW
    else: 
        if fill == True:
            plt.fill_between(WL, TW, 0, color='gainsboro')
        return plt.plot(WL, TW, label=f"load factor {n}g", **plot_styling)
# %%
def instant_load_factor(Ma, alt, n, a=a, rho=rho,  
                        CL=CLmax['takeoff'], 
                        plot_styling={}):
    a = a(alt); rho = rho(alt)
    V = Ma * a
    q = 1/2 * rho * V**2 # 

    WL = q * CL / (n*0.85)

    if not plot_styling:
        return WL
    else:
        return plt.axvline(x=WL, label=f"vertical load factor {n}g", **plot_styling)
    

# %% [markdown]
# ## Dash Speed
# Just a casual equilibrium where $L = W$ and $T = D$ such that when we divide the two equations we get
# 
# $$\frac{T}{W} = \frac{qSc_D}{qSc_L} =\frac{qS(c_{D0}+kc_L^2)}{qSc_L}$$
# 
# so in terms of wing loading,  
# $$ \begin{gather}\frac{T}{W}=\frac{qc_{D0}}{\text{W/S}}+\frac{k}{q}\text{W/S}\end{gather}$$
# 
# where $k = \frac{1}{\pi e\text{AR}}$
# 
# 
# Sea Level Dash  
# - **required speed**: Mach 0.85  
# - desirable speed: Mach 0.90
# - $a$ = 1116.4 ft/s, $\rho$ = 2.377e-3 slugs/ft-3 
# 
# 30,000 ft Dash  
# - **required speed**: Mach 1.6  
# - desirable speed: Mach 2.0 
# - $a$ = 994.7 ft/s, $\rho$ = 0.8893e-3 slugs/ft-3
# 

# %%
def dash(WL, Ma, alt, a=a, rho=rho,
         e=AERO_DEF['e'], AR=AERO_DEF['AR'], c_Do=AERO_DEF['c_Do'], 
         plot_styling={}, fill=True):
    a = a(alt); rho = rho(alt)
    V = Ma * a
    q = 1/2 * rho * V**2 # dynamic pressure
    k = 1/ (np.pi*e*AR)
    TW = q* c_Do / WL + k/q * WL

    if not plot_styling:
        return TW
    else:
      if fill==True:
         plt.fill_between(WL, TW, 0, color='gainsboro')
      return plt.plot(WL, TW, label=f"Ma {Ma} dash, {alt/1000:.0f}k ft", **plot_styling)

# %% [markdown]
# ## Approach & Arrest
# Raymer defines approach speed as 1.2x the stall speed
# 
# from RFP, calculate to be 1.1x the stall speed
# 
# 

# %%
def approach(V_stall, rho=2.377e-3, CLmax_landing=CLmax['approach'], plot_styling={}):
    V = V_stall * 1.6878 # convert from kts to ft/s
    WL = 1/2 * rho * (1.1*V**2) * CLmax_landing
    
    if not plot_styling:
        return WL 
    else: 
        plt.fill_betweenx((0, 50), WL, 300, color='gainsboro')
        return plt.axvline(x=WL, label=f'approach at {1.1*V_stall:.0f} kts', **plot_styling)
