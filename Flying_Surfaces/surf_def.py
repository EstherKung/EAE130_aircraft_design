"""
Calculate and export the wing and tail dimensions of a simple aircraft defined by parameters. 
"""

import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
import pprint
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.axes import Axes
import matplotlib as mpl

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "mathtext.fontset": "stix",
    "font.size": 12
})


#####################
# AIRCRAFT DEFINITION
#####################

# From TS-Diagram, RFP
S_w = 465               # Wing Area, ft^2
L_fuse = 50             # Fuselage Length, ft

# Wing Definition
wing_parm = {
    "AR": 3.5,          # Wing Aspect Ratio
    "lambda_w": 0.27,   # Wing Taper Ratio
    "LE_swp": 35        # Wing Leading Edge Sweep, degrees
}

wing_geom = {
    "Z_loc": -0.1,       # Vertical Offset, ft
    "Y_rot": 1.5,       # Angle of Incidence, degrees
    "X_Rot": 0,         # Dihedral, degrees
    "Fold_Loc": 14.0,   # Location of wing fold, ft 
    "Tip_X_rot": -2.0   # Washout, degrees
}

wing_flap = {
    "Flap_Y_start":3.8, # Flap Y Start Distance from AC Centerline, ft
    "cf_c_1": 0.25,     # Flap Root Chord Fraction
    "cf_c_2": 0.25      # Flap Tip Chord Fraction
}

wing_ail = {
    "b1_offset": 0.005, # Percent Span Offset, Aileron span start from flap span end
    "b2_ail": 1,        # Percent Span, Aileron Tip
    "ca_c1": 0.2,       # Aileron Root Chord Fraction
    "ca_c2": 0.25       # Aileron Tip Chord Fraction
}

wing_slat = {
    "b1_slat": 0.15,
    "b2_slat": 1.0,
    "cs_c1": .15,
    "cs_c2": .2
}

# AVL parsing; 0 = regular chord element, no control surfaces. 
#              1 = TE control surface
#              2 = LE control surface
#              4 = regular chord tip, LE & TE terminating
#              5 = regular chord, TE sfs terminating
wing_control = [0, 2, 1, 5, 1.5, 4]

# HStab Definition
Hstab_parm = {
    "c_HT": 0.30,       # HStab Tail Volume Coefficient
    "AR_HT": 2.4,       # HStab Aspect Ratio
    "lambda_HT": 0.29,  # HStab Taper Ratio
    "LE_swp_HT": 40,    # HStab Leading Edge Sweep, degrees
    "L_HT_frac": 0.29,  # HStab Tail Arm Ratio: L_HT / L_fuse
}

Hstab_geom = {
    "YLoc_HT": 2.3,     # Horizontal Offset, ft
    "ZLoc_HT": -0.613  # Vertical Offset, ft
}

Hstab_control = [-1, 0, 0] # for AVL parsing; if 0, regular chord element (Root Chord, Tip Chord)
# -1 = root bridging

# Vstab Definition
VStab_parm = {
    "c_VT": 0.08,       # Vstab Tail Volume Coefficient
    "AR_VT": 1.35,      # VStab Aspect Ratio
    "lambda_VT": 0.4,   # VStab Taper Ratio
    "LE_swp_VT": 40,    # Vstab Leading Edge Sweep, degrees
    "L_VT_frac": 0.31   # VStab Tail Arm Ratio: L_VT / L_fuse
}

VStab_geom = {
    "Y_loc_VT": 2.5,       # Horizontal Offset, ft
    "Z_loc_VT": 0.25,      # Vertical Offset, ft
    "X_rot_VT": 70         # Cant Angle, degrees
}

Vstab_rud = {
    "cr_c1": 0.3,       # Chord Fraction of Rudder
    "cr_c2": 0.3,
    "b1_rud": 0.1,      # Start Span Fraction
    "b2_rud": 1.0       # End Span Fraction
}

Vstab_control = [0, 1, 3] # For AVL parsing; if 0, regular chord element; if 1, TE CNTL sfs, 3 if tip chord & TE surface termination


