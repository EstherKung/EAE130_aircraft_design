import openvsp as vsp
import json
import pandas as pd
import numpy as np
import pprint 
from collections import defaultdict
from dataclasses import dataclass
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Initialize config file, contains files and constants
@dataclass
class Config:
    vsp_filename: str
    geom_def_path: str
    fuse_file_path: str
    wing_foils: list       # Root, Mid, Tip; .dat format
    tail_foils: list       # VStab root & tip, HStab tip, HStab root

    # Fixed Weights Parameters
    W_dg: float = 50213.0  # Design Gross Weight !!! MUST CHANGE TO USE 50% FUEL !!!
    N_z: float = 10.5      # Design Ultimate Load Factor (7*1.5)
    tc_rt: float = 0.06    # Wing Airfoil Thickness @ Root
    F_w: float = 7.0       # Fuselage Width @ HStab intersection
    M: float = 1.6         # Design Max Mach Number
    rho_fuel: float = 6.65 # Density of JP-5 Fuel


########################
# VSP INTERFACE
########################

class VSP_Geom:
    # Generate aircraft geometry & run compgeom

    def __init__(self):
        pass






########################
# RUN FILE
########################

if __name__ == "__main__":
    config = Config(vsp_filename='F24HH_2.vsp3',
                    geom_def_path='airplane_geom2.json',
                    fuse_file_path=r"C:\Users\14153\Desktop\OpenVSP-3.48.2-win64\VSPFiles\2_SIMPLE_F24HH_FUSE.vsp3",
                    wing_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A006_TEST.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A004_TEST.dat"],
                    tail_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A005.dat"])
    
    pprint.pprint(config.__dict__)