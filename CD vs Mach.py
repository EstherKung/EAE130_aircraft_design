import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ambiance import Atmosphere
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Times New Roman"

# Convert altitude
h_cruise_ft = 35000
h_cruise_m = h_cruise_ft * 0.3048

# Initialize atmosphere
atm = Atmosphere(h_cruise_m)

# Extract properties (SI units)
rho = atm.density[0]
mu = atm.dynamic_viscosity[0]
T = atm.temperature[0]
P = atm.pressure[0]
a = atm.speed_of_sound[0]
#print("Atmospheric properties at Cruise Altitude:")
#print("Density: ", rho)
#print("Dynamic Viscosity: ", mu)
#print("Temperature: ", T)
#print("Pressure: ", P)
#print("Speed of Sound at Cruise: ", a)

# Cruise @ 35,000 ft
M_cruise = 0.85
V_cruise = M_cruise * a
q_cruise = 0.5 * rho * V_cruise**2
#print("Cruise Pressure: ", P)
#print("Cruise Velocity: ", V_cruise)
#print("Dynamic pressure at cruise: ", q_cruise)

# Dash(M = 1.6 at 35,000 ft)
M_dash = 1.6
V_dash = M_dash * a
q_dash = 0.5 * rho * V_dash**2

# Mach Range (0 - 1.6)
M_range = np.linspace(0.1, 1.6, num=100)

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

# Transonic or Supersonic (cd = cruise/dash) 
R_cutoff_fuselage_cd = 44.62 * ((l_fuselage_c / k) ** 1.053) * (M_range ** 1.16)
R_cutoff_wing_cd = 44.62 * ((l_wing_cbar / k) ** 1.053) * (M_range ** 1.16)
R_cutoff_HT_cd = 44.62 * ((l_HT_cbar / k) ** 1.053) * (M_range ** 1.16)
R_cutoff_VT_cd = 44.62 * ((l_VT_cbar / k) ** 1.053) * (M_range ** 1.16)
R_cutoff_droptank_cd = 44.62 * ((l_wing_cbar / 2 / k) ** 1.053) * (M_range ** 1.16)
R_cutoff_aim_9x_cd = 44.62 * ((l_aim_9x / k) ** 1.053) * (M_range ** 1.16)
R_cutoff_aim_120_cd = 44.62 * ((l_aim_120 / k) ** 1.053) * (M_range ** 1.16)
R_cutoff_mk_83_cd = 44.62 * ((l_mk_83 / k) ** 1.053) * (M_range ** 1.16)

# Turbulent Skin Friction Coefficient for Transonic/Supersonic Conditions
C_fc_turb_fuselage_d = 0.455 / ((np.log10(R_cutoff_fuselage_cd) ** 2.58) * (1 + 0.144 * M_range**2) ** 0.65)
C_fc_turb_wing_d = 0.455 / ((np.log10(R_cutoff_wing_cd) ** 2.58) * (1 + 0.144 * M_range**2) ** 0.65)
C_fc_turb_HT_d = 0.455 / ((np.log10(R_cutoff_HT_cd) ** 2.58) * (1 + 0.144 * M_range**2) ** 0.65)
C_fc_turb_VT_d = 0.455 / ((np.log10(R_cutoff_VT_cd) ** 2.58) * (1 + 0.144 * M_range**2) ** 0.65)
C_fc_turb_droptank = 0.455 / ((np.log10(R_cutoff_droptank_cd) ** 2.58) * (1 + 0.144 * M_range**2) ** 0.65)
C_fc_turb_aim_9x = 0.455 / ((np.log10(R_cutoff_aim_9x_cd) ** 2.58) * (1 + 0.144 * M_range**2) ** 0.65)
C_fc_turb_aim_120 = 0.455 / ((np.log10(R_cutoff_aim_120_cd) ** 2.58) * (1 + 0.144 * M_range**2) ** 0.65)
C_fc_turb_mk_83 = 0.455 / ((np.log10(R_cutoff_mk_83_cd) ** 2.58) * (1 + 0.144 * M_range**2) ** 0.65)

# Friction Drag Form Factor (FF) for Components
#Fuselage (FF)
f_fuselage = l_fuselage_c / d_fuselage # Fineness Ratio for Fuselage
FF_fuselage = (0.9 + (5 / (f_fuselage ** 1.5)) + (f_fuselage / 400)) # Form Factor for Fuselage (Raymer 12.31)
#print("Form Factor for Fuselage: ", FF_fuselage)

# Wing (FF)
tc_wing = 0.0599 # Thickness-to-Chord Ratio for Wing
FF_wing_cruise = (1 + (0.6/(0.25)*tc_wing) + 100*(tc_wing) ** 4) * ((1.34 * M_cruise**0.18) * (np.cos(np.radians(35))**0.28)) #(Raymer 12.30) (Cruise Conditions)
FF_wing_dash = (1 + (0.6/(0.25)*tc_wing) + 100*(tc_wing) ** 4) * ((1.34 * M_range**0.18) * (np.cos(np.radians(35))**0.28)) #(Raymer 12.30) (Supersonic Conditions)
#print("Form Factor (FF) for Wing during Cruise: ", FF_wing_cruise)
#print("Form Factor (FF) for Wing during Supersonic Dash: ", FF_wing_dash)

# Horizontal Tail (FF_HT)
tc_HT = 0.05002 # Thickness-to-Chord Ratio for Horizontal Tail
FF_HT_cruise = (1 + (0.6/(0.25)*tc_HT) + 100*(tc_HT) ** 4) * ((1.34 * M_cruise**0.18) * (np.cos(np.radians(40))**0.28)) #(Raymer 12.30) (Cruise Conditions)
FF_HT_dash = (1 + (0.6/(0.25)*tc_HT) + 100*(tc_HT) ** 4) * ((1.34 * M_range**0.18) * (np.cos(np.radians(40))**0.28)) #(Raymer 12.30) (Supersonic Conditions)
#print("Form Factor (FF) for Horizontal Tail during Cruise: ", FF_HT_cruise)
#print("Form Factor (FF) for Horizontal Tail during Supersonic Dash: ", FF_HT_dash)

