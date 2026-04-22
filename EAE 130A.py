import numpy as np
from scipy.optimize import fsolve
import pandas as pd
import matplotlib.pyplot as plt

# Aircraft Parameters
L = 50 # Length in ft
b = 60 # Wingspan in ft
h = 15 # Height in ft
c = 12 # Mean Aerodynamic Chord in ft
S_ref = 408 # Reference Wing Area in ft^2
S_wet = 2108 # Wetted Aircraft Area in ft^2
W_empty = 39000 # Empty Weight in lbs
W_full = 70000 # Max Takeoff Weight in lbs
W_fuel = W_full - W_empty # Fuel Weight in lbs
AR = b**2 / S_ref # Aspect Ratio
Swet_Sref = S_wet / S_ref # Wetted Area Ratio

# Performance Parameters
performance = {
    "M_cruise"  : 0.85,     # Cruise mach speed
    "h_cruise"  : 40000,    # Cruise altitude, FT
    "a_cruise"  : 994.3,    # Speed of sound at cruise, FT/s
    "R_cruise"  : 700,      # Cruise distance (Combat Radius), Nautical Miles
    "E_loiter"  : 20,       # Loiter time, min
    "C_cruise"  : 0.7,      # Engine SFC in Cruise, 1/hr
    "C_loiter"  : 0.7,      # Engine SFC in Loiter, 1/hr
    "C_after"   : 1.8,      # Engine SFC with Afterburner, 1/hr
    "E_combat"  : 2,        # Combat time, min
    "AR"        : 2.5,        # Estimated Aspect Ratio
    "Swet_Sref" : 5.16,        # Guess of Wetted Area Ratio
    "K_LD"      : 14,       # Factor in calculating L/D_max
}
