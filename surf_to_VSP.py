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
    F_w: float = 6.0       # Fuselage Width @ HStab intersection
    M: float = 1.6         # Design Max Mach Number
    rho_fuel: float = 6.65 # Density of JP-5 Fuel


########################
# VSP INTERFACE
########################

class VSP_Interface:
    # Interface to OpenVSP

    def __init__(self, config: Config, global_x_transl: float = 16.0):
        self.config = config
        self.global_x_transl = global_x_transl

        self.planefile = f'{self.config.vsp_filename}.vsp3'

        # Load json file
        with open(f"{self.config.geom_def_path}", 'r') as file:
            self.geom = json.load(file)

        # Instantiate containers for compgeom results, VSPAERO cases
        self.comp_vols = defaultdict(float)
        self.comp_wet_areas = defaultdict(float)
        self.ss_areas = {}

    def BuildPlane(self, include_fuse: bool):
        # Build complete aircraft in OpenVSP. Call to generate aircraft

        logging.info('Building Aircraft...')

        vsp.ClearVSPModel()

        # Fuselage File
        if include_fuse == True:
            vsp.InsertVSPFile(self.config.fuse_file_path, "")
            logging.info('Imported Fuselage File...')
        elif include_fuse == False:
            logging.info('Fuselage Excluded...')
        
        self._Build_Wing()
        self._Build_HStab()
        self._Build_VStab()

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
        vsp.SetParmVal(wing_id, "SectTess_U", "XSec_1", 13.0) 

        #Folding Outer Panel
        vsp.SetParmVal(wing_id, "Span", "XSec_2", b_half - y_fold)
        vsp.SetParmVal(wing_id, "Root_Chord", "XSec_2", c_mid)
        vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_2", c_tip)
        vsp.SetParmVal(wing_id, "Sweep_Location", "XSec_2", 0.0)
        vsp.SetParmVal(wing_id, "Sweep", "XSec_2", wing["swp_w"])
        vsp.SetParmVal(wing_id, "SectTess_U", "XSec_2", 9)
        vsp.SetParmVal(wing_id, 'Twist', 'XSec_2', wing['Tip_X_rot'])

        # Global Positioning 
        vsp.SetParmVal(wing_id, "X_Rel_Location", "XForm", self.global_x_transl)
        vsp.SetParmVal(wing_id, "Z_Rel_Location", "XForm", wing["Z_loc"])
        vsp.SetParmVal(wing_id, "Y_Rel_Rotation", "XForm", wing["Y_rot"])
        vsp.SetParmVal(wing_id, "X_Rel_Rotation", "XForm", wing["X_rot"])

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
        vsp.SetParmVal(hstab_id, "SectTess_U", "XSec_1", 13)
        vsp.SetParmVal(hstab_id, "X_Rel_Location", "XForm", hstab["x_loc_HT"] + self.global_x_transl)
        vsp.SetParmVal(hstab_id, "Y_Rel_Location", "XForm", hstab["Y_loc"])
        vsp.SetParmVal(hstab_id, "Z_Rel_Location", "XForm", hstab["Z_loc"])

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
        vsp.SetParmVal(vstab_id, "SectTess_U", "XSec_1", 11.0)
        vsp.SetParmVal(vstab_id, "X_Rel_Location", "XForm", vstab["x_loc_VT"] + self.global_x_transl)
        vsp.SetParmVal(vstab_id, "Y_Rel_Location", "XForm", vstab["Y_loc"])
        vsp.SetParmVal(vstab_id, "Z_Rel_Location", "XForm", vstab["Z_loc"])
        vsp.SetParmVal(vstab_id, "X_Rel_Rotation", "XForm", vstab["X_rot"])
        #vsp.SetParmVal(vstab_id, "CapBoundFlag", "Endcap", 0.0) # NEW PARMS IN VSP 3.48; DISABLE IF USING 3.47
        #vsp.SetParmVal(vstab_id, "WakeRootFlag", "Endcap", 0.0) # NEW PARMS IN VSP 3.48; DISABLE IF USING 3.47

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
        # By default, uses 100 slices. Can change for improved accuracy
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

        self.tot_mass = vsp.GetDoubleResults(mass_res_id, 'Total_Mass')

        logging.info(f'Calculated Mass Properties: Total Mass = {self.tot_mass} slugs /// XCG = {self.xCG}')


    def Run_VSPAERO_NP(self):
        # Run a steady Neutral Point analysis, return NP
        logging.info('Setting up a VSPAERO Steady Neutral Point Analysis...')

        vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)

        self._initialize_NP_VSPAERO()


        vsp.Update()
        vsp.WriteVSPFile(self.planefile)


    def _initialize_NP_VSPAERO(self):
        # Set up VSPAERO settings for steady NP analysis case
        # Should run CalcCG, and input it into initialization
        '''vsp.ClearVSPModel()
        vsp.ReadVSPFile(self.planefile)''' # Turn on for testing

        aero_id = vsp.FindContainer("VSPAEROSettings", 0)
        
        #Toggle Steady Analysis
        vsp.SetParmVal(aero_id, "UnsteadyType", "VSPAERO", 1.0)
        
        #Take Ref Area from Geom, MAC
        vsp.SetParmVal(aero_id, "RefFlag", "VSPAERO", 1.0)
        vsp.SetParmVal(aero_id, 'MACFlag', 'VSPAERO', 1.0)
        
        #Use 16 CPUs
        vsp.SetParmVal(aero_id, "NCPU", "VSPAERO", 16.0)
        
        #Init. CG Calc
        vsp.SetParmVal(aero_id, "NumMassSlice", "VSPAERO", 100.0)
        
        #Present Analysis to Set_3
        #set_index = vsp.GetSetIndex("Set_3")
        vsp.SetParmVal(aero_id, "ThinGeomSet", "VSPAERO", float(self.set_3_idx))
        
        #No VLM 
        vsp.SetParmVal(aero_id, "GeomSet", "VSPAERO", float(vsp.SET_NONE))

        logging.info('Initialized Steady NP Case...')

        # turn on for testing
        '''vsp.Update()
        vsp.WriteVSPFile(self.planefile)'''


        

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


class Weigh_Plane:
    # Class to calculate wing, hstab, vstab, and fuel tank weights/masses per Raymer's Eqns. 
    def __init__(self, manager: VSP_Interface):
        pass


########################
# RUN FILE
########################

if __name__ == "__main__":
    config = Config(vsp_filename='F24HH_2',
                    geom_def_path='airplane_geom2.json',
                    fuse_file_path=r"C:\Users\14153\Desktop\OpenVSP-3.48.2-win64\VSPFiles\2_SIMPLE_F24HH_FUSE.vsp3",
                    wing_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A006_TEST.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A004_TEST.dat"],
                    tail_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A005.dat"])
    
    vspfile = VSP_Interface(config=config)
    #vspfile.BuildPlane(include_fuse=True)
    #vspfile.Tester()
    #vspfile.Run_CompGeom()
    #vspfile.Run_VSPAERO_NP()
    #pprint.pprint(vspfile.comp_vols)