"""
Automatically model a simple aircraft in OpenVSP. Calculate and assign wing, wing fuel tank, tail masses. Run CompGeom, MassProp, VSPAERO.
"""
import openvsp_config
# disable graphics for dask parallel computing
openvsp_config.LOAD_GRAPHICS = False
openvsp_config.LOAD_FACADE = False

import openvsp as vsp
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np
import pprint 
from collections import defaultdict
from dataclasses import dataclass
import logging

from utils import atmos 

# Initialize config file, contains files and constants
@dataclass
class Config:
    vsp_filename: str
    geom_def_path: str| dict
    fuse_file_path: str
    wing_foils: list       # Root, Mid, Tip; .dat format
    tail_foils: list       # VStab root & tip, HStab tip, HStab root

    # Fixed Weights Parameters
    W_dg: float = 42449  # Design Gross Weight !!! MUST CHANGE TO USE 50% FUEL !!!, lbs
    N_z: float = 10.5      # Design Ultimate Load Factor (7*1.5)
    tc_rt: float = 0.06    # Wing Airfoil Thickness @ Root
    F_w: float = 6.0       # Fuselage Width @ HStab intersection, ft
    M: float = 1.6         # Design Max Mach Number
    rho_fuel: float = 6.65 # Density of JP-5 Fuel, lbs/ft^2


########################
# VSP INTERFACE
########################

