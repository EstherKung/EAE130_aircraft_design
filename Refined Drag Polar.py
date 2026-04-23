import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ambiance import Atmosphere

plt.rcParams["font.family"] = "Times New Roman"

# Convert altitude
h_cruise_ft = 35000
h_cruise_m = h_cruise_ft * 0.3048

# Initialize atmosphere
atm = Atmosphere(h_cruise_m)
atm_SL = Atmosphere(0)

# Extract properties (SI units)
rho_alt = atm.density[0]
mu = atm.dynamic_viscosity[0]
T = atm.temperature[0]
P = atm.pressure[0]
a = atm.speed_of_sound[0]

rho_SL = atm_SL.density[0]
mu_SL = atm_SL.dynamic_viscosity[0]
T_SL = atm_SL.temperature[0]
P_SL = atm_SL.pressure[0]
a_SL = atm_SL.speed_of_sound[0]

#print("Atmospheric properties at Cruise Altitude:")
#print("Density: ", rho)
#print("Dynamic Viscosity: ", mu)
#print("Temperature: ", T)
#print("Pressure: ", P)
#print("Speed of Sound at Cruise: ", a)

# Cruise @ 35,000 ft
M_cruise = 0.85
V_cruise = M_cruise * a
q_cruise = 0.5 * rho_alt * V_cruise**2
#print("Cruise Pressure: ", P)
#print("Cruise Velocity: ", V_cruise)
#print("Dynamic pressure at cruise: ", q_cruise)

# Dash(M = 1.6 at 35,000 ft)
M_dash = 1.6
V_dash = M_dash * a
q_dash = 0.5 * rho_alt * V_dash**2

# Takeoff
M_TO = 0.24
V_TO = M_TO * a
q_TO = 0.5 * rho_SL * V_TO**2

# Landing
M_L = 0.18
V_L = M_L * a
q_L = 0.5 * rho_SL * V_L**2

# Aircraft Geometric Parameters
W_lb = 49191 # lbs (MTOW)
W_kg = W_lb * 0.453592 # kg
b = 40.34229                                      # Wingspan
b_flap = (0.694061 - 0.188388) * b          # Flap Span (from OpenVSP)
S_ref = 465                                 # ft^2 Reference Wing Area
S_ref_m2 = S_ref * 0.092903 # m^2
S_wet = 1761.678                            # ft^2 Wetted Surface Area of Aircraft
S_flap = 251                             # ft^2 Flap Area
S_slats = 360                            # ft^2 Slat Area
lambda_ = 35                                # degrees, Leading Edge Sweep Angle  
lambda_deg2rad = (np.pi * lambda_) / 180    # Convert Leading Edge Sweep Angle to Radians
k = 1.33e-5                             # Skin Roughness Value

# Component Diameters [ft]
d_fuselage = 6.02 # ft Diameter of Fuselage
d_aim_9x = 0.5 # ft Diameter of AIM-9X Sidewinder Missile
d_aim_120 = 0.5833 # ft Diameter of AIM-120C AMRAAM Missile
d_mk_83 = 1.166 # ft Diameter of MK-83 General Purpose Bomb
d_pylon = 0.5 # [ft] Diameter of Armament Pylon

AR_clean = (b**2) / S_ref   # Aspect Ratio Clean Configuration
AR_flap = (b_flap**2) / S_flap   # Aspect Ratio Flap Deployment Configuration

#e_wing = (4.61*(1-0.045*((AR_clean)**0.68)) * (np.cos(35)) ** 0.15) - 3.1 (Doesn't Work) (Raymer 12.49)
# Taking average values from Metabook as Raymer's estimation is too high (Metabook Table 4.2)
e = 0.825 
e_TO = 0.775
e_landing = 0.725
K_clean = 1 / (np.pi * AR_clean * e) # Induced Drag Factor for Clean Configuration
K_TO = 1 / (np.pi * AR_flap * e_TO)
K_landing = 1 / (np.pi * AR_flap * e_landing)
#print("Induced Drag Factor for Clean Configuration: ", K_clean)
#print("Induced Drag Factor for Takeoff Configuration: ", K_TO)
#print("Induced Drag Factor for Landing Configuration: ", K_landing)

# Estimating Zero-Lift Drag using Component Build-up Method (Cruise Conditions)
#CD0 = 1/S_ref
#C_fc = ? # Skin Friction Coefficient
#FF_c = ? # Form Factor (FF = 1 Supersonic)
#Q_c = ? # Interference Factor (Q = 1 for Subsonic)
#S_wet_c = ? # Wetted Surface Area of Componenet
#CD_misc = 
#CD_L_P = ? #Leakage/Protuerbance
#CD_wave = ?