#####################
# PLANFORM
#####################
class planform:
    '''
    Calculates dimension of a typical single-taper planform. Plots for visualization 
    '''
    def __init__(self, name: str, S:float, AR:float, lam:float, LE_swp:float, L_offset:float = 0): # L_offset offsets the entire surface along the x-axis
        '''
        Initializes parameters

        Args:
            name (str): Name of the planform 
            S (float): Planform area [ft^2]
            AR (float): Aspect ratio of planform
            lam (float): Taper ratio of planform
            LE_swp (float): Leading Edge Sweep 
            L_offset (float) (optional): Distance to offset surface along x-axis, measured from origin to root chord LE point
        '''

        self.name = name
        self.S = S
        self.AR = AR
        self.lam = lam
        self.LE_swp = LE_swp
        self.L_offset = L_offset
        self.ss = {}

        #automatically calculate planform upon object instatiation
        self.calc_plan()

    def calc_plan(self):
        '''
        Calculates wingspan, root and tip chord, and MAC chord. Calculates quarter MAC point with reference to origin (wing LE point OR wing LE point plus L_offset), calculates sweep at quarter MAC.
        '''

        # Define core planform
        self.b = np.sqrt(self.S * self.AR)
        self.c_r = (2 * self.S) / (self.b * (1 + self.lam))
        self.c_t = self.lam * self.c_r
        self.c_bar = (2/3) * self.c_r * (1 + self.lam + self.lam**2) / (1+self.lam)
        self.y_bar = (self.b / 6) * ((1 + 2 * self.lam) / (1 + self.lam))

        # Sweep
        self.LE_swp_rad = np.deg2rad(self.LE_swp)
        self.LE_s_bar = np.tan(self.LE_swp_rad)

        # Quarter MAC Point relative to global origin (either wing LE, or Wing LE point + offset)
        self.quart_mac_x = self.y_bar # X & Y are switched here for plotting.
        self.quart_mac_y = -(self.y_bar * self.LE_s_bar + 0.25 * self.c_bar + self.L_offset)

        # 25% MAC Wing Sweep
        self.quart_c_r = self.c_r / 4 + self.L_offset
        self.quart_mac_swp = np.rad2deg(np.arctan((abs(self.quart_mac_y) - self.quart_c_r) / self.y_bar))

        # Planform vertices w.r.t. global origin (y, x), aircraft coords
        self.LE_point = (0, 0 -self.L_offset)
        self.Tip_f_point = (self.b/2, -self.b/2 * self.LE_s_bar - self.L_offset)
        self.Tip_b_point = (self.b/2, -self.b/2 * self.LE_s_bar - self.c_t - self.L_offset)
        self.TE_point = (0, -self.c_r - self.L_offset)

        # Store x & y points for future use (LE root, LE tip, TE tip, TE root)
        self.xpoints = [self.LE_point[1], self.Tip_f_point[1], self.Tip_b_point[1], self.TE_point[1]]
        self.ypoints = [self.LE_point[0], self.Tip_f_point[0], self.Tip_b_point[0], self.TE_point[0]]

    def set_global_loc(self, new_L_offset:float):
        '''
        Modifies the planform LE location (use to move tail surfaces to correct location). Re-calculates planform parameters with reference to offset distance.
        
        Args:
            new_L_offset (float): The new offset distance [ft] to offset the surface.
        '''

        self.L_offset = new_L_offset
        
        # Re-calculate planform based on new offset
        self.calc_plan()

    def plan_plot(self, ax: Axes):
        '''
        Plots the planform to visualize the geometry

        Args:
            ax (Axes): The axes object to plot upon.    
        '''

        # Plot planform
        self.points = [self.LE_point, self.Tip_f_point, self.Tip_b_point, self.TE_point]

        self.mac_line_x = (self.y_bar, self.y_bar)
        self.mac_line_y = (-(self.y_bar * self.LE_s_bar + self.L_offset), -(self.y_bar * self.LE_s_bar + self.c_bar + self.L_offset))

        self.trapezoid = patches.Polygon(self.points, closed=True,  edgecolor='black', fill=True)
        ax.add_patch(self.trapezoid)
        ax.plot(self.mac_line_x, self.mac_line_y, color="red", label=rf'{self.name} MAC: {self.c_bar:.2f} ft')
        ax.scatter(self.quart_mac_x, self.quart_mac_y, color="orange", label=rf'{self.name} $\frac{{1}}{{4}}$MAC: ({-self.quart_mac_y:.2f}, {self.quart_mac_x:.2f})')
        ax.axis('equal')
        ax.legend()
        ax.set_xlabel("Body Y")
        ax.set_ylabel("Body X")
        ax.set_title(f"{self.name} Planform")



#####################
# Main Wing
#####################

