# Landing Gear Loads Calculator (in imperial units)

import numpy as np
import pandas as pd

# Aircraft Parameters 
MTOW = 49191
V_stall = 204.25 # [ft/s]
Main_tire_pressure = 280  
Nose_tire_pressure = 150
Number_of_main_tires = 2 
Number_of_nose_tires = 2

# Kinetic Energy per braked wheel 
W_Landing = 1.0*MTOW
g = 32.2                                                        # [ft/s^2]
KE_braking = (1/2*(W_Landing/g)*V_stall**2)/Number_of_main_tires

# Landing Gear Lengths (from OpenVSP)
N_a = 14.22
N_f = 11.27
M_a = 2.6
M_f = 5.55
B = 16.82
H = 5.91

# Tire Loads (Raymer 2024)
Load_margin = 1.25
Max_main_static_load = Load_margin*MTOW*(N_a/B)
Max_nose_static_load = Load_margin*MTOW*(M_f/B)
Min_nose_static_load = Load_margin*MTOW*(M_a/B) 
Dynamic_brake_loading_nose = Load_margin*50*MTOW*(H/B)/g

# Load per Tire (Raymer 2024)
Load_per_main_tire = Max_main_static_load/Number_of_main_tires
Load_per_nose_tire = Max_nose_static_load/Number_of_nose_tires

# Statistical Main Tire Sizing Parameters (Raymer 2024) 
A_d = 1.59
B_d = 0.302
A_w = 0.098
B_w = 0.467
W_W_main = Load_per_main_tire
W_W_nose = Load_per_nose_tire
W_allowed = Number_of_main_tires*W_W_main + Number_of_nose_tires*W_W_nose

# Statistical Main Tire Sizing (Raymer 2024)
Main_tire_diameter = (A_d*(W_W_main)**B_d)
Main_tire_radius = Main_tire_diameter/2
Main_tire_width = A_w*(W_W_main)**B_w

# Statistical Nose Tire Sizing (Raymer 2024)
Nose_to_Main_Ratio = 0.7
Nose_tire_diameter = Nose_to_Main_Ratio*Main_tire_diameter
Nose_tire_radius = Nose_to_Main_Ratio*Main_tire_radius
Nose_tire_width = Nose_to_Main_Ratio*Main_tire_width

# Load Checks (Raymer 2024)
Load_check_M_a = M_a/B
Load_check_M_f = M_f/B

if Load_check_M_a > 0.05:
         print(f'M_a/B ratio "{Load_check_M_a:.2f}" is sufficient, it is greater than 0.05')
else: 
         print(f'M_a/B ratio "{Load_check_M_a:.2f}" is not sufficient, decrease B value and/or increase M_a value to increase the ratio to above 0.05')
   
if Load_check_M_f < 0.20:
         print(f'M_f/B ratio "{Load_check_M_f:.2f}" is sufficent, it is less than 0.20')
else: 
         print(f'M_f/B ratio "{Load_check_M_f:.2f}" is not sufficent, increase B value and/or decrease M_f to decrease the ratio to below 0.20')

# Tire Sizing Table
data = { 
    "Parameter": ["Total weight allowed",
                  "Kinetic energy per braked wheel",
                  "Main tire diameter",
                  "Nose tire diameter",
                  "Main tire radius",
                  "Nose tire radius",
                  "Main tire width",
                  "Nose tire width",
                  "Main tire pressure",
                  "Nose tire pressure"],

    "Value": [W_allowed, 
              KE_braking, 
              Main_tire_diameter,
              Nose_tire_diameter,
              Main_tire_radius,
              Nose_tire_radius,
              Main_tire_width,
              Nose_tire_width,
              Main_tire_pressure,
              Nose_tire_pressure],

    "Units": ["lbf",
              "ft*lb/s",
              "in",
              "in",
              "in", 
              "in", 
              "in", 
              "in", 
              "psi", 
              "psi"]
}

table = pd.DataFrame(data)
print("\nTire Sizing Table\n")
print(table)