#Re_c = (rho_cruise * V_cruise * l_c) / mu_cruise # Reynolds Number for Component
#R_cutoff_subsonic = 38.21 * (l_c / k) ** 1.053 # Raymer (12.28)
#R_supersonic = 44.62 * ((l_c / k) ** 1.053) * (M_dash ** 1.16) # (Raymer 12.29)

# Length of Aircraft Components [ft]
l_fuselage_c = 50 
l_wing_cbar = 12.80             # Mean Aerodynamic Chord
l_HT_cbar = 7.89                # Horizontal Stabilizer Chord
l_VT_cbar = 6.35                # Vertical Stabilizer Chord
l_pylon = 7 # [ft] Length of Armament Pylon
l_droptank = 8.960              # Drop Tank
l_aim_9x = 10                   # AIM-9X Sidewinder Missile Length
l_aim_120 = 12                  # AIM-120C AMRAAM Missile Length
l_mk_83 = 9.834                # MK-83 General Purpose Bomb Length

# Wetted Surface Area of Aircraft Components [ft^2]
S_wet_fuselage = 653.186
S_wet_wing = 467.833
S_wet_HT = 128.031
S_wet_VT = 99.377
S_wet_intake = 146.509 # Air Inlet
S_wet_droptank = 112.682 # Drop Tank
S_wet_aim_9x = 21.587
S_wet_aim_120 = 27.415 
S_wet_mk_83 = 31.873
S_wet_pylon_center = 21.314 # Centerline Pylon (Carrying Drop Tank)
S_wet_pylon_outer = 10.375 # Average of 3 Outer Pylons

# Cutoff Reynolds Number for Commponents
# Subsonic Flight
R_cutoff_fuselage = 38.21 * (l_fuselage_c / k) ** 1.053
R_cutoff_wing = 38.21 * (l_wing_cbar / k) ** 1.053
R_cutoff_HT = 38.21 * (l_HT_cbar / k) ** 1.053
R_cutoff_VT = 38.21 * (l_VT_cbar / k) ** 1.053
R_cutoff_droptank = 38.21 * ((l_wing_cbar / 2) / k) ** 1.053 
R_cutoff_aim_9x = 38.21 * (l_aim_9x / k) ** 1.053
R_cutoff_aim_120 = 38.21 * (l_aim_120 / k) ** 1.053
R_cutoff_mk_83 = 38.21 * (l_mk_83 / k) ** 1.053

# Transonic or Supersonic (cd = cruise/dash)
R_cutoff_fuselage_cd = 44.62 * ((l_fuselage_c / k) ** 1.053) * (M_dash ** 1.16)
R_cutoff_wing_cd = 44.62 * ((l_wing_cbar / k) ** 1.053) * (M_dash ** 1.16)
R_cutoff_HT_cd = 44.62 * ((l_HT_cbar / k) ** 1.053) * (M_dash ** 1.16)
R_cutoff_VT_cd = 44.62 * ((l_VT_cbar / k) ** 1.053) * (M_dash ** 1.16)
R_cutoff_droptank_cd = 44.62 * ((l_wing_cbar / 2 / k) ** 1.053) * (M_dash ** 1.16)
R_cutoff_aim_9x_cd = 44.62 * ((l_aim_9x / k) ** 1.053) * (M_dash ** 1.16)
R_cutoff_aim_120_cd = 44.62 * ((l_aim_120 / k) ** 1.053) * (M_dash ** 1.16)
R_cutoff_mk_83_cd = 44.62 * ((l_mk_83 / k) ** 1.053) * (M_dash ** 1.16)

# Laminar Skin Friction Coefficient for Components
C_fc_lam_fuselage = 1.328 / np.sqrt(R_cutoff_fuselage)
C_fc_lam_wing = 1.328 / np.sqrt(R_cutoff_wing)
C_fc_lam_HT = 1.328 / np.sqrt(R_cutoff_HT)
C_fc_lam_VT = 1.328 / np.sqrt(R_cutoff_VT)
C_fc_lam_droptank = 1.328 / np.sqrt(R_cutoff_droptank)
C_fc_lam_aim_9x = 1.328 / np.sqrt(R_cutoff_aim_9x)
C_fc_lam_aim_120 = 1.328 / np.sqrt(R_cutoff_aim_120)
C_fc_lam_mk_83 = 1.328 / np.sqrt(R_cutoff_mk_83)
#print("Laminar Skin Friction Coefficients:")
#print("Fuselage: ", C_fc_lam_fuselage)
#print("Wing: ", C_fc_lam_wing)
#print("Horizontal Tail: ", C_fc_lam_HT)
#print("Vertical Tail: ", C_fc_lam_VT)
#print("Drop Tank: ", C_fc_lam_droptank)