class Wing(planform):
    def __init__(self, name, S, AR, lam, LE_swp, L_offset, Z_loc, Y_rot, X_rot, Fold_Loc, Tip_X_rot):
        super().__init__(name, S, AR, lam, LE_swp, L_offset)
        
        self.fold_loc = Fold_Loc
        self.washout = Tip_X_rot
        self.Z_loc = Z_loc
        self.Y_rot = Y_rot
        self.X_rot = X_rot 
    
    def add_flaps(self, Flap_Y_offset, cf_c_1, cf_c_2):
        # parametrically define the flap start and end span/chord
        self.ss['flap'] = {
            'b1_flap': Flap_Y_offset / (self.b/2),
            'b2_flap': self.fold_loc / (self.b/2),
            'c1_flap': cf_c_1,
            'c2_flap': cf_c_2
        }

    def add_ailerons(self, b1_offset, b2_ail, ca_c1, ca_c2):
        self.ss['aileron'] = {
            'b1_ail': self.ss['flap']['b2_flap'] + b1_offset,
            'b2_ail': b2_ail,
            'c1_ail': ca_c1,
            'c2_ail': ca_c2
        }

    def add_slats(self, b1_slat, b2_slat, cs_c1, cs_c2):
        self.ss['slat'] = {
            'b1_slat': b1_slat,
            'b2_slat': b2_slat,
            'c1_slat': cs_c1,
            'c2_slat': cs_c2
        }

    def calc_coords(self):
        # Calculate LE coordinates for AVL
        span_fracs = np.unique([
            0.0,
            self.ss['slat']['b1_slat'],
            self.ss['flap']['b1_flap'],
            self.ss['flap']['b2_flap'],
            self.fold_loc / (self.b / 2),
            self.ss['aileron']['b1_ail'],
            self.ss['aileron']['b2_ail'],
            self.ss['slat']['b2_slat'],
            1.0
        ])

        yLE = (self.b / 2) * span_fracs
        xLE = yLE * np.tan(self.LE_swp_rad) + self.L_offset
        chords = self.c_r - ((self.c_r - self.c_t) * span_fracs)

        self.xLE = xLE.tolist()
        self.yLE = yLE.tolist()
        self.zLE = self.Z_loc
        self.chords = chords.tolist()
        

        pprint.pprint(yLE)

# Testing, enable if testing wing
'''# Call the Wing class to define the main wing
wing = Wing('Wing', S=S_w, AR=wing_parm["AR"], lam=wing_parm["lambda_w"], LE_swp=wing_parm["LE_swp"], L_offset=0,
            Z_loc=wing_geom["Z_loc"], Y_rot=wing_geom["Y_rot"], X_rot=wing_geom['X_Rot'], Fold_Loc=wing_geom['Fold_Loc'], Tip_X_rot=wing_geom['Tip_X_rot'])

wing.add_flaps(Flap_Y_offset=wing_flap["Flap_Y_start"], cf_c_1=wing_flap['cf_c_1'], cf_c_2=wing_flap['cf_c_2'])
wing.add_ailerons(b1_offset=wing_ail['b1_offset'], b2_ail=wing_ail['b2_ail'], ca_c1=wing_ail['ca_c1'], ca_c2=wing_ail['ca_c2'])
wing.add_slats(b1_slat=wing_slat['b1_slat'], b2_slat=wing_slat['b2_slat'], cs_c1=wing_slat['cs_c1'], cs_c2=wing_slat['cs_c2'])

# Plot Wing Planform
fig, ax = plt.subplots()
wing.plan_plot(ax)
plt.show()
'''

#####################
# HStab
#####################

class HStab(planform):
    def __init__(self, name, S, AR, lam, LE_swp, YLoc_HT, ZLoc_HT, L_offset=0):
        super().__init__(name, S, AR, lam, LE_swp, L_offset)

        self.Y_Loc = YLoc_HT
        self.Z_Loc = ZLoc_HT 

    def calc_coords(self):
        # tabulate coordinates for AVL export
        # Store LE points for AVL usage
        self.xLE_pts = [-self.xpoints[0], -self.xpoints[1]]
        self.yLE_pts = [self.ypoints[0] + self.Y_Loc, self.ypoints[1]+ self.Y_Loc]
        self.zLE_pts = [self.Z_Loc, self.Z_Loc]

        # Store chord length for AVL usage
        self.chords = [self.c_r, self.c_t]