# Vertical Tail (FF_VT)
tc_VT = 0.04003 # Thickness-to-Chord Ratio for Vertical Tail
FF_VT_cruise = (1 + (0.6/(0.25)*tc_VT) + 100*(tc_VT) ** 4) * ((1.34 * M_cruise**0.18) * (np.cos(np.radians(40))**0.28)) #(Raymer 12.30) (Cruise Conditions)
FF_VT_dash = (1 + (0.6/(0.25)*tc_VT) + 100*(tc_VT) ** 4) * ((1.34 * M_range**0.18) * (np.cos(np.radians(40))**0.28)) #(Raymer 12.30) (Supersonic Conditions)
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

# Component Drag Coefficient for Supersonic Conditions (Set Q = 1)
CD_fuselage_turb_d = (C_fc_turb_fuselage_d * FF_fuselage * Q_Fuselage * S_wet_fuselage)
CD_wing_turb_d = (C_fc_turb_wing_d * FF_wing_dash * Q_Fuselage * S_wet_wing)
CD_HT_turb_d = (C_fc_turb_HT_d * FF_HT_dash * Q_Fuselage * S_wet_HT)
CD_VT_turb_d = (C_fc_turb_VT_d * FF_VT_dash * Q_Fuselage * S_wet_VT)
CD_droptank_turb_d = (C_fc_turb_droptank * FF_wing_dash * Q_Fuselage * S_wet_droptank)
CD_aim_9x_turb_d = (C_fc_turb_aim_9x * FF_aim_9x_supersonic * Q_Fuselage * S_wet_aim_9x)
CD_aim_120_turb_d = (C_fc_turb_aim_120 * FF_aim_120_supersonic * Q_Fuselage * S_wet_aim_120)
CD_mk_83_turb_d = (C_fc_turb_mk_83 * FF_mk_83_supersonic * Q_Fuselage * S_wet_mk_83)

# Wave Drag (Metabook Section 7.4)
k_dd = 0.95
CL_cruise = 0.535
M_DD_wing = (k_dd / np.cos(np.radians(lambda_))) - (0.05 / (np.cos(np.radians(lambda_))**2)) - (CL_cruise / (10*(np.cos(np.radians(lambda_))**3)))
M_DD_HT = (k_dd / np.cos(np.radians(lambda_))) - (0.045 / (np.cos(np.radians(lambda_))**2)) - (CL_cruise / (10*(np.cos(np.radians(lambda_))**3)))
M_DD_VT = (k_dd / np.cos(np.radians(lambda_))) - (0.04 / (np.cos(np.radians(lambda_))**2)) - (CL_cruise / (10*(np.cos(np.radians(lambda_))**3)))
#print("Drag Divergent Mach Number for Wing:", M_DD_wing)
#print("Drag Divergent Mach Number for HT:", M_DD_HT)
#print("Drag Divergent Mach Number for VT:", M_DD_VT)

M_crit_wing = M_DD_wing - ((0.1 /80) ** (1/3))
M_crit_HT= M_DD_HT - ((0.1 /80) ** (1/3))
M_crit_VT = M_DD_VT - ((0.1 /80) ** (1/3))

#CD_wave_wing = np.where(M_range > M_crit_wing, 20 * ((M_range - M_crit_wing) ** 4))
CD_wave_wing = np.where(M_range > M_crit_wing, 20*(M_range - M_crit_wing)**4,0)
#CD_wave_HT = 20 * ((M_range - M_crit_HT) ** 4)
#CD_wave_VT = 20 * ((M_range - M_crit_VT) ** 4)

CD_LP = 0.10 # Estimated Leakage & Protuberance Drag (Raymer Table 12.9) 

#CD0_turb_aa = (1/S_ref) * (CD_fuselage_turb_d + CD_wing_turb_d + CD_HT_turb_d + CD_VT_turb_d + CD_droptank_turb_d + 2*CD_aim_9x_turb_d + 6*CD_aim_120_turb_d) + CD_LP 
CD0_turb_aa = 0.01299 
CD0_turb_strike = (1/S_ref) * (CD_fuselage_turb_d + CD_wing_turb_d + CD_HT_turb_d + CD_VT_turb_d + CD_droptank_turb_d + 2*CD_aim_9x_turb_d + 4*CD_mk_83_turb_d) + CD_LP

CD_turb_aa = CD0_turb_aa + CD_wave_wing #+ CD_wave_HT + CD_wave_VT
CD_turb_strike = CD0_turb_strike 

#mask_aa = (M_range >= ) & (CL_clean <= CL_max_cruise)
#mask_strike = (CL_TO >= CL_min) & (CL_TO <= CL_max_takeoff)

plt.figure(figsize=(10, 6))  
#plt.plot(CD_turb_aa[mask_cruise], CL_clean[mask_cruise], label='Clean, Cruise')
plt.plot(M_range, CD_turb_aa, label='Air-to-Air Loadout')
plt.xlim(0,2)
plt.xticks(np.arange(0, 2, 0.25))
plt.yticks(np.arange(0, 1, 0.25))
plt.ylim(0,1.1)
plt.xlabel("Mach Number")
plt.ylabel("$C_D$")
plt.axhline(y=0, color='black', linewidth=0.5)  
plt.title("CD vs Mach Number")
plt.legend(loc = 'lower right')
plt.grid(False)
plt.show() 