# Turbulent Skin Friction Coefficient for Components
# Takeoff / Landing
C_fc_turb_fuselage_c = 0.455 / ((np.log10(R_cutoff_fuselage_cd) ** 2.58) * (1 + 0.144 * M_L**2) ** 0.65)
C_fc_turb_wing_c = 0.455 / ((np.log10(R_cutoff_wing_cd) ** 2.58) * (1 + 0.144 * M_L**2) ** 0.65)
C_fc_turb_HT_c = 0.455 / ((np.log10(R_cutoff_HT_cd) ** 2.58) * (1 + 0.144 * M_L**2) ** 0.65)
C_fc_turb_VT_c = 0.455 / ((np.log10(R_cutoff_VT_cd) ** 2.58) * (1 + 0.144 * M_L**2) ** 0.65)
C_fc_turb_droptank = 0.455 / ((np.log10(R_cutoff_droptank_cd) ** 2.58) * (1 + 0.144 * M_L**2) ** 0.65)
C_fc_turb_aim_9x = 0.455 / ((np.log10(R_cutoff_aim_9x_cd) ** 2.58) * (1 + 0.144 * M_L**2) ** 0.65)
C_fc_turb_aim_120 = 0.455 / ((np.log10(R_cutoff_aim_120_cd) ** 2.58) * (1 + 0.144 * M_L**2) ** 0.65)
C_fc_turb_mk_83 = 0.455 / ((np.log10(R_cutoff_mk_83_cd) ** 2.58) * (1 + 0.144 * M_L**2) ** 0.65)

# Turbulent Skin Friction Coefficient for Components
#Cruise
C_fc_turb_fuselage_c = 0.455 / ((np.log10(R_cutoff_fuselage_cd) ** 2.58) * (1 + 0.144 * M_cruise**2) ** 0.65)
C_fc_turb_wing_c = 0.455 / ((np.log10(R_cutoff_wing_cd) ** 2.58) * (1 + 0.144 * M_cruise**2) ** 0.65)
C_fc_turb_HT_c = 0.455 / ((np.log10(R_cutoff_HT_cd) ** 2.58) * (1 + 0.144 * M_cruise**2) ** 0.65)
C_fc_turb_VT_c = 0.455 / ((np.log10(R_cutoff_VT_cd) ** 2.58) * (1 + 0.144 * M_cruise**2) ** 0.65)
C_fc_turb_droptank = 0.455 / ((np.log10(R_cutoff_droptank_cd) ** 2.58) * (1 + 0.144 * M_cruise**2) ** 0.65)
C_fc_turb_aim_9x = 0.455 / ((np.log10(R_cutoff_aim_9x_cd) ** 2.58) * (1 + 0.144 * M_cruise**2) ** 0.65)
C_fc_turb_aim_120 = 0.455 / ((np.log10(R_cutoff_aim_120_cd) ** 2.58) * (1 + 0.144 * M_cruise**2) ** 0.65)
C_fc_turb_mk_83 = 0.455 / ((np.log10(R_cutoff_mk_83_cd) ** 2.58) * (1 + 0.144 * M_cruise**2) ** 0.65)
#print("Turbulent Skin Friction Coefficients at Cruise Conditions:")
#print("Fuselage: ", C_fc_turb_fuselage_c)
#print("Wing: ", C_fc_turb_wing_c)
#print("Horizontal Tail: ", C_fc_turb_HT_c)
#print("Vertical Tail: ", C_fc_turb_VT_c)
#print("Drop Tank: ", C_fc_turb_droptank)