# Testing, enable if plotting hstab on own
'''
L_HT = Hstab_parm['L_HT_frac'] * L_fuse
S_HT = (Hstab_parm['c_HT'] * wing.c_bar * S_w) / L_HT

# Call HStab class to define the hstab
hstab = HStab('HStab', S=S_HT, AR=Hstab_parm['AR_HT'], lam=Hstab_parm['lambda_HT'], LE_swp=Hstab_parm['LE_swp_HT'], 
              YLoc_HT=Hstab_geom['YLoc_HT'], ZLoc_HT=Hstab_geom['ZLoc_HT'])

# Plot HStab Planform (local coordinates)
fig, ax = plt.subplots()
hstab.plan_plot(ax)
plt.show()

# Move HStab to global location w.r.t. to wing
L_abs_HT = L_HT + abs(wing.quart_mac_y) - abs(hstab.quart_mac_y)
hstab.set_global_loc(new_L_offset=L_abs_HT)

# Plot HStab & Wing Planform
fig, ax = plt.subplots()
wing.plan_plot(ax)
hstab.plan_plot(ax)
plt.show()'''


#####################
# VStab
#####################

class VStab(planform):
    def __init__(self, name, S, AR, lam, LE_swp, Y_loc_VT, Z_loc_VT, X_rot_VT, L_offset=0):
        super().__init__(name, S, AR, lam, LE_swp, L_offset)

        self.Y_loc = Y_loc_VT
        self.Z_loc = Z_loc_VT
        self.X_rot = X_rot_VT

    def add_rudder(self, cr_c1, cr_c2, b1_rud, b2_rud):
        self.ss['rudder'] = {
            'b1_rud': b1_rud,
            'b2_rud': b2_rud,
            'c1_rud': cr_c1,
            'c2_rud': cr_c2
        }

        self._calc_coords()
    
    def _calc_coords(self):
        span_fracs = np.unique([
            0.0, 
            self.ss['rudder']['b1_rud'], 
            self.ss['rudder']['b2_rud'], 
            1.0
        ])
        
        # Calculate local spanwise distance (s) along the surface
        s = (self.b / 2) * span_fracs
        
        # Vectorize X, Y, Z, and Chord calculations simultaneously
        gamma = np.deg2rad(self.X_rot)
        
        xLE = s * np.tan(self.LE_swp_rad) + self.L_offset
        yLE = self.Y_loc + (s * np.cos(gamma))
        zLE = self.Z_loc + (s * np.sin(gamma))
        chords = self.c_r - ((self.c_r - self.c_t) * span_fracs)
        
        # Convert arrays back to standard Python lists for JSON export
        self.xLE_pts = xLE.tolist()
        self.yLE_pts = yLE.tolist()
        self.zLE_pts = zLE.tolist()
        self.chords = chords.tolist()

        #print(f"LE POINT OF VSTAB: {self.LE_point}")

# Testing; enable if plotting VStab independently.
'''
L_VT = VStab_parm['L_VT_frac'] * L_fuse
S_VT = (VStab_parm['c_VT'] * wing.b * wing.S) / L_VT

# Define VStab class
vstab = VStab('VStab', S=S_VT, AR=2*VStab_parm['AR_VT'], lam=VStab_parm['lambda_VT'], LE_swp=VStab_parm['LE_swp_VT'], 
              Y_loc_VT=VStab_geom['Y_loc_VT'], Z_loc_VT=VStab_geom['Z_loc_VT'], X_rot_VT=VStab_geom['X_rot_VT'])

vstab.add_rudder(cr_c1=Vstab_rud['cr_c1'], cr_c2=Vstab_rud['cr_c2'], b1_rud=Vstab_rud['b1_rud'], b2_rud=Vstab_rud['b2_rud'])

# Plot VStab Planform (local coords)
fig, ax = plt.subplots()
vstab.plan_plot(ax)
plt.show()

# Move Vstab to global location
L_abs_VT = L_VT + abs(wing.quart_mac_y) - abs(vstab.quart_mac_y)
vstab.set_global_loc(new_L_offset=L_abs_VT)

# Plot VStab, HStab & Wing Planform
fig, ax = plt.subplots()
wing.plan_plot(ax)
hstab.plan_plot(ax)
vstab.plan_plot(ax)
plt.show()'''


#####################
# Aircraft
#####################
# Top-level class housing all surfaces 

