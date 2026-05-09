'''
Adjust X_wing, L_HT to find geometry that satisfies design SM under the conditions
    - Lowest W0
    - Reasonable stab. deflection in flight phases
'''

from Flying_Surfaces import surf_def as sdef
from AVL_scripting import write_avl_file as wavl

from pprint import pprint
from pathlib import Path
from dataclasses import dataclass

# Global variables
X_wing = 16.0
L_HT_f = 0.29




# Top level config (this may go inside the sm convergence function, to allow for inputs to be passed to it)
@dataclass
class SM_Config:
    fuse_vspfile = str  # vsp3 file for the fuselage imported for surf_to_VSP
    wing_airfoils = list    # List of airfoil dat files for the wing (root, mid, tip)
    hstab_airfoils = list   # List of airfoils for hstab (root, tip)
    vstab_airfoils = str    # Airfoil dat file for vstab






# Get current directory
cwd = Path(__file__).resolve().parent


# Generate aircraft json
planedef = sdef.define_plane(X_loc_wing=X_wing, L_HT_frac=L_HT_f, save_dir=cwd, fname='sm_conv_plane')