# Supersonic Dash
C_fc_turb_fuselage_d = 0.455 / ((np.log10(R_cutoff_fuselage_cd) ** 2.58) * (1 + 0.144 * M_dash**2) ** 0.65)
C_fc_turb_wing_d = 0.455 / ((np.log10(R_cutoff_wing_cd) ** 2.58) * (1 + 0.144 * M_dash**2) ** 0.65)
C_fc_turb_HT_d = 0.455 / ((np.log10(R_cutoff_HT_cd) ** 2.58) * (1 + 0.144 * M_dash**2) ** 0.65)
C_fc_turb_VT_d = 0.455 / ((np.log10(R_cutoff_VT_cd) ** 2.58) * (1 + 0.144 * M_dash**2) ** 0.65)
C_fc_turb_droptank = 0.455 / ((np.log10(R_cutoff_droptank_cd) ** 2.58) * (1 + 0.144 * M_dash**2) ** 0.65)
C_fc_turb_aim_9x = 0.455 / ((np.log10(R_cutoff_aim_9x_cd) ** 2.58) * (1 + 0.144 * M_dash**2) ** 0.65)
C_fc_turb_aim_120 = 0.455 / ((np.log10(R_cutoff_aim_120_cd) ** 2.58) * (1 + 0.144 * M_dash**2) ** 0.65)
C_fc_turb_mk_83 = 0.455 / ((np.log10(R_cutoff_mk_83_cd) ** 2.58) * (1 + 0.144 * M_dash**2) ** 0.65)
#print("Turbulent Skin Friction Coefficients at Supersonic Conditions:")
#print("Fuselage: ", C_fc_turb_fuselage_d)
#print("Wing: ", C_fc_turb_wing_d)
#print("Horizontal Tail: ", C_fc_turb_HT_d)
#print("Vertical Tail: ", C_fc_turb_VT_d)
#print("Drop Tank: ", C_fc_turb_droptank)

# Friction Drag Form Factor (FF) for Components
#Fuselage (FF)
f_fuselage = l_fuselage_c / d_fuselage # Fineness Ratio for Fuselage
FF_fuselage = (0.9 + (5 / (f_fuselage ** 1.5)) + (f_fuselage / 400)) # Form Factor for Fuselage (Raymer 12.31)
#print("Form Factor for Fuselage: ", FF_fuselage)

# Wing (FF)
tc_wing = 0.0599 # Thickness-to-Chord Ratio for Wing
FF_wing_cruise = (1 + (0.6/(0.25)*tc_wing) + 100*(tc_wing) ** 4) * ((1.34 * M_cruise**0.18) * (np.cos(np.radians(35))**0.28)) #(Raymer 12.30) (Cruise Conditions)
FF_wing_dash = (1 + (0.6/(0.25)*tc_wing) + 100*(tc_wing) ** 4) * ((1.34 * M_dash**0.18) * (np.cos(np.radians(35))**0.28)) #(Raymer 12.30) (Supersonic Conditions)
#print("Form Factor (FF) for Wing during Cruise: ", FF_wing_cruise)
#print("Form Factor (FF) for Wing during Supersonic Dash: ", FF_wing_dash)

# Horizontal Tail (FF_HT)
tc_HT = 0.05002 # Thickness-to-Chord Ratio for Horizontal Tail
FF_HT_cruise = (1 + (0.6/(0.15)*tc_HT) + 100*(tc_HT) ** 4) * ((1.34 * M_cruise**0.18) * (np.cos(np.radians(40))**0.28)) #(Raymer 12.30) (Cruise Conditions)
FF_HT_dash = (1 + (0.6/(0.15)*tc_HT) + 100*(tc_HT) ** 4) * ((1.34 * M_dash**0.18) * (np.cos(np.radians(40))**0.28)) #(Raymer 12.30) (Supersonic Conditions)
#print("Form Factor (FF) for Horizontal Tail during Cruise: ", FF_HT_cruise)
#print("Form Factor (FF) for Horizontal Tail during Supersonic Dash: ", FF_HT_dash)

# Vertical Tail (FF_VT)
tc_VT = 0.04003 # Thickness-to-Chord Ratio for Vertical Tail
FF_VT_cruise = (1 + (0.6/(0.15)*tc_VT) + 100*(tc_VT) ** 4) * ((1.34 * M_cruise**0.18) * (np.cos(np.radians(40))**0.28)) #(Raymer 12.30) (Cruise Conditions)
FF_VT_dash = (1 + (0.6/(0.15)*tc_VT) + 100*(tc_VT) ** 4) * ((1.34 * M_dash**0.18) * (np.cos(np.radians(40))**0.28)) #(Raymer 12.30) (Supersonic Conditions)
#print("Form Factor (FF) for Vertical Tail during Cruise: ", FF_VT_cruise)
#print("Form Factor (FF) for Vertical Tail during Supersonic Dash: ", FF_VT_dash)

# External Armament Pylon:
f_pylon = l_pylon / d_pylon # Fineness Ratio for Armament Pylon
FF_pylon = 1 + (0.35 / f_pylon) # Form Factor for Armament Pylon (Raymer 12.32)
FF_pylon_supersonic = 1 # Form Factor for Armament Pylon at Supersonic
#print("Form Factor for Smooth Armament Pylon: ", FF_pylon)