class Aircraft:
    def __init__(self, name, L_fuse):
        self.name = name
        self.L_fuse = L_fuse

        self.surfaces = {}

    def add_wing(self, wing_object):
        self.surfaces['Wing'] = wing_object


    def add_hstab(self, Hstab_parm, Hstab_geom): # CALL AFTER CREATING wing OBJECT
        # Calculate tail arm and surface area
        L_HT = Hstab_parm['L_HT_frac'] * L_fuse
        S_HT = (Hstab_parm['c_HT'] * wing.c_bar * S_w) / L_HT

        # Call HStab class to create Hstab, assign to Aircraft.surfaces
        hstab = HStab('HStab', S=S_HT, AR=Hstab_parm['AR_HT'], lam=Hstab_parm['lambda_HT'], LE_swp=Hstab_parm['LE_swp_HT'], 
              YLoc_HT=Hstab_geom['YLoc_HT'], ZLoc_HT=Hstab_geom['ZLoc_HT'])
        hstab.L_HT = L_HT
        self.surfaces['HStab'] = hstab
        
        # Move HStab to global location w.r.t. to wing
        L_abs_HT = L_HT + abs(wing.quart_mac_y) - abs(hstab.quart_mac_y)
        hstab.L_abs_HT = L_abs_HT
        hstab.set_global_loc(new_L_offset=L_abs_HT)

        # re-calculate points for AVL export
        hstab.calc_coords()


    def add_vstab(self, VStab_parm, VStab_geom, Vstab_rud): # CALL AFTER CREATING wing OBJECT
        # Calc. tail arm and area
        L_VT = VStab_parm['L_VT_frac'] * L_fuse
        S_VT = (VStab_parm['c_VT'] * wing.b * wing.S) / L_VT

        # Create VStab, assign to Aircraft.surfaces
        vstab = VStab('VStab', S=S_VT, AR=2*VStab_parm['AR_VT'], lam=VStab_parm['lambda_VT'], LE_swp=VStab_parm['LE_swp_VT'], 
              Y_loc_VT=VStab_geom['Y_loc_VT'], Z_loc_VT=VStab_geom['Z_loc_VT'], X_rot_VT=VStab_geom['X_rot_VT'])
        vstab.add_rudder(cr_c1=Vstab_rud['cr_c1'], cr_c2=Vstab_rud['cr_c2'], b1_rud=Vstab_rud['b1_rud'], b2_rud=Vstab_rud['b2_rud'])
        vstab.L_VT = L_VT
        self.surfaces['VStab'] = vstab

        # Move Vstab to global location
        L_abs_VT = L_VT + abs(wing.quart_mac_y) - abs(vstab.quart_mac_y)
        vstab.L_abs_VT = L_abs_VT
        vstab.set_global_loc(new_L_offset=L_abs_VT)

        # re-calculate points for AVL export
        vstab._calc_coords()


    def plot_plane(self, ax): # Plot aircraft planform in 2D top-down on XY plane
        for name, surface in self.surfaces.items():
            surface.plan_plot(ax)

    #def plot_3D(self, a):
        # implement in future if time, use plotly to make a 3D visualization of the planform

    def json_export(self, fname):
        wing = self.surfaces['Wing']
        hstab = self.surfaces['HStab']
        vstab = self.surfaces['VStab']

        geom_def = {
            "wing": {
                'b_w': wing.b,
                'S_w': wing.S,
                'ar_w': wing.AR,
                'lamb_w': wing.lam,
                'c_r_w': wing.c_r,
                'c_t_w': wing.c_t,
                'c_bar': wing.c_bar,
                'swp_w': wing.LE_swp,
                'swp_mac25_w': wing.quart_mac_swp,
                'b_fold': wing.fold_loc,
                "flap_1_span": wing.ss['flap']['b1_flap'],
                "flap_2_span": wing.ss['flap']['b2_flap'],
                "flap_c_frac1": wing.ss['flap']['c1_flap'],
                "flap_c_frac2": wing.ss['flap']['c2_flap'],
                "ail_1_span": wing.ss['aileron']['b1_ail'],
                "ail_2_span": wing.ss['aileron']['b2_ail'],
                "ail_c_frac1": wing.ss['aileron']['c1_ail'],
                "ail_c_frac2": wing.ss['aileron']['c2_ail'],
                "slat_1_span": wing.ss['slat']['b1_slat'],
                "slat_2_span": wing.ss['slat']['b2_slat'],
                "slat_c_frac1": wing.ss['slat']['c1_slat'],
                "slat_c_frac2": wing.ss['slat']['c2_slat'],
                "Z_loc": wing.Z_loc,
                "Y_rot": wing.Y_rot,
                "X_rot": wing.X_rot,
                "Tip_X_rot": wing.washout,
                'cntl_sqs': wing_control,
                'xLE_pts': wing.xLE,
                'yLE_pts': wing.yLE,
                'zLE_pts': wing.zLE,
                'chords': wing.chords
            },
            "hstab": {
                "b_HT": hstab.b,
                "S_HT": hstab.S,
                "c_r_HT": hstab.c_r,
                "c_t_HT": hstab.c_t,
                "swp_HT": hstab.LE_swp,
                "x_loc_HT": hstab.L_abs_HT,
                "Y_loc": hstab.Y_Loc,
                "Z_loc": hstab.Z_Loc,
                'cntl_sqs': Hstab_control,
                'xLE_pts': hstab.xLE_pts,
                'yLE_pts': hstab.yLE_pts,
                'zLE_pts': hstab.zLE_pts,
                'chords': hstab.chords
            },
            "vstab": {
                "b_VT": vstab.b,
                "S_VT": vstab.S,
                "AR_VT": vstab.AR,
                "c_r_VT": vstab.c_r,
                "c_t_VT": vstab.c_t,
                "swp_VT": vstab.LE_swp,
                "swp_25mac_VT": vstab.quart_mac_swp,
                "lam_VT": vstab.lam,
                "L_VT": vstab.L_VT,
                "rud_c_frac": vstab.ss['rudder']['c1_rud'], ### COME BACK AND CHANGE THIS ONCE WE TEST
                "rud_1_span": vstab.ss['rudder']['b1_rud'],
                "rud_2_span": vstab.ss['rudder']['b2_rud'],
                "x_loc_VT": vstab.L_abs_VT,
                "Y_loc": vstab.Y_loc,
                "Z_loc": vstab.Z_loc,
                "X_rot": vstab.X_rot,
                'cntl_sqs': Vstab_control,
                'xLE_pts': vstab.xLE_pts,
                'yLE_pts': vstab.yLE_pts,
                'zLE_pts': vstab.zLE_pts, 
                'chords': vstab.chords
            }
        }

        # Get local directory, save json there
        dir = Path(__file__).parent
        json_path = os.path.join(dir, fname)
        with open(json_path, 'w') as json_file:
            json.dump(geom_def, json_file, indent=4)

        

########################
# AIRCRAFT CONSTRUCTOR #
########################
# Call all classes and methods to model aircraft

# Create Wing
wing = Wing('Wing', S=S_w, AR=wing_parm["AR"], lam=wing_parm["lambda_w"], LE_swp=wing_parm["LE_swp"], L_offset=0,
            Z_loc=wing_geom["Z_loc"], Y_rot=wing_geom["Y_rot"], X_rot=wing_geom['X_Rot'], Fold_Loc=wing_geom['Fold_Loc'], Tip_X_rot=wing_geom['Tip_X_rot'])

wing.add_flaps(Flap_Y_offset=wing_flap["Flap_Y_start"], cf_c_1=wing_flap['cf_c_1'], cf_c_2=wing_flap['cf_c_2'])
wing.add_ailerons(b1_offset=wing_ail['b1_offset'], b2_ail=wing_ail['b2_ail'], ca_c1=wing_ail['ca_c1'], ca_c2=wing_ail['ca_c2'])
wing.add_slats(b1_slat=wing_slat['b1_slat'], b2_slat=wing_slat['b2_slat'], cs_c1=wing_slat['cs_c1'], cs_c2=wing_slat['cs_c2'])

wing.calc_coords()

# Add to aircraft
F24HH = Aircraft(name='F24HH', L_fuse=L_fuse)
F24HH.add_wing(wing)

# Create HStab, Vstab
F24HH.add_hstab(Hstab_parm=Hstab_parm, Hstab_geom=Hstab_geom)
F24HH.add_vstab(VStab_parm=VStab_parm, VStab_geom=VStab_geom, Vstab_rud=Vstab_rud)

# Plot aircraft planform projection on XY plane
fig, ax = plt.subplots()
F24HH.plot_plane(ax)
plt.title('F24HH Planform')
#plt.show()

# Export as json
F24HH.json_export(fname='airplane_geom2.json')

#pprint.pprint(vars(F24HH.surfaces['HStab']))

#pprint.pprint(wing.xpoints)