class VSP_Interface:
    '''
    Class to interface with OpenVSP. Script in wing and tail geometry, input mass parameters, run analyses (VSPAERO, CompGeom, MassProp).
    '''

    def __init__(self, config: Config, global_x_transl: float = 16.0, save_dir: str = None):
        '''
        Initializes inputs, file paths and containers. 

        Args: 
            config (Config): Contains file paths and constants. 
            global_x_transl (float): The X offset distance applied to all modeled objects relative to the origin
            save_dir (str): Directory in which to save the vsp3 file
        '''

        self.config = config
        self.global_x_transl = global_x_transl

        # Use the provided directory, or default to the Current Working Directory
        self.local_dir = Path(save_dir) if save_dir else Path.cwd()
        vsp_file_name = f'{self.config.vsp_filename}.vsp3'

        self.planefile = os.path.join(self.local_dir, vsp_file_name)

        # Allow either a filepath to a json file, OR a straight dictionary input
        if isinstance(self.config.geom_def_path, (str, os.PathLike)):
            # If a string or Path object is passed, read the file
            with open(self.config.geom_def_path, 'r') as file:
                self.geom = json.load(file)
        elif isinstance(self.config.geom_def_path, dict):
            # If a dictionary is passed directly, just use it
            self.geom = self.config.geom_def_path
        else:
            # Safety net: fail cleanly if the wrong data type is passed
            raise TypeError(f"geom_def_path must be a file path or a dictionary. Got: {type(self.config.geom_def_path)}")

        # Instantiate containers for compgeom results, VSPAERO cases
        self.comp_vols = defaultdict(float)
        self.comp_wet_areas = defaultdict(float)
        self.ss_areas = {}

        # Set up logging
        # Initialize logging
        # removed for parallel processing: logging.FileHandler(os.path.join(Path(__file__).parent, "surf_to_VSP.log"), mode='w')
        logging.basicConfig(handlers=[
                                
                                logging.StreamHandler()
                            ],
                            level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        

    def BuildPlane(self, include_fuse: bool):
        # Build complete aircraft in OpenVSP. Call to generate aircraft

        logging.info('Building Aircraft...')

        vsp.ClearVSPModel()

        #vsp.InitGUI()
        #vsp.StartGUI()

        # Fuselage File
        if include_fuse == True:
            vsp.InsertVSPFile(self.config.fuse_file_path, "")
            logging.info('Importing Fuselage File...')
        elif include_fuse == False:
            logging.info('Fuselage Excluded...')

        vsp.SetAllViews(vsp.CAM_LEFT_ISO)
        vsp.FitAllViews()
        #vsp.UpdateGUI()
        
        self._Build_Wing()
        #vsp.UpdateGUI()
        self._Build_HStab()
        #vsp.UpdateGUI()
        self._Build_VStab()

        vsp.SetAllViews(vsp.CAM_LEFT_ISO)
        vsp.FitAllViews()
        #vsp.UpdateGUI()
        #vsp.StopGUI()

        vsp.Update()
        vsp.WriteVSPFile(self.planefile)
        logging.info(f'Successfully modeled aircraft, saved to {self.planefile}')

    def _Build_Wing(self):
        # Create wing geometry, conformal fuel tanks, and control surfaces. Internal method, don't call externally

        # Load wing data
        wing = self.geom['wing']

        wing_id = vsp.AddGeom("WING", "")
        vsp.SetGeomName(wing_id, "Main_Wing")

        #Define Fold Sections
        y_fold = wing["b_fold"]
        b_half = wing["b_w"]/2
        c_root = wing["c_r_w"]
        c_tip = wing["c_t_w"]

        c_mid = c_root + ((c_tip - c_root) / b_half) * y_fold

        #Inboard Section
        vsp.InsertXSec(wing_id, 1, vsp.XS_FILE_AIRFOIL)
        vsp.Update()

        vsp.SetParmVal(wing_id, "Span", "XSec_1", y_fold)
        vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", c_root)
        vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", c_mid)
        vsp.SetParmVal(wing_id, "Sweep_Location", "XSec_1", 0.0)
        vsp.SetParmVal(wing_id, "Sweep", "XSec_1", wing["swp_w"])
        vsp.SetParmVal(wing_id, "SectTess_U", "XSec_1", 40) 

        #Folding Outer Panel
        vsp.SetParmVal(wing_id, "Span", "XSec_2", b_half - y_fold)
        vsp.SetParmVal(wing_id, "Root_Chord", "XSec_2", c_mid)
        vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_2", c_tip)
        vsp.SetParmVal(wing_id, "Sweep_Location", "XSec_2", 0.0)
        vsp.SetParmVal(wing_id, "Sweep", "XSec_2", wing["swp_w"])
        vsp.SetParmVal(wing_id, "SectTess_U", "XSec_2", 20)
        vsp.SetParmVal(wing_id, 'Twist', 'XSec_2', wing['Tip_X_rot'])

        # Global Positioning 
        vsp.SetParmVal(wing_id, "X_Rel_Location", "XForm", self.global_x_transl)
        vsp.SetParmVal(wing_id, "Z_Rel_Location", "XForm", wing["Z_loc"])
        vsp.SetParmVal(wing_id, "Y_Rel_Rotation", "XForm", wing["Y_rot"])
        vsp.SetParmVal(wing_id, "X_Rel_Rotation", "XForm", wing["X_rot"])
        
        # Increase Num_W
        vsp.SetParmVal(wing_id, 'Tess_W', 'Shape', 41)

        #Assign to set0, 3, 19
        ########### SET0 = WING/TANK, TAILS, FUSE SURFACE;  SET3 = WING & TAIL ONLY;   SET19 = ALL MASS (USE FOR CG CALC)
        self.set_0_idx = vsp.GetSetIndex("Set_0")
        self.set_3_idx = vsp.GetSetIndex("Set_3")
        self.set_19_idx = vsp.GetSetIndex("Set_19")
        vsp.SetSetFlag(wing_id, self.set_0_idx, True)
        vsp.SetSetFlag(wing_id, self.set_3_idx, True)
        vsp.SetSetFlag(wing_id, self.set_19_idx, True)

        #Set Wing Airfoils
        xsec_surf = vsp.GetXSecSurf(wing_id, 0)
        vsp.ChangeXSecShape(xsec_surf, 0, vsp.XS_FILE_AIRFOIL)
        vsp.ChangeXSecShape(xsec_surf, 1, vsp.XS_FILE_AIRFOIL)

        root_xsec = vsp.GetXSec(xsec_surf, 0)
        fold_xsec = vsp.GetXSec(xsec_surf, 1)
        tip_xsec = vsp.GetXSec(xsec_surf, 2)

        vsp.ReadFileAirfoil(root_xsec, self.config.wing_foils[0])
        vsp.ReadFileAirfoil(fold_xsec, self.config.wing_foils[1])
        vsp.ReadFileAirfoil(tip_xsec, self.config.wing_foils[2])


        ## FUEL TANKS ## (tweak the hardcoded values to change the tank geometry. if time, remove hardcoded values and pass parms)
        wtank_id = vsp.AddGeom("CONFORMAL", wing_id)
        vsp.SetGeomName(wtank_id, "Wing Fuel Tank")

        vsp.SetParmVal(wtank_id, "Offset", "Design", 0.05)
        vsp.SetParmVal(wtank_id, "UTrimFlag", "Design", 1)
        vsp.SetParmVal(wtank_id, "ChordTrimFlag", "Design", 1)

        vsp.SetParmVal(wtank_id, "UMinTrimTypeFalg", "Design", 2)
        vsp.SetParmVal(wtank_id, "UMaxTrimTypeFalg", "Design", 2)

        vsp.SetParmVal(wtank_id, "ChordTrimMin", "Design", wing["flap_c_frac1"] + 0.02)
        vsp.SetParmVal(wtank_id, "ChordTrimMax", "Design", 1 - wing["slat_c_frac2"])

        vsp.SetParmVal(wtank_id, "EtaTrimMin", "Design", 0.15)
        vsp.SetParmVal(wtank_id, "EtaTrimMax", "Design", y_fold/b_half - 0.02)

        vsp.SetSetFlag(wtank_id, self.set_19_idx, True)


        ## CONTROL SUBSURFACES ##
        # Flaps
        flap_id = vsp.AddSubSurf(wing_id, vsp.SS_CONTROL)
        vsp.SetSubSurfName(wing_id, flap_id, "Flaps")

        vsp.SetParmVal(flap_id, 'EtaFlag', 'SS_Control', 1.0)
        vsp.SetParmVal(flap_id, 'EtaStart', 'SS_Control', wing['flap_1_span'])
        vsp.SetParmVal(flap_id, 'EtaEnd', 'SS_Control', wing['flap_2_span'])
        vsp.SetParmVal(flap_id, 'Length_C_Start', 'SS_Control', wing['flap_c_frac1'])
        vsp.SetParmVal(flap_id, 'Length_C_End', 'SS_Control', wing['flap_c_frac2'])

        # Ailerons
        ail_id = vsp.AddSubSurf(wing_id, vsp.SS_CONTROL)
        vsp.SetSubSurfName(wing_id, ail_id, "Ailerons")

        vsp.SetParmVal(ail_id, 'EtaFlag', 'SS_Control', 1.0)
        vsp.SetParmVal(ail_id, 'EtaStart', 'SS_Control', wing['ail_1_span'])
        vsp.SetParmVal(ail_id, 'EtaEnd', 'SS_Control', wing['ail_2_span'])
        vsp.SetParmVal(ail_id, 'Length_C_Start', 'SS_Control', wing['ail_c_frac1'])
        vsp.SetParmVal(ail_id, 'Length_C_End', 'SS_Control', wing['ail_c_frac2'])

        # Slats
        slat_id = vsp.AddSubSurf(wing_id, vsp.SS_CONTROL)
        vsp.SetSubSurfName(wing_id, slat_id, "Slats")

        vsp.SetParmVal(slat_id, 'EtaFlag', 'SS_Control', 1.0)
        vsp.SetParmVal(slat_id, 'SE_Const_Flag', 'SS_Control', 0.0)
        vsp.SetParmVal(slat_id, 'LE_Flag', 'SS_Control', 1.0)
        vsp.SetParmVal(slat_id, 'EtaStart', 'SS_Control', wing['slat_1_span'])
        vsp.SetParmVal(slat_id, 'EtaEnd', 'SS_Control', wing['slat_2_span'])
        vsp.SetParmVal(slat_id, 'Length_C_Start', 'SS_Control', wing['slat_c_frac1'])
        vsp.SetParmVal(slat_id, 'Length_C_End', 'SS_Control', wing['slat_c_frac2'])

        logging.info('Modeled Wing...')

    def _Build_HStab(self):
        # Build the HStab in OpenVSP. Internal method, don't call externally

        # Load HStab data
        hstab = self.geom['hstab']

        #Define the HStab
        hstab_id = vsp.AddGeom("WING", "")
        vsp.SetGeomName(hstab_id, "HStab")
        vsp.SetSetFlag(hstab_id, self.set_0_idx, True)
        vsp.SetSetFlag(hstab_id, self.set_3_idx, True)
        vsp.SetSetFlag(hstab_id, self.set_19_idx, True)

        vsp.SetParmVal(hstab_id, "Span", "XSec_1", hstab["b_HT"]/2)
        vsp.SetParmVal(hstab_id, "Root_Chord", "XSec_1", hstab["c_r_HT"])
        vsp.SetParmVal(hstab_id, "Tip_Chord", "XSec_1", hstab["c_t_HT"])
        vsp.SetParmVal(hstab_id, "Sweep_Location", "XSec_1", 0)
        vsp.SetParmVal(hstab_id, "Sweep", "XSec_1", hstab["swp_HT"])
        vsp.SetParmVal(hstab_id, "SectTess_U", "XSec_1", 41)
        vsp.SetParmVal(hstab_id, "X_Rel_Location", "XForm", hstab["x_loc_HT"] + self.global_x_transl)
        vsp.SetParmVal(hstab_id, "Y_Rel_Location", "XForm", hstab["Y_loc"])
        vsp.SetParmVal(hstab_id, "Z_Rel_Location", "XForm", hstab["Z_loc"])

        # Increase Num_W
        vsp.SetParmVal(hstab_id, 'Tess_W', 'Shape', 61)

        #Define the HStab Airfoil
        hstab_xsec_surf = vsp.GetXSecSurf(hstab_id, 0)
        vsp.ChangeXSecShape(hstab_xsec_surf, 0, vsp.XS_FILE_AIRFOIL)
        vsp.ChangeXSecShape(hstab_xsec_surf, 1, vsp.XS_FILE_AIRFOIL)

        logging.info('Modeled HStab...')

        hstab_root_xsec = vsp.GetXSec(hstab_xsec_surf, 0)
        hstab_tip_xsec = vsp.GetXSec(hstab_xsec_surf, 1)

        vsp.ReadFileAirfoil(hstab_root_xsec, self.config.tail_foils[1])
        vsp.ReadFileAirfoil(hstab_tip_xsec, self.config.tail_foils[0])

    def _Build_VStab(self):
        # Model VStab in OpenVSP. Internal method, don't call externally

        # Load VStab data
        vstab = self.geom['vstab']

        #Define the Vstab
        vstab_id = vsp.AddGeom("WING", "")
        vsp.SetGeomName(vstab_id, "VStab")
        vsp.SetSetFlag(vstab_id, self.set_0_idx, True)
        vsp.SetSetFlag(vstab_id, self.set_3_idx, True)
        vsp.SetSetFlag(vstab_id, self.set_19_idx, True)

        vsp.SetParmVal(vstab_id, "Span", "XSec_1", vstab["b_VT"]/2)
        vsp.SetParmVal(vstab_id, "Root_Chord", "XSec_1", vstab["c_r_VT"])
        vsp.SetParmVal(vstab_id, "Tip_Chord", "XSec_1", vstab["c_t_VT"])
        vsp.SetParmVal(vstab_id, "Sweep_Location", "XSec_1", 0)
        vsp.SetParmVal(vstab_id, "Sweep", "XSec_1", vstab["swp_VT"])
        vsp.SetParmVal(vstab_id, "SectTess_U", "XSec_1", 21)
        vsp.SetParmVal(vstab_id, "X_Rel_Location", "XForm", vstab["x_loc_VT"] + self.global_x_transl)
        vsp.SetParmVal(vstab_id, "Y_Rel_Location", "XForm", vstab["Y_loc"])
        vsp.SetParmVal(vstab_id, "Z_Rel_Location", "XForm", vstab["Z_loc"])
        vsp.SetParmVal(vstab_id, "X_Rel_Rotation", "XForm", vstab["X_rot"])
        #vsp.SetParmVal(vstab_id, "CapBoundFlag", "Endcap", 0.0) # NEW PARMS IN VSP 3.48; DISABLE IF USING 3.47
        #vsp.SetParmVal(vstab_id, "WakeRootFlag", "Endcap", 0.0) # NEW PARMS IN VSP 3.48; DISABLE IF USING 3.47

        vsp.SetParmVal(vstab_id, 'Tess_W', 'Shape', 33)

        #Define the VStab Airfoil
        vstab_xsec_surf = vsp.GetXSecSurf(vstab_id, 0)
        vsp.ChangeXSecShape(vstab_xsec_surf, 0, vsp.XS_FILE_AIRFOIL)
        vsp.ChangeXSecShape(vstab_xsec_surf, 1, vsp.XS_FILE_AIRFOIL)

        vstab_root_xsec = vsp.GetXSec(vstab_xsec_surf, 0)
        vstab_tip_xsec = vsp.GetXSec(vstab_xsec_surf, 1)

        vsp.ReadFileAirfoil(vstab_root_xsec, self.config.tail_foils[0])
        vsp.ReadFileAirfoil(vstab_tip_xsec, self.config.tail_foils[0])


        #Define the Rudder
        rudder_id = vsp.AddSubSurf(vstab_id, vsp.SS_CONTROL)
        vsp.SetSubSurfName(vstab_id, rudder_id, "Rudder")

        vsp.SetParmVal(rudder_id, 'EtaFlag', 'SS_Control', 1.0)
        vsp.SetParmVal(rudder_id, 'EtaStart', 'SS_Control', vstab['rud_1_span'])
        vsp.SetParmVal(rudder_id, 'EtaEnd', 'SS_Control', vstab['rud_2_span'])
        vsp.SetParmVal(rudder_id, 'Length_C_Start', 'SS_Control', vstab['rud_c_frac'])
        vsp.SetParmVal(rudder_id, 'Length_C_End', 'SS_Control', vstab['rud_c_frac'])

        logging.info('Modeled VStab...')

    def Run_CompGeom(self):
        # Runs compgeom on vsp file. By default, runs compgeom on the file modeled by BuildPlane.
        # Returns component volumes, planform areas, and subsurface areas in: self.comp_vols, self.comp_wet_areas, self.ss_areas

        logging.info('Setting up CompGeom Run...')

        # Load vsp file
        vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)

        logging.info(f'Loaded {self.planefile}...')

        # Run CompGeom (Fixed to run only on Set 19, which is wings/tank and tail. Hardcoded value, so change in future if time)
        logging.info(f'Running CompGeom on {self.planefile}, Set {self.set_19_idx}...')
        vsp.ComputeCompGeom(self.set_19_idx, False, 1)

        # Access & Store Results
        compgeom_res_id = vsp.FindLatestResultsID('Comp_Geom')

        # Theoretical Volumes, corresponding component names
        comp_names = vsp.GetStringResults(compgeom_res_id, "Comp_Name")
        theo_vols = vsp.GetDoubleResults(compgeom_res_id, "Theo_Vol")

        for name, vol in zip(comp_names, theo_vols):
            self.comp_vols[name.strip()] += vol

        pprint.pprint(self.comp_vols)

        # Theoretical wetted areas 
        wet_areas = vsp.GetDoubleResults(compgeom_res_id, "Theo_Area")

        for name, area in zip(comp_names, wet_areas):
            self.comp_wet_areas[name.strip()] += area

        #Theoretical Surface Areas, Control Surfaces ## NOTICE: OPENVSP REPORTS THEORETICAL AREA, MEANING WETTED AREA!! Divide by 2 to get planform area.
        ss_names = vsp.GetStringResults(compgeom_res_id, "SubSurf_Name")
        ss_wet_areas = vsp.GetDoubleResults(compgeom_res_id, "SubSurf_Theo_Area")
        ss_plan_areas = [x / 2 for x in ss_wet_areas]   

        self.ss_areas = dict(zip(ss_names, ss_plan_areas))

        logging.info('Succesfully ran CompGeom.')

        vsp.Update()

    def Run_MassProp(self, set: str = 'Set_19', n_slice: float = 100):
        # Runs MassProp (by default uses Set_19, can change if wish), returns CG location in self.cg
        # By default, uses 100 slices. Can change for improved accuracy. Suggest 200. 250 crashed my computer so maybe don't do that
        # Run this analysis only if you want 

        # Returns xCG Location and total Mass
        logging.info('Setting up a Mass Properties Analysis...')

        mass_set_idx = vsp.GetSetIndex(set)

        vsp.SetAnalysisInputDefaults("MassProp")

        vsp.SetIntAnalysisInput('MassProp', 'Set', [mass_set_idx])
        vsp.SetIntAnalysisInput('MassProp', 'NumMassSlices', [n_slice])
        vsp.SetIntAnalysisInput('MassProp', 'MassSliceDir', [vsp.X_DIR])

        logging.info('Running a Mass Properties Analysis...')
        vsp.ExecAnalysis('MassProp')

        mass_res_id = vsp.FindLatestResultsID("Mass_Properties")
        #vsp.PrintResults(mass_res_id)

        self.CG = vsp.GetVec3dResults(mass_res_id, 'Total_CG')[0]
        self.xCG = self.CG.x() # use .y() and .z() for other cg components
        self.yCG = self.CG.y()
        self.zCG = self.CG.z()

        self.tot_mass = vsp.GetDoubleResults(mass_res_id, 'Total_Mass')

        logging.info(f'Calculated Mass Properties: Total Mass = {self.tot_mass[0]} slugs;   XCG = {self.xCG};   ZCG = {self.zCG}')

        return self.xCG, self.yCG, self.zCG, self.tot_mass[0]

    def Assign_Mass(self, densities: dict):
        # Use this method once you run Weigh_Plane.Mass(). Assigns calculated masses of wing, tails and wing tanks to existing vsp model. 
        logging.info(f'Assigning densities to {self.planefile}...')

        vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)

        # Find Component IDs 
        wing_id = vsp.FindGeomsWithName("Main_Wing")[0]
        hstab_id = vsp.FindGeomsWithName("HStab")[0]
        vstab_id = vsp.FindGeomsWithName("VStab")[0]
        ftank_id = vsp.FindGeomsWithName("Wing Fuel Tank")[0]

        # Assign Density of Main Wing
        logging.info('Setting the density of the Wing...')
        vsp.SetParmVal(wing_id, "Density", "Mass_Props", 0)
        vsp.SetParmVal(wing_id, "Shell_Flag", "Mass_Props", 1)
        vsp.SetParmVal(wing_id, 'Mass_Area', 'Mass_Props', densities['Wing_Density'])

        # Assign Density of Hstab
        logging.info('Setting the density of the HStab...')
        vsp.SetParmVal(hstab_id, "Density", "Mass_Props", densities['HStab_Density'])
        vsp.SetParmVal(hstab_id, "Shell_Flag", "Mass_Props", 0.0)

        # Assign Density of Vstab
        logging.info('Setting the density of the VStab...')
        vsp.SetParmVal(vstab_id, "Density", "Mass_Props", densities['VStab_Density'])
        vsp.SetParmVal(vstab_id, "Shell_Flag", "Mass_Props", 0.0)

        #Assign Density of Fuel Tanks
        logging.info('Setting the density of the Fuel Tanks...')
        vsp.SetParmVal(ftank_id, "Density", "Mass_Props", densities['Wing_Tank_Density'])
        vsp.SetParmVal(ftank_id, "Shell_Flag", "Mass_Props", 0.0)
        vsp.SetParmVal(ftank_id, "Mass_Prior", "Mass_Props", 1.0)

        logging.info(f'Succesfully Assigned Masses to {self.planefile}')
    
        vsp.Update()
        vsp.WriteVSPFile(self.planefile)


    def Run_VSPAERO_NP(self, xcg: float, VSPAERO_dir: str = 'VSPAERO_Results'):
        # Run a steady Neutral Point analysis, return NP & SM
        # Creates a copy of the aircraft in VSPAERO_dir (by default VSPAERO_Results), stores results in that directory

        vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)

        logging.info('Setting up a VSPAERO Steady Neutral Point Analysis...')

        self._initialize_NP_VSPAERO(xcg=xcg)

        vsp.Update()

        # Set Up a Separate Directory to house VSPAERO Output files
        results_dir_path = os.path.join(self.local_dir, VSPAERO_dir)
        os.makedirs(results_dir_path, exist_ok=True)
        vspaero_file = os.path.join(results_dir_path, "F24HH_VSPAERO.vsp3")
        vsp.WriteVSPFile(vspaero_file)

        # Compute VSPAERO Mesh 
        logging.info('Computing VSPAERO Mesh')

        vsp.SetAnalysisInputDefaults('VSPAEROComputeGeometry')
        vsp.ExecAnalysis('VSPAEROComputeGeometry')

        # Run VSPAERO Steady Case
        logging.info('Running VSPAERO Steady Case...')

        vsp.SetAnalysisInputDefaults("VSPAEROSweep")
        vsp.ExecAnalysis('VSPAEROSweep')

        # Access Stability Results
        aero_res_id = vsp.FindLatestResultsID("VSPAERO_Stab")

        self.static_margin = vsp.GetDoubleResults(aero_res_id, "SM")[0]
        self.neutral_point = vsp.GetDoubleResults(aero_res_id, "X_np")[0]
            
        logging.info(f"X Neutral Point: {self.neutral_point:.3f}")
        logging.info(f"Static Margin: {self.static_margin:.4f}")

        vsp.Update()
        vsp.WriteVSPFile(self.planefile)

        return self.static_margin, self.neutral_point


    def _initialize_NP_VSPAERO(self, xcg: float):
        # Set up VSPAERO settings for steady NP analysis case
        # By Default, runs on Set_3; which houses only wing and tail surfaces (no fuselage)

        # Grab wing dimensions
        wing = self.geom['wing']

        '''vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)''' # Turn on for testing

        aero_id = vsp.FindContainer("VSPAEROSettings", 0)
        
        # Toggle Steady Analysis
        vsp.SetParmVal(aero_id, "UnsteadyType", "VSPAERO", 1.0)
        
        # Manually enter Ref. Wing parameters
        vsp.SetParmVal(aero_id, "RefFlag", "VSPAERO", 0.0)
        #vsp.SetParmVal(aero_id, 'MACFlag', 'VSPAERO', 1.0)
        vsp.SetParmVal(aero_id, 'Sref', 'VSPAERO', wing['S_w'])
        vsp.SetParmVal(aero_id, 'bref', 'VSPAERO', wing['b_w'])
        vsp.SetParmVal(aero_id, 'cref', 'VSPAERO', wing['c_bar'])
        
        # Use 16 CPUs
        vsp.SetParmVal(aero_id, "NCPU", "VSPAERO", 16.0)

        # Adjust these settings for higher accuracy. Otherwise leave default.
        '''# Adjust number iterations:
        vsp.SetParmVal(aero_id, 'WakeNumIter', 'VSPAERO', 30)

        # Number wake nodes
        vsp.SetParmVal(aero_id, 'RootWakeNodes', 'VSPAERO', 20)'''

        '''# Relaxation
        vsp.SetParmVal(aero_id, 'WakeRelax', 'VSPAERO', 0.5)'''
        
        # Init. CG Calc
        vsp.SetParmVal(aero_id, "NumMassSlice", "VSPAERO", 100.0)
        
        # Present Analysis to Set_3
        current_set3_index = vsp.GetSetIndex("Set_3")
        vsp.SetParmVal(aero_id, "ThinGeomSet", "VSPAERO", float(current_set3_index))
        
        # No Panel Method
        vsp.SetParmVal(aero_id, "GeomSet", "VSPAERO", float(vsp.SET_NONE))

        # Set CG Ref Point
        vsp.SetParmVal(aero_id, 'Xcg', 'VSPAERO', xcg)

        logging.info('Initialized Steady NP Case...')


        # turn on for testing
        '''vsp.Update()
        vsp.WriteVSPFile(self.planefile)'''

    def calc_CD0(self, Mach, alt):
        '''
        Run a parasite drag analysis in OpenVSP

        Args:
            Mach (float): Mach number of flight condition
            Alt (float): Altitude of flight condition
        
        Returns:
            CD0 (float): Parasite Drag
        '''

        # Calculate flight velocity
        rho, a = atmos.atmos(h=alt)
        fvel = Mach * a
        logging.info(f'Flight Velocity = {fvel:.2f} ft/s')

        # Import plane
        vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)

        # Define analysis type name
        analysis = "ParasiteDrag"

        # Clear any previous results 
        #vsp.DeleteAllResults()
        
        # Debugging; print all available analysis inputs 
        #vsp.PrintAnalysisInputs("ParasiteDrag")

        # Set analysis inputs
        logging.info('Setting up a Parasite Drag Analysis...')
        vsp.SetIntAnalysisInput(analysis, "GeomSet", [self.set_0_idx])
        vsp.SetDoubleAnalysisInput(analysis, "Sref", [self.geom['wing']['S_w']])
        vsp.SetDoubleAnalysisInput(analysis, "Vinf", [fvel])
        vsp.SetDoubleAnalysisInput(analysis, "Altitude", [alt])

        logging.info('Running a Parasite Drag Analysis...')
        res_id = vsp.ExecAnalysis(analysis)

        # Debugging, print all results
        #vsp.PrintResults(res_id)

        # Grab results
        CD0 = vsp.GetDoubleResults(res_id, "Total_CD_Total")
        logging.info(f'Parasite Drag = {CD0[0]}')

        vsp.Update()
        vsp.WriteVSPFile(self.planefile)

        return CD0[0]

    def calc_CD_wave(self, Mach):
        '''
        Run a wave drag analysis in OpenVSP

        Args:
            Mach (float): Mach number of flight condition
        
        Returns:
            CD0_w (float): Wave Drag
        '''

        # Import plane
        vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)

        # Analysis type
        wave = "WaveDrag"

        # we have to specify the wave drag settings in two methods
        wd_id = vsp.FindContainer("WaveDragSettings", 0)

        vsp.SetParmVal(wd_id, "RefFlag", "WaveDrag", 0.0) 
        vsp.SetParmVal(wd_id, "Sref", "WaveDrag", self.geom['wing']['S_w'])

        vsp.Update()

        # Clear any previous results 
        #vsp.DeleteAllResults()

        # Set analysis inputs
        logging.info('Setting up a Wave Drag Analysis...')
        vsp.SetIntAnalysisInput(wave, "Set", [self.set_0_idx])
        vsp.SetDoubleAnalysisInput(wave, "Mach", [Mach])
        
        #vsp.PrintAnalysisInputs("WaveDrag")

        # Execute Analysis
        logging.info('Running a Wave Drag Analysis...')
        res_id = vsp.ExecAnalysis(wave)

        #vsp.PrintResults(res_id)

        # Grab results
        CD_wave = vsp.GetDoubleResults(res_id, "CDWave")
        logging.info(f'Wave Drag = {CD_wave[0]}')

        vsp.Update()
        vsp.WriteVSPFile(self.planefile)

        return CD_wave[0]


    def Tester(self):
        # A method to test other methods that interface with vsp. (so no need to have all methods import and save files)
        vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)
        #################################
        # call test method here
        
        #################################
        vsp.Update()
        vsp.WriteVSPFile(self.planefile)


    def ID_Helper(self, geom_id):
        """
        helper function to print every parameter, its group, and its API name 
        for a given OpenVSP geometry ID. Run this if you are having trouble finding the right parameter names
        """
        print(f"\n--- Parameters for Geometry ID: {geom_id} ---")
        
        # get all parm IDs in this geometry's container
        parm_ids = vsp.FindContainerParmIDs(geom_id)
        
        print(f"{'GROUP NAME':<20} | {'PARAMETER NAME':<25} | {'CURRENT VALUE'}")
        print("-" * 65)
        
        # loop through and extract group, name, and value
        for p_id in parm_ids:
            group_name = vsp.GetParmGroupName(p_id)
            parm_name = vsp.GetParmName(p_id)
            
            # try to get it as a float; covers toggles and numbers
            try:
                val = vsp.GetParmVal(p_id)
            except:
                val = "N/A"
                
            print(f"{group_name:<20} | {parm_name:<25} | {val}")
        print("-" * 65 + "\n")