# Air Inlet (FF)
# Using a Diverterless Supersonic Inlet (Air Force Research Laboratory, AFRL) (as seen with F-35)
# reducing the need for a complex inlet design, mechanical maintainence, and associated pressure drag.

# AIM-9X Sidewinder Missile (FF)
f_aim_9x = l_aim_9x / d_aim_9x # Fineness Ratio for AIM-9X Sidewinder Missile
FF_aim_9x = 1 + (0.35 / f_aim_9x) # Form Factor for AIM-9X Sidewinder Missile (Raymer 12.32)
FF_aim_9x_supersonic = 1 # Form Factor for AIM-9X Sidewinder Missile at Supersonic

# AIM-120C AMRAAM Missile (FF)
f_aim_120 = l_aim_120 / d_aim_120 # Fineness Ratio for AIM-120C AMRAAM Missile
FF_aim_120 = 1 + (0.35 / f_aim_120) # Form Factor for AIM-120C AMRAAM Missile (Raymer 12.32)
FF_aim_120_supersonic = 1 # Form Factor for AIM-120C AMRAAM Missile at Supersonic

# MK-83 General Purpose Bomb (FF)
f_mk_83 = l_mk_83 / d_mk_83 # Fineness Ratio for MK-83 General Purpose Bomb
FF_mk_83 = 1 + (0.35 / f_mk_83) # Form Factor for MK-83 General Purpose Bomb (Raymer 12.32)
FF_mk_83_supersonic = 1 # Form Factor for MK-83 General Purpose Bomb at Supersonic


# Component Drag Coefficients for Cruise Conditions
Q_Fuselage = 1.0 # Interference Factor for Fuselage
Q_wing = 1.05 # Interference Factor for Well-filleted Wing (Raymer Table 12.6))
Q_HT = 1.05 # Interference Factor for Horizontal Tail (Raymer Table 12.6)
Q_VT = 1.03 # Interference Factor for Clean V-Tail
Q_droptank = 1.5
Q_Nacelle = 1.3 # Interference Factor for Armament Nacelles
Q_aim_9x = 1.25 # Interference Factor for AIM-9X Sidewinder Missile
Q_aim_120 = 1.5 # Interference Factor for AIM-120C AMRAAM Missile
Q_mk_83 = 1.5 # Interference Factor for MK-83 General Purpose Bomb

CD_fuselage_lam = (C_fc_lam_fuselage * FF_fuselage * Q_Fuselage * S_wet_fuselage)
CD_wing_lam = (C_fc_lam_wing * FF_wing_cruise * Q_wing * S_wet_wing)
CD_HT_lam = (C_fc_lam_HT * FF_HT_cruise * Q_HT * S_wet_HT)
CD_VT_lam = (C_fc_lam_VT * FF_VT_cruise * Q_VT * S_wet_VT)
CD_droptank_lam = (C_fc_lam_droptank * FF_wing_cruise * Q_droptank * S_wet_droptank)
CD_aim_9x_lam = (C_fc_lam_aim_9x * FF_aim_9x * Q_aim_9x * S_wet_aim_9x)
CD_aim_120_lam = (C_fc_lam_aim_120 * FF_aim_120 * Q_aim_120 * S_wet_aim_120)
CD_mk_83_lam = (C_fc_lam_mk_83 * FF_mk_83 * Q_mk_83 * S_wet_mk_83)
#print("Component Drag Coefficients during Cruise Conditions with Laminar Flow:")
#print("Fuselage: ", CD_fuselage_lam)
#print("Wing: ", CD_wing_lam)
#print("Horizontal Tail: ", CD_HT_lam)
#print("Vertical Tail: ", CD_VT_lam)
#print("Drop Tank: ", CD_droptank_lam)

CD_fuselage_turb_c = (C_fc_turb_fuselage_c * FF_fuselage * Q_Fuselage * S_wet_fuselage)
CD_wing_turb_c = (C_fc_turb_wing_c * FF_wing_cruise * Q_wing * S_wet_wing)
CD_HT_turb_c = (C_fc_turb_HT_c * FF_HT_cruise * Q_HT * S_wet_HT)
CD_VT_turb_c = (C_fc_turb_VT_c * FF_VT_cruise * Q_VT * S_wet_VT)
CD_droptank_turb_c = (C_fc_turb_droptank * FF_wing_cruise * Q_droptank * S_wet_droptank)
CD_aim_9x_turb_c = (C_fc_turb_aim_9x * FF_aim_9x * Q_aim_9x * S_wet_aim_9x)
CD_aim_120_turb_c = (C_fc_turb_aim_120 * FF_aim_120 * Q_aim_120 * S_wet_aim_120)
CD_mk_83_turb_c = (C_fc_turb_mk_83 * FF_mk_83 * Q_mk_83 * S_wet_mk_83)
#print("Component Drag Coefficients during Cruise Conditions with Turbulent Flow:")
#print("Fuselage: ", CD_fuselage_turb_c)
#print("Wing: ", CD_wing_turb_c)
#print("Horizontal Tail: ", CD_HT_turb_c)
#print("Vertical Tail: ", CD_VT_turb_c)
#print("Drop Tank: ", CD_droptank_turb_c)

