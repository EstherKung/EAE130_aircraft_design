from Flying_Surfaces import surf_def as sdef
from Initial_Weight_Est import weight
from Surface_to_VSP import surf_to_VSP as svsp
from SM_conv import sm_convergence as smgen
from AVL_scripting import write_avl_file2 as wavl
from utils import atmos
from OptVL_Interface import ovl_analysis as ovl

from pathlib import Path
from pprint import pprint
import sys
import pandas as pd


# Current Directory:
cwd = Path(__file__).resolve().parent

# Global parameters
X_wing = 18.1530 
L_HT_f = 0.3337
c_HT = 0.2986
M_cruise = 0.85
AR_w = 3.5
name = 'aiaa_plane'

fuse_tank = 6788.66

SMconf = smgen.SM_Config(
    fuse_vspfile = r'VSP_Files\4_SIMPLE_F24HH_FUSE.vsp3',
    wing_airfoils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A006_TEST.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A004_TEST.dat"],
    hstab_airfoils = [r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat"],
    vstab_airfoils = [r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat"],
    xcg_fuse= 28.886,
    zcg_fuse= -0.191
    )


### Generate main geom def file ###
aiaa_plane = sdef.define_plane(X_loc_wing=X_wing, L_HT_frac=L_HT_f, c_HT=c_HT, save_dir=cwd, fname=name)

### Get init weights esimate ###
W0_i, W_empty_i, W_fuel_i, W_dg_i, W_fuse_empty_i = weight.weight_convergence(S = {'wing': 465, 'htail': aiaa_plane['hstab']['S_HT'], 'vtail': aiaa_plane['vstab']['S_VT'], 'fuse_wet': 678.915,}, 
                                            AR=AR_w, M_cruise=M_cruise, Swet_Sref=3.911, 
                                            mission='strike')

print(f'Init. Weight Est: W0 = {W0_i:.2f} lbs | Empty Weight = {W_empty_i:.2f} lbs | Design Gross Weight = {W_dg_i:.2f} lbs | Fuselage Empty = {W_fuse_empty_i:.2f} lbs')

### Create OpenVSP Model ###
vspconfig = svsp.Config(
        vsp_filename='AIAA_wing_only',
        geom_def_path=aiaa_plane,
        fuse_file_path=SMconf.fuse_vspfile,
        wing_foils=SMconf.wing_airfoils,
        tail_foils=[SMconf.hstab_airfoils[1], SMconf.hstab_airfoils[0]],

        W_dg=W_dg_i
    )

vsp_file = svsp.VSP_Interface(config=vspconfig, global_x_transl=X_wing, save_dir=cwd)
vsp_file.BuildPlane(include_fuse=False, high_fidel=False)
vsp_file.Run_CompGeom()
fsurf_mass = svsp.Weigh_Plane(manager=vsp_file)
densities, comp_mass = fsurf_mass.Mass()
vsp_file.Assign_Mass(densities=densities)

pprint(comp_mass)

# Get cg and mass of flying surfaces
fs_xcg, fs_ycg, fs_zcg, fs_mass_slug = vsp_file.Run_MassProp(n_slice=150)
fs_weight_lbf = fs_mass_slug * 32.174 

# Wing fuel tank weight
W_wing_fuel = comp_mass.at['Wing Fuel Tanks', 'Weight [lbf]']

# Get weight of just wings and tail
fs_empty_lbf = fs_weight_lbf - comp_mass.at['Wing Fuel Tanks', 'Weight [lbf]']

# Calculate drop tank weight (fuse tank = 6788.66 lbf)
dtank_weight = W_fuel_i - fuse_tank - comp_mass.at['Wing Fuel Tanks', 'Weight [lbf]']

# Calculate loaded fuselage weight and CG (4380 + 2500 = strike payload)
W_fuse_load = W_fuse_empty_i + fuse_tank + 4380 + 2500 + dtank_weight

# Get cg of combined plane
ac_xcg = (fs_weight_lbf*fs_xcg + W_fuse_load*SMconf.xcg_fuse) / (fs_weight_lbf + W_fuse_load)
ac_zcg = (fs_weight_lbf*fs_zcg + W_fuse_load*SMconf.zcg_fuse) / (fs_weight_lbf + W_fuse_load)
#print(ac_xcg, ac_zcg)

# Get component MTOW
W_comp_tot = W_fuse_load + fs_weight_lbf

# Create weights dictionary & df
weights_sum = {
    'Initial MTOW': W0_i,
    'Initial Empty': W_empty_i,
    'Initial Fuel': W_fuel_i,
    'Initial Empty Fuse': W_fuse_empty_i,
    '------------------': '--------------',
    'Fuselage Fuel Tank': fuse_tank,
    'Strike Payload': 4380 + 2500,
    '------------------ ': '--------------',
    'Wings & Tail': fs_empty_lbf,
    'Wing Fuel Tank': W_wing_fuel,
    'Drop Tank': dtank_weight,
    'New Component MTOW': W_comp_tot
}

df_weights = pd.DataFrame.from_dict(weights_sum, orient='index', columns=['Weight [lbf]'])
df_weights['Weight [lbf]'] = df_weights['Weight [lbf]'].apply(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)


### Create full plane openvsp model ###
vspconfig = svsp.Config(
        vsp_filename='AIAA_F24HH_FINAL',
        geom_def_path=aiaa_plane,
        fuse_file_path=SMconf.fuse_vspfile,
        wing_foils=SMconf.wing_airfoils,
        tail_foils=[SMconf.hstab_airfoils[1], SMconf.hstab_airfoils[0]],

        W_dg=W_dg_i
    )

vsp_file = svsp.VSP_Interface(config=vspconfig, global_x_transl=X_wing, save_dir=cwd)
vsp_file.BuildPlane(include_fuse=True, high_fidel=False)
vsp_file.Assign_Mass(densities=densities)


### AVL TIME ###
# Calculate various CLs first (sea level and 35k ft)
rho_sl, a_sl = atmos.atmos(0)
V_sl = 0.21 * a_sl
CL_sea_level = (2 * W_comp_tot) / (rho_sl * V_sl**2 * 465)

rho_35k, a_35k = atmos.atmos(35000)
V_35k = 0.85 * a_35k
CL_35k = (2 * W_comp_tot) / (rho_35k * V_35k**2 * 465)

# Write AVL File
avlconfig = wavl.AVL_Config(
plane_name='F24HH_AIAA_FINAL', # Iterate this name so ovl can find it
geom_def=aiaa_plane,
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

# Run AVL Analyses
ovlplane = ovl.ovl_analysis('AIAA_FINAL\F24HH_AIAA_FINAL.avl')
ovlplane.SM(Mach=0.21, cref=aiaa_plane['wing']['c_bar'], xcg=ac_xcg, CL=CL_sea_level)
ovlplane._stab_crs(Mach=0.85, cref=aiaa_plane['wing']['c_bar'], xcg=ac_xcg, CL=CL_35k)


### print weights summary ###
print(df_weights)
print(f'(X, Y, Z) CG = ({ac_xcg:.2f}, 0.0, {ac_zcg:.2f})')