########################
# WEIGHTS CALCULATOR
########################

class Weigh_Plane:
    # Class to calculate wing, hstab, vstab, and fuel tank weights/masses per Raymer's Eqns. 
    # Must be run after you initialize VSP Model using VSP_Interface, VSP_Interface.BuildPlane(), VSP_Interface.RunCompGeom()
    def __init__(self, manager: VSP_Interface):
        self.manager = manager
        self.config = manager.config
        self.masses = {}
        self.weights = {}

    def Mass(self):
        # Calculate mass of Wing, Wing Tank, Tails.  
        # Returns dictionary with densities [slug/ft^3], [slug/ft^2] for each component
        self._WingMass()
        self._HStabMass()
        self._VStabMass()
        self._WTankMass()

        # Weights of JUST Wing, HStab, VStab
        self.tot_surf_mass = self.M_w_slug + self.M_HT_slug + self.M_VT_slug
        self.tot_surf_weight = self.W_w_lbf + self.W_HT_lbf + self.W_VT_lbf

        # Tabulation of Total Weights
        self.Weights = [self.W_w_lbf, self.W_HT_lbf, self.W_VT_lbf, self.W_WTank_Fuel_lbf, self.tot_surf_weight + self.W_WTank_Fuel_lbf]
        self.Masses = [self.M_w_slug, self.M_HT_slug, self.M_VT_slug, self.M_WTank_Fuel_slug, self.tot_surf_mass + self.M_WTank_Fuel_slug]
        self.mlabels = ['Wing', 'HStab', 'VStab', 'Wing Fuel Tanks', 'Total']

        self.mass_df = pd.DataFrame({
            'Weight [lbf]': self.Weights,
            'Mass [slugs]': self.Masses
        }, index=self.mlabels)

        print(self.mass_df.round(3))

        logging.info(f'Total Weight of Flying Surfaces = {self.tot_surf_weight:.2f} lbf;   Total Mass of Flying Surfaces = {self.tot_surf_mass:.2f} slugs')

        # Store masses in a dictionary to use later
        self.mass_dict = dict(zip(self.mlabels, self.Masses))

        # Calculate required density ([slug/ft^3] for Wing Tank, Tails) ([slug/ft^2] for Wing) for each component
        self.comp_dens = {
            'Wing_Density': self.M_w_slug / self.manager.comp_wet_areas['Main_Wing'],
            'Wing_Tank_Density': self.M_WTank_Fuel_slug / self.manager.comp_vols['Wing Fuel Tank'],
            'HStab_Density': self.M_HT_slug / self.manager.comp_vols['HStab'],
            'VStab_Density': self.M_VT_slug / self.manager.comp_vols['VStab']
        }

        return self.comp_dens, self.mass_df.round(3)


    def _WingMass(self):
        # Estimate wing weight per Raymer's Eqns. (Internal method)
        logging.info('Calculating Wing Weight...')
        wing = self.manager.geom['wing']

        self.S_csw = self.manager.ss_areas['Main_Wing,Ailerons'] + self.manager.ss_areas['Main_Wing,Flaps'] + self.manager.ss_areas['Main_Wing,Slats']

        self.W_w_lbf = 0.0103 * (self.config.W_dg * self.config.N_z)**0.5 * wing['S_w']**0.622 * wing['ar_w']**0.785 * self.config.tc_rt**(-0.4) * (1 + wing['lamb_w'])**0.05 * (np.cos(np.deg2rad(wing['swp_mac25_w'])))**(-1.0) * self.S_csw**0.04
        self.M_w_slug = self.W_w_lbf / 32.174
        
        logging.info(f'Wing Weight = {self.W_w_lbf:.2f} lbf;   Wing Mass = {self.M_w_slug:.2f}slugs')

        # Log weights variables in dictionary
        self.wing_weight_parms = {
            'W_dg': self.config.W_dg,
            'N_z': self.config.N_z,
            'S_w': wing['S_w'],
            'A': wing['ar_w'],
            'tc_rt': self.config.tc_rt,
            'lambda_w': wing['lamb_w'],
            '25MAC_Swp': wing['swp_mac25_w'],
            'S_csw': self.S_csw
        }

        logging.info('Wing Weight Parameters:')
        pprint.pprint(self.wing_weight_parms)

        # Store MAC information for later
        self.W_MAC = wing['c_bar']

    def _HStabMass(self):
        # Estimate hstab mass per Raymer's Eqns. (Internal method)
        logging.info('Calculating HStab Weight')
        hstab = self.manager.geom['hstab']

        self.W_HT_lbf = 3.316 * (1 + self.config.F_w / hstab['b_HT'])**(-2.0) * ((self.config.W_dg * self.config.N_z) / 1000)**0.260 * hstab['S_HT']**0.806
        self.M_HT_slug = self.W_HT_lbf / 32.174

        logging.info(f'HStab Weight = {self.W_HT_lbf:.2f} lbf;   HStab Mass = {self.M_HT_slug:.2f} slugs')

        # Log weights variables
        self.hstab_weight_parms = {
            'F_w': self.config.F_w,
            'B_h': hstab['b_HT'],
            'W_dg': self.config.W_dg,
            'N_z': self.config.N_z,
            'S_ht': hstab['S_HT']
        }

        logging.info('HStab Weight Parameters:')
        pprint.pprint(self.hstab_weight_parms)

    def _VStabMass(self):
        # Estimate vstab mass per Raymer's Eqns. (Internal Method)
        logging.info('Calculating VStab Weight')
        vstab = self.manager.geom['vstab']

        self.S_r = self.manager.ss_areas['VStab,Rudder']

        self.W_VT_lbf = 0.452 * (1)**0.5 * (self.config.W_dg * self.config.N_z)**0.488 * vstab['S_VT']**0.718 * self.config.M**0.341 * vstab['L_VT']**(-1.0) * (1 + self.S_r / vstab['S_VT'])**0.348 * vstab['AR_VT']**0.233 * (1 + vstab['lam_VT'])**0.25 * np.cos(np.deg2rad(vstab['swp_25mac_VT']))**(-0.323)
        self.M_VT_slug = self.W_VT_lbf / 32.174

        logging.info(f'VStab Weight = {self.W_VT_lbf:.2f} lbf;   VStab Mass = {self.M_VT_slug:.2f} slugs')

        # Log weights variables
        self.vstab_weight_parms = {
            'W_dg': self.config.W_dg,
            'N_z': self.config.N_z,
            'S_VT': vstab['S_VT'],
            'M': self.config.M,
            'L_t': vstab['L_VT'],
            'S_r': self.S_r,
            'A_VT': vstab['AR_VT'],
            'lambda': vstab['lam_VT'],
            '25MAC_swp': vstab['swp_25mac_VT']
        }

        logging.info('VStab Weights Parameters:')
        pprint.pprint(self.vstab_weight_parms)

    def _WTankMass(self):
        # Calculate Mass of fuel in wing tanks 
        logging.info('Calculating Mass of Fuel in Wing Tanks...')

        self.wtank_vol_gal = self.manager.comp_vols['Wing Fuel Tank'] / 0.1336805556
        self.W_WTank_Fuel_lbf = self.wtank_vol_gal * self.config.rho_fuel
        self.M_WTank_Fuel_slug = self.W_WTank_Fuel_lbf / 32.174

        logging.info(f'Volume of Integral Wing Tanks: {self.wtank_vol_gal:.2f} gal;   Weight of Fuel in Wing Tanks: {self.W_WTank_Fuel_lbf:.2f} lbf;   Mass of Fuel in Wing Tanks: {self.M_WTank_Fuel_slug:.2f} slugs')


    def CG_Limits(self, lower_SM: float, upper_SM: float, SM: float, xNP: float):
        self.forward_xCG = lower_SM * self.W_MAC + xNP
        self.aft_xCG = upper_SM * self.W_MAC + xNP

        logging.info(f'Forward CG Limit = {self.forward_xCG:.2f} ft')
        logging.info(f'Aft CG Limit = {self.aft_xCG:.2f} ft')

        return self.forward_xCG, self.aft_xCG


        