#Supersonic, set Q = 1
CD_fuselage_turb_d = (C_fc_turb_fuselage_d * FF_fuselage * Q_Fuselage * S_wet_fuselage)
CD_wing_turb_d = (C_fc_turb_wing_d * FF_wing_dash * Q_Fuselage * S_wet_wing)
CD_HT_turb_d = (C_fc_turb_HT_d * FF_HT_dash * Q_Fuselage * S_wet_HT)
CD_VT_turb_d = (C_fc_turb_VT_d * FF_VT_dash * Q_Fuselage * S_wet_VT)
CD_droptank_turb_d = (C_fc_turb_droptank * FF_wing_dash * Q_Fuselage * S_wet_droptank)
CD_aim_9x_turb_d = (C_fc_turb_aim_9x * FF_aim_9x_supersonic * Q_Fuselage * S_wet_aim_9x)
CD_aim_120_turb_d = (C_fc_turb_aim_120 * FF_aim_120_supersonic * Q_Fuselage * S_wet_aim_120)
CD_mk_83_turb_d = (C_fc_turb_mk_83 * FF_mk_83_supersonic * Q_Fuselage * S_wet_mk_83)
#print("Component Drag Coefficients during Supersonic Dash Conditions with Turbulent Flow:")
#print("Fuselage: ", CD_fuselage_turb_d)
#print("Wing: ", CD_wing_turb_d)
#print("Horizontal Tail: ", CD_HT_turb_d)
#print("Vertical Tail: ", CD_VT_turb_d)
#print("Drop Tank: ", CD_droptank_turb_d)

# Estimating Trim Drag
# Tail Lift Coefficient
CL_w = 0
x_w = 0
CL_t = 0

# Miscellaneous Drag Coefficients
#u = 0 # Upsweep Angle of Fuselage
#A_max = 6.02041
A_speedbrake = 12.5 # ft^2 Speed Brake Area
#D_q_upsweep = 3.83 * (u ** 2.5) * A_max # Upsweep Drag (Raymer 12.33)
#D_q_base_subsonic = (0.139 + 0.419*((M_cruise-0.161**2))) * A_base
#D_q_dash = (0.064 + 0.4042*(M_dash - 3.84) ** 2) * A_base
D_q_speed_brake_subsonic = 0.139 + 0.419*((M_cruise-0.161**2)) * A_speedbrake # Fuselage-mounted Speed Brake Drag Area (Raymer 12.37)
D_q_speed_brake_supersonic = 0.064 + (0.4042*(M_dash - 3.84) ** 2) * A_speedbrake # Fuselage-mounted Speed Brake Drag Area at Supersonic Conditions (Raymer 12.38)
D_q_arresting_hook = 0.5 # Drag from Arresting Hook (Raymer 12.34)
D_q_landing_gear = 0.25 # Drag from Landing Gear (Raymer Table 12.7)
#CD_speedbrake = (1/S_ref) *  (D_q_speed_brake_subsonic)
#CD_speedbrake = 0.5
CD_arresting_hook = (1/S_ref) * D_q_arresting_hook
CD_arresting_hook = 0.025
CD_gear_ = (1/S_ref) * (3*D_q_landing_gear)
CD_gear = 0.025
#print("Speed Brake Drag Coefficient at Subsonic Conditions: ", CD_speedbrake)
#print("Arresting Hook Drag Coefficient: ", CD_arresting_hook)
#print("Landing Gear Drag Coefficient: ", CD_gear_)
#print("Landing Gear Drag Coefficient: ", CD_gear)

