'''
Adjust X_wing, L_HT to find geometry that satisfies design SM (SM=-5%+/-1%)
    With the Objective:
        - Lowest W0
    Against the constraints
        - Reasonable stab. deflection in flight phases: stabilator deflection < 8 deg
        - Aircraft length (x_end_hstab) < 50 ft
'''

from Flying_Surfaces import surf_def as sdef
from AVL_scripting import write_avl_file2 as wavl
from Surface_to_VSP import surf_to_VSP as svsp
from Initial_Weight_Est import weight
from OptVL_Interface import ovl_analysis as ovl
from utils import atmos

from pprint import pprint
from pathlib import Path
from dataclasses import dataclass
import json
import sys
import time

# Global variables (to be adjusted for SM convergence)
X_wing = 18.0
L_HT_f = 0.29

# Global 'preset' variables
AR_w = 3.5
M_cruise = 0.85

# Top level config
@dataclass
class SM_Config:
    fuse_vspfile: str  # vsp3 file for the fuselage imported for surf_to_VSP
    wing_airfoils: list    # List of airfoil dat files for the wing (root, mid, tip)
    hstab_airfoils: list   # List of airfoils for hstab (root, tip)
    vstab_airfoils: str    # Airfoil dat file for vstab
    xcg_fuse: float        # x CG location of fuselage
    zcg_fuse: float        # z CG location of fusealge

#######################################################################################

### OUTER VARS (FIXED) ###

# Setup Global Config file
SMconf = SM_Config(
    fuse_vspfile = r'VSP_Files\7_SM_AERO_F24HH_FUSE.vsp3',
    wing_airfoils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A006_TEST.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A004_TEST.dat"],
    hstab_airfoils = [r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat"],
    vstab_airfoils = [r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat"],
    xcg_fuse=28.304,
    zcg_fuse= -0.193
    )

# Get current directory
cwd = Path(__file__).resolve().parent

'''start_time = time.perf_counter()'''

def SM_Iteration(X_wing, L_HT_f):
    # Generate initial aircraft json
    planedef = sdef.define_plane(X_loc_wing=X_wing, L_HT_frac=L_HT_f, save_dir=cwd, fname='sm_conv_plane')

    # Get hstab TE X coord (to make sure 50ft is not exceeded)
    x_end_hstab = planedef['hstab']['xLE_pts'][0] + planedef['hstab']['chords'][0] + X_wing # Kill loop if over 50ft


    # Get initial weights estimate (Run only once)
    W0, W_empty, W_fuel, W_dg, W_fuse_empty = weight.weight_convergence(S = {'wing': 465, 'htail': planedef['hstab']['S_HT'], 'vtail': planedef['vstab']['S_VT'], 'fuse_wet': 678.915,}, 
                                            AR=AR_w, M_cruise=M_cruise, Swet_Sref=3.911, 
                                            mission='strike')  # THERE really should be a script to input these weights into the vsp fuselage model to get accurate results...


    ### Interface with OpenVSP to find cg of just flying surfaces ###
    vspconfig = svsp.Config(
        vsp_filename='F24HH_SM',
        geom_def_path=planedef,
        fuse_file_path=r'VSP_Files\7_SM_AERO_F24HH_FUSE.vsp3',
        wing_foils=SMconf.wing_airfoils,
        tail_foils=[SMconf.hstab_airfoils[1], SMconf.hstab_airfoils[0]],

        W_dg=W_dg 
    )

    vsp_file = svsp.VSP_Interface(config=vspconfig, global_x_transl=X_wing, save_dir=cwd)
    vsp_file.BuildPlane(include_fuse=True, high_fidel=False)
    vsp_file.Run_CompGeom()
    fsurf_mass = svsp.Weigh_Plane(manager=vsp_file)
    densities, comp_mass = fsurf_mass.Mass()
    vsp_file.Assign_Mass(densities=densities)

    fs_xcg, fs_ycg, fs_zcg, fs_mass_slug = vsp_file.Run_MassProp(n_slice=50)

    fs_weight_lbf = fs_mass_slug * 32.174 


    # Calculate CG of aircraft
    ac_xcg = (fs_weight_lbf*fs_xcg + W_fuse_empty*SMconf.xcg_fuse) / (fs_weight_lbf + W_fuse_empty)
    ac_zcg = (fs_weight_lbf*fs_zcg + W_fuse_empty*SMconf.zcg_fuse) / (fs_weight_lbf + W_fuse_empty)
    print(ac_xcg, ac_zcg)


    # Calculate sea level CL
    rho_sl, a_sl = atmos.atmos(0)
    V_sl = 0.21 * a_sl
    CL_sea_level = (2 * W0) / (rho_sl * V_sl**2 * 465)
    print(CL_sea_level)

    ### Write AVL file ###
    avlconfig = wavl.AVL_Config(
        plane_name='F24HH_SM', # Iterate this name so ovl can find it
        geom_def=planedef,
        wing_foils=SMconf.wing_airfoils,
        hstab_foils=SMconf.hstab_airfoils,
        vstab_foils=SMconf.vstab_airfoils,
        CG=[ac_xcg, 0, ac_zcg],
        X_wing=X_wing,
        Mach=M_cruise
    )

    avl_hstab = wavl.Hstab(name='Hstab', config=avlconfig)
    avl_vstab = wavl.Vstab(name='Vstab', config=avlconfig)
    avl_wing = wavl.Wing(name='Wing', config=avlconfig)

    avl_file = wavl.Write_AVL_File(config=avlconfig, surfaces=[avl_hstab, avl_vstab, avl_wing])
    avl_file.Write_File(savedir=cwd)


    #### RUN AVL
    ovlplane = ovl.ovl_analysis('SM_conv\F24HH_SM.avl')
    SM, stabl_defl = ovlplane.SM(Mach=0.2, cref=planedef['wing']['c_bar'], xcg = ac_xcg, CL=CL_sea_level)

    print(f'Static Margin: {SM:.4f} | Elevator Deflection: {stabl_defl:.4f} | Length Plane: {x_end_hstab:.4f} | Flying Surface Weight: {fs_weight_lbf:.4f}')
    return SM, stabl_defl, x_end_hstab, fs_weight_lbf

'''end_time = time.perf_counter()
execution_time = end_time - start_time

print(f"Executed in {execution_time:.4f} seconds")'''




'''Static Margin: -0.0408 | Elevator Deflection: 3.3511 | Length Plane: 47.5961 | Flying Surface Weight: 8119.8471'''

if __name__=='__main__':
    SM_Iteration(X_wing=X_wing, L_HT_f=L_HT_f)