########################
# RUN CONTROL
########################

if __name__ == "__main__":
    config = Config(vsp_filename='F24HH_3',
                    geom_def_path=r'C:\Users\14153\Desktop\Skewl\EAE 130\Python\EAE130_aircraft_design\Flying_Surfaces\airplane_geom2.json',
                    fuse_file_path=r"C:\Users\14153\Desktop\Skewl\EAE 130\Python\EAE130_aircraft_design\VSP_Files\4_SIMPLE_F24HH_FUSE.vsp3",
                    wing_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A006_TEST.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A004_TEST.dat"],
                    tail_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A005.dat"])
    
    # Initialize and Model the Aircraft in OpenVSP, run CompGeom to get surfaces areas and volumes
    vspfile = VSP_Interface(config=config, global_x_transl=17)
    vspfile.BuildPlane(include_fuse=True)
    vspfile.Run_CompGeom()

    # Calculate CD0
    #CD0 = vspfile.calc_CD0(Mach=0.85, alt=35000)

    # Calculate Wave Drag
    #vspfile.calc_CD_wave(Mach=1.6)
    

    # Calculate Masses of surfaces based on CompGeom results and 
    mass = Weigh_Plane(manager=vspfile)
    desnities, comp_mass = mass.Mass()

    # Assigns densities to previously created VSP file
    vspfile.Assign_Mass(densities=desnities)

    # Perform VSP analyses; MassProps, VSPAERO, etc. 
    xcg, ycg, zcg, AC_mass_slug = vspfile.Run_MassProp(n_slice=150)

    print(AC_mass_slug * 32.174)
    #vspfile._initialize_NP_VSPAERO(xcg=xcg)
    
    #SM, xNP = vspfile.Run_VSPAERO_NP(xcg=xcg)

    # Calculate CG Limits
    #forward_xCG, aft_xCG = mass.CG_Limits(lower_SM=-0.15, upper_SM=0.08, SM=SM, xNP=xNP)
    
    # Dictionary to store weights information
    '''weights_CG = {
        'xCG [ft]': xcg,
        'yCG [ft]': ycg,
        'zCG [ft]': zcg,
        #"Static Margin": SM,
        #'Forward CG Limit [ft]': forward_xCG,
        #'Aft CG Limit [ft]': aft_xCG,
        'MTOW [slug]': AC_mass_slug,
    }

    pprint.pprint(weights_CG)
    pprint.pprint(comp_mass)'''

    ### Add fn. to compute Swet/Sref
    ### Add fn. to compute CD0, CD_wave