# Traditionally, F/A-18 has 3 Flap Settings (AUTO, HALF, FULL) for the following conditions (Cruise, Takeoff, Landing) respectively.
# The following is the deflection angles associated with each flap configuration:
# AUTO = 0 - 17 degrees | HALF = ~ 30 degrees | FULL = ~ 45 degrees
# Estimating Flap Drag (Slotted Flaps)
F_flap = 0.0074 # Flap Form Factor (Slotted Flaps)
c_flap = 0.25 * l_wing_cbar # Flap Chord Length
CD_flap_auto = F_flap * (c_flap / l_wing_cbar) * (S_flap / S_ref) * (0 - 10) # Flap Drag Coefficient (Raymer 12.61)
CD_flap_half = F_flap * (c_flap / l_wing_cbar) * (S_flap / S_ref) * (30 - 10) # Flap Drag Coefficient (Raymer 12.61)
CD_flap_full = F_flap * (c_flap / l_wing_cbar) * (S_flap / S_ref) * (45 - 10) # Flap Drag Coefficient (Raymer 12.61)
#print("Auto Flap Drag Coefficient: ", CD_flap_auto)
print("Half Flap Drag Coefficient: ", CD_flap_half)
print("Full Flap Drag Coefficient: ", CD_flap_full)

# Slat Deployment (Great Book of Modern Warplanes Spick, Mike, ed.)
F_slat = 0.0074
c_slat = 0.15 * l_wing_cbar
CD_slat_auto = F_slat * (c_slat / l_wing_cbar) * (S_slats / S_ref) * (0 - 10) # Slat Drag Coefficient 
CD_slat_half = F_slat * (c_slat / l_wing_cbar) * (S_slats / S_ref) * (15 - 10) # Slat Drag Coefficient 
CD_slat_full = F_slat * (c_slat / l_wing_cbar) * (S_slats / S_ref) * (15 - 10) # Slat Drag Coefficient 
#print("Auto Slat Drag Coefficient: ", CD_slat_auto)
#print("Half Slat Drag Coefficient: ", CD_slat_half)
#print("Full Slat Drag Coefficient: ", CD_slat_full)

# Estimated Total Aircraft Drag Polar (OpenVSP)
#CD0 = 0.01290 # Estimated Zero-Lift Drag Coefficient (CD0) for Cruise Conditions
CD_LP = 0.075 # Estimated Leakage & Protuberance Drag (Raymer Table 12.9)
CD_wave = 0.0533 # Estimated Wave Drag at Supersonic Dash Conditions (Mach 1.6) (OpenVSP Wave Drag)
CD0_lam = (1/S_ref) * (CD_fuselage_lam + CD_wing_lam + CD_HT_lam + CD_VT_lam + CD_droptank_lam) + (CD_LP)  # Total Zero-Lift Drag Coefficient (CD0) for Cruise Conditions
CD0_turb_c = ((1/S_ref) * (CD_fuselage_turb_c + CD_wing_turb_c + CD_HT_turb_c + CD_VT_turb_c + CD_droptank_turb_c) + (CD_LP) ) / 6.9 # Total Zero-Lift Drag Coefficient (CD0) for Cruise Conditions (Turbulent Flow)
CD0_turb_d = ((1/S_ref) * (CD_fuselage_turb_d + CD_wing_turb_d + CD_HT_turb_d + CD_VT_turb_d + CD_droptank_turb_d) + (CD_LP) ) # Total Zero-Lift Drag Coefficient (CD0) for Supersonic Dash Conditions (Turbulent Flow)
#print("Estimated Zero-Lift Drag Coefficient (CD0) for Cruise Conditions with Laminar Flow: ", CD0_lam)
print("Estimated Zero-Lift Drag Coefficient (CD0) for Cruise Conditions with Turbulent Flow: ", CD0_turb_c)
#print("Estimated Zero-Lift Drag Coefficient (CD0) for Supersonic Dash Conditions with Turbulent Flow: ", CD0_turb_d)

# Supersonic Lift-Curve Slope Estimation 
#B = np.sqrt(M_dash**2 - 1) #(Raymer 12.13)
#CL_alpha_supersonic = 4 / B #(Raymer 12.12)

# Total CD of Aircraft for all 5 Configurations
'''CL_clean = np.linspace(-1, 2.5, num=100)
CL_TO = np.linspace(-1.5, 2.5, num=100)
CL_Landing = np.linspace(-3, 3, num=100)'''

#CL_min_drag = W_kg / (q_cruise * S_ref_m2) # Lift Coefficient at Minimum Drag Condition (Approximately at Cruise) (NEED CITATION!!!!!!!)
#CL_min_drag = 0.25
#print("Lift Coefficient at Minimum Drag Condition: ", CL_min_drag)

#CD0_clean = CD0_turb_c 
#CD0_TO = CD0_turb_c + CD_flap_half 
#CD0_Landing = CD0_turb_c + CD_flap_full + CD_gear + CD_speedbrake + CD_arresting_hook

### RYUYA CODE RYUYA CODE ALERT ###
avl_data = pd.read_csv('EAE130_aircraft_design/Prelim_Drag_Polar_Data.csv')

CL_clean = avl_data['Cruise_CL'].values
CL_TO = avl_data['Takeoff_CL'].values
CL_Landing = avl_data['Landing_CL'].values

CDi_clean = avl_data['Cruise_CDi'].values
CDi_TO = avl_data['Takeoff_CDi'].values
CDi_Landing = avl_data['Landing_CDi'].values

# NACA 64A005 (Symmetrical Airfoil for Wing, Horizontal Tail, Vertical Tail)
#+ CD_flap_auto + CD_slat_auto + 

# Fudge factor to have only viscous effects flaps
Flap_FF = 0.6

CD_clean = (CD0_turb_c  + CDi_clean)  #+ (CD_trim)                    # Clean, Cruise
CD_TO_GD = (CD0_turb_c  + Flap_FF * CD_flap_half + Flap_FF * CD_slat_half + CD_gear + CDi_TO )   # + (CD_trim)         # Takeoff Flaps, Gear Down
CD_TO_GU = (CD0_turb_c + Flap_FF * CD_flap_half + Flap_FF * CD_slat_half + CDi_TO )          # + (CD_trim)                # Takeoff Flaps, Gear Up
CD_L_GD = (CD0_turb_c + Flap_FF * CD_flap_full + Flap_FF * CD_slat_full + CD_gear + CD_arresting_hook + CDi_Landing )      # Landing Flaps, Gear Down
CD_L_GU = (CD0_turb_c + Flap_FF * CD_flap_full + Flap_FF * CD_slat_full + CD_arresting_hook + CDi_Landing )     # Landing Flaps, Gear Up


# Non-induced Drag Coefficients for each configuration
CD_clean_ = (CD0_turb_c) - (CD_flap_auto + CD_slat_auto) 
CD_TO_GD_ = (CD0_turb_c  + CD_flap_half + CD_slat_half + CD_gear)
CD_TO_GU_ = (CD0_turb_c + CD_flap_half + CD_slat_half)
CD_L_GD_ = (CD0_turb_c + CD_flap_full + CD_slat_full + CD_gear + CD_arresting_hook)   #+ CD_speedbrake 
CD_L_GU_ = (CD0_turb_c + CD_flap_full + CD_slat_full + CD_arresting_hook) #+  CD_speedbrake 
print("CD0 for Clean Configuration: ", CD_clean_)
print("CD0 for Takeoff, Gear Down ", CD_TO_GD_)
print("CD0 for Takeoff, Gear Up ", CD_TO_GU_)
print("CD0 for Landing, Gear Down ", CD_L_GD_)
print("CD0 for Landing, Gear Up ", CD_L_GU_)

CL_min = -0.8

#XFOIL Estimates for CL
CL_max_cruise = 0.535 
CL_max_takeoff = 1.67
CL_max_landing = 1.86

mask_cruise = (CL_clean >= CL_min) & (CL_clean <= CL_max_cruise)
mask_takeoff = (CL_TO >= CL_min) & (CL_TO <= CL_max_takeoff)
mask_landing = (CL_Landing >= CL_min) & (CL_Landing <= CL_max_landing)

plt.figure(figsize=(8, 6))  
plt.plot(CD_clean[mask_cruise], CL_clean[mask_cruise], label='Clean, Cruise')
plt.plot(CD_TO_GU[mask_takeoff], CL_TO[mask_takeoff], label='Takeoff Flaps + Gear Up')
plt.plot(CD_TO_GD[mask_takeoff], CL_TO[mask_takeoff], label='Takeoff Flaps + Gear Down')
plt.plot(CD_L_GU[mask_landing], CL_Landing[mask_landing], label='Landing Flaps + Gear Up')
plt.plot(CD_L_GD[mask_landing], CL_Landing[mask_landing], label='Landing Flaps + Gear Down')
#plt.xlim(0,1)
#plt.xticks(np.arange(0, 1.1, 0.25))
#plt.yticks(np.arange(-2, 2.1, 0.5))
#plt.ylim(-2,2)
plt.xlabel("$C_D$")
plt.ylabel("$C_L$")
plt.axhline(y=0, color='black', linewidth=0.5)  
plt.title("Drag Polar for F/A-24 Hyper-Hornet")
plt.legend(loc = 'lower right')
plt.grid(True)
plt.savefig(r"C:\Users\14153\Desktop\Skewl\EAE 130\Python\EAE130_aircraft_design\Drag\EAE130_aircraft_design\refined_drag_polar2.pdf")
plt.show() 