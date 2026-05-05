import subprocess
import re
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from pathlib import Path
from dataclasses import dataclass
import pandas as pd
import ussa1976 
from pint import UnitRegistry
import pprint
import pandas as pd


@dataclass
class Flight_Config:
    flight_conds: dict

class AVL_Analysis:
    # general class to handle AVL analysis routines
    def __init__(self, avlexec:str, avlfile: str):
        self.avl_exec = avlexec
        self.avl_file = avlfile

        # add regex parsing here to read the avl file and return: S, X_ref, c_ref, etc.


    def Alfa(self, alfa: float, testdir: str, quiet: bool = False, slat: float = 0, flap: float = 0, Mach: float = 0.85):
        # run a single alfa setting, return CL, CDi 
        # 

        self.mach = Mach
        
        # make local directory to hold results
        self.local_dir = Path(__file__).parent

        # directory locations of results file and log file 
        self.res_dir_loc = self.local_dir / testdir
        self.log_dir_log = self.local_dir / 'ALFA_log.txt'
        
        # make directory to hold avl results
        os.makedirs(self.res_dir_loc, exist_ok=True)
        # results files
        res_file = self.res_dir_loc / f"ALFA_{alfa}_deg.dat"

        # delete existing files
        if res_file.exists():
            res_file.unlink()
            print('deleted existing file')

        rel_res_file = f"{testdir}/ALFA_{alfa}_deg_MACH_{Mach}_FLAP_{flap}_deg_SLAT_{slat}_deg.dat"

        # Instantiate subprocess, run AVL
        '''if quiet: out = None
        else: out = open(f'{self.log_dir_log}', 'w')'''

        proc = subprocess.Popen(self.avl_exec,
                                shell=False,
                                stdin=subprocess.PIPE,
                                stdout = subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=self.local_dir)

        # Text commands to pass to AVL
        # NOTE: AVL REQURES SLAT DEFLECTION TO BE NEGATIVE (FOR DROOP)
        commands = f"""load {self.avl_file}
oper
m
MN {Mach}

A A {alfa}
D3 D3 {-slat}
D4 D4 {flap}
x
ft
{rel_res_file}

quit
"""
        
        # get output
        stdout_bytes, stderr_bytes = proc.communicate(input=commands.encode('utf-8'))
        stdout_str = stdout_bytes.decode('utf-8')

        # Log File
        if not quiet:
            with open(self.log_dir_log, 'w') as f:
                f.write(stdout_str)

        # Parse results (hardcoded right now, but can change if need be)
        cl_match = re.search(r'CLtot\s*=\s*([-\d.]+)', stdout_str)
        cdi_match = re.search(r'CDff\s*=\s*([-\d.]+)', stdout_str)
        e_match = re.search(r'e\s*=\s*([-\d.]+)', stdout_str)
        
        self.Cl = float(cl_match.group(1)) if cl_match else None
        self.Cd_ind = float(cdi_match.group(1)) if cdi_match else None
        self.e = float(e_match.group(1)) if e_match else None

        #print(f"Alpha: {alfa}° | CLtot: {self.Cl} | CDtot: {self.Cd_ind} | e: {self.e}")
        
        return self.Cl, self.Cd_ind, self.e
    
    def Sweep_ALFA(self, ax: Axes, name: str, alfa_lwr: float, alfa_upr: float, steps: float, mach: float, slat: float=0, flap: float=0):
        # sweep through a series of alfa values in avl; can be modified with deflection of flaps and slats, flight condition
        # return list of Cl 
        
        # Set up values of Alpha to sweep 
        self.alfas = np.linspace(alfa_lwr, alfa_upr, steps)

        # instantiate lists to store Cl and CDi
        CL_res = []
        CDi_res = []
        e_res = []

        # loop thru alfas and store results (discard nan values)
        for alfa in self.alfas:
            CL, CDi, e = self.Alfa(alfa=alfa, testdir='Alfa_ClCdi', slat=slat, flap=flap, Mach=mach)
            if CL is not None and CDi is not None:
                CL_res.append(CL)
                CDi_res.append(CDi)
                e_res.append(e)

                print(f"Alpha: {alfa:>5.1f} | CL: {CL:>7.4f} | CDi: {CDi:>7.4f} | e: {e:>7.4f}")

        # Plot results
        ax.plot(CDi_res, CL_res, marker='o', linestyle='-', label=rf'{name}: Mach = {mach}, Flap = {flap}°, Slat = {slat}°')
        #ax.plot(self.alfas, e_res, marker='+')
        plt.xlabel('$C_{Di}$')
        plt.ylabel('$C_L$')
        plt.grid(True)
        plt.title(rf'$C_L$ v $C_{{Di}}$')
        #plt.title(rf'M = {self.mach}, Slat Deflection = {slat} deg., Flap Deflection = {flap} deg.')
        plt.legend()

        return CL_res, CDi_res
    
    def atmos(self, h: float):
        '''
        takes altitude and returns properties of air
        
        args:
            h (float): Altitude of interest, ft
        
        return:
            rho (float): Density of air, slug/ft^3
            a (float): Speed of sound, ft/s
        '''
        ureg = UnitRegistry()

        alt_ft = h * ureg.feet
        alt_m = np.array([alt_ft.to(ureg.meters).magnitude])

        ds = ussa1976.compute(z=alt_m, variables=["rho", "cs"]) # DON'T USE mu FROM USSA1976, THERE IS A BUG.

        rho_kg_m3 = ds['rho'].item() * (ureg.kg / ureg.m**3)
        a_m_s = ds['cs'].item() * (ureg.m / ureg.s)

        rho_slug_ft3 = rho_kg_m3.to(ureg.slug / ureg.ft**3).magnitude
        a_ft_s = a_m_s.to(ureg.ft / ureg.s).magnitude

        print(f'Air Density = {rho_slug_ft3:.2e} slug/ft^3,  Speed of Sound = {a_ft_s:.2f} ft/s')

        return rho_slug_ft3, a_ft_s
    

    def Trim(self, fdir:str, fcond: str, W: float, alt: float, S: float, mach: float = None, vel: float = None, quiet: bool = False, 
             flap: float = 0, slat: float = 0, stab_driver: str = 'PM'):
        '''compute elevator deflection required for trim
        
        args:
            fdir (str): Name of directory to hold results
            fcond (str): Name of the flight condition
            W (float): Weight of the aircraft, lbs
            alt (float): Altitude of flight condition, ft
            S (float): Wing planform area
            mach (float): Flight condition mach number
            OR
            vel (float): Flight condition velocity, ft/s

            flap (float): Deflection of flaps, + down
            slat (float): Deflection of slats, 
             
        returns:
            stabilator deflection (angle)
            delta cd drag
            fcond trimmed aoa'''
        
        self.trim_dir = fdir
        # Determine Flight Condition
        self.fcond_name = fcond
        self.S = S
        self.fcond_alt = alt
        self.rho, self.spd_sound = self.atmos(h=self.fcond_alt)

        # Get flight velocity depending if input
        if mach == None:
            # If velocity is given
            self.fcond_vel = vel
            self.fcond_mach = vel / self.spd_sound
        elif vel == None: 
            # If mach number is given
            self.fcond_vel = mach * self.spd_sound
            self.fcond_mach = mach
        elif mach == None and vel == None:
            print('Must provide velocity OR mach!!')
            sys.exit()
        elif mach is not None and vel is not None:
            print('Cannot provide both velocity and mach!!')
            sys.exit()
        
        # Determine Cl required for steady level flight, assume L = W
        self.fcond_CL = (2 * W) / (self.rho * self.fcond_vel**2 * self.S)

        print(f'CL required for steady level flight (L = W) in {self.fcond_name} = {self.fcond_CL:.4f}')

        
        ##### Connect with avl to run trim case #####
        # in the future, we should really have a general AVL interface function, and another function to write commands for specific analyses (ie, alpha, trim, etc.)
        
        # make local directory to hold results
        self.local_dir = Path(__file__).parent

        # directory locations of results file and log file 
        self.res_dir_loc = self.local_dir / self.trim_dir
        self.log_dir_log = self.local_dir / 'TRIM_log.txt'
        
        # make directory to hold avl results
        os.makedirs(self.res_dir_loc, exist_ok=True)
        # results files
        trim_res_name = f"TRIM_{self.fcond_name}_MACH_{self.fcond_mach:.3f}_ALT_{self.fcond_alt}ft_FLAP_{flap}_deg_SLAT_{slat}_deg.dat"
        res_file = self.res_dir_loc / trim_res_name

        # delete existing files
        if res_file.exists():
            res_file.unlink()
            print('deleted existing file')

        rel_res_file = f"{self.trim_dir}/{trim_res_name}"

        # Instantiate subprocess, run AVL

        proc = subprocess.Popen(self.avl_exec,
                                shell=False,
                                stdin=subprocess.PIPE,
                                stdout = subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=self.local_dir)

        # Text commands to pass to AVL
        commands = f"""load {self.avl_file}
oper
m
MN {self.fcond_mach} \n
A C {self.fcond_CL}
D1 {stab_driver} 0
D3 D3 {-slat}
D4 D4 {flap}
x
st
{rel_res_file}

quit
"""
        
        # get output
        stdout_bytes, stderr_bytes = proc.communicate(input=commands.encode('utf-8'))
        stdout_str = stdout_bytes.decode('utf-8')

        # Log File
        if not quiet:
            with open(self.log_dir_log, 'w') as f:
                f.write(stdout_str)

        # Parse results (hardcoded right now, but can change if need be)
        alfa_match = re.findall(r'(?i)Alpha\s*=\s*([-\d.eE+]+)', stdout_str)
        stab_match = re.findall(r'(?i)stabilator\s*=\s*([-\d.eE+]+)', stdout_str)
        cdi_match = re.findall(r'(?i)CDff\s*=\s*([-\d.eE+]+)', stdout_str)
        e_match = re.findall(r'(?i)\be\s*=\s*([-\d.eE+]+)', stdout_str)
        
        self.alfa_trim = float(alfa_match[-1]) if alfa_match else None
        self.stab_trim = float(stab_match[-1]) if stab_match else None
        self.cdi_trim = float(cdi_match[-1]) if cdi_match else None
        self.e_trim = float(e_match[-1]) if e_match else None

        # Find Xnp
        stability_filename = res_file
        try:
            with open(stability_filename, 'r') as st_file:
                st_str = st_file.read()
                
            # Run the Xnp regex against the file contents, not stdout
            xnp_match = re.findall(r"Xnp\s*=\s*([+-]?\d+\.?\d*)", st_str)
            self.xnp_trim = float(xnp_match[-1]) if xnp_match else None

        except FileNotFoundError:
            print(f"Warning: Could not find {stability_filename} to parse Xnp.")
            self.xnp_trim = None

        #print(f"Xnp: {self.xnp_trim}")

        # calculate static margin
        #hardcode in value of c_ref for now
        self.c_ref = 12.795799393235756
        self.x_ref = 27.7943

        self.fcond_SM = (self.xnp_trim - self.x_ref) / self.c_ref
        #print(f'Trimmed Static Margin is: {self.fcond_SM:.3f}')


        print(f"Aircraft Config for {self.fcond_name}: CL = {self.fcond_CL:.3f} | Mach = {self.fcond_mach:.3f} | Alpha = {self.alfa_trim}° | Stabilator Deflection = {self.stab_trim:.2f}° | SM = {self.fcond_SM:.2f} | CDind = {self.cdi_trim:.5f} | e = {self.e_trim:.3f}")

        return self.alfa_trim, self.stab_trim, self.cdi_trim
    

    def TRIM_drag(self, fcond: dict):
        '''
        Calculates trim drag of each condition using AVL_Analysis.TRIM()
        Runs AVL_Analysis.TRIM() twice, once with stabilator tied to Zero Pitching Moment, and once with it fixed at 0 deg.
        '''
        #self

        


if __name__=='__main__':
    fconds = Flight_Config(
        flight_conds= {
            'Takeoff': {
                'Altitude [ft]': 0,
                'Velocity [ft/s]': 270,
                'Mach': 0.242,
                'Flap Deflection [deg]': 30,
                'Slat Deflection [deg]': 15
            },
            'Cruise': {
                'Altitude [ft]': 30000,
                'Velocity [ft/s]': 950,
                'Mach': 0.850,
                'Flap Deflection [deg]': 0,
                'Slat Deflection [deg]': 0
            },
            'Landing': {
                'Altitude [ft]': 0,
                'Velocity [ft/s]': 224,
                'Mach': 0.202,
                'Flap Deflection [deg]': 45,
                'Slat Deflection [deg]': 15
            }
        }
    )
    '''fcond_df = pd.DataFrame.from_dict(fconds.flight_conds)
    pprint.pprint(fconds.flight_conds)
    print(fcond_df)'''

    avlexe = r'AVL_scripting\avl.exe'
    planefile = r'F24HH.avl'
    avl = AVL_Analysis(avlexec=avlexe, avlfile=planefile)
    #avl.Alfa(alfa=2, testdir='Alfa_ClCd')ß

    # takeoff = 160kts = 270.05 ft/s
    # approach = 133kts = 224.479 ft/s
    avl.Trim(fdir='TRIM', fcond='Cruise', W=50000, alt=30000, S=465, mach=0.85, flap=0, slat=0, stab_driver='PM')
    #avl.Trim(fdir='TRIM', fcond='Takeoff', W=50000, alt=0, S=465, vel=270, flap=30, slat=15, stab_driver='PM')
    #avl.Trim(fdir='TRIM', fcond='Landing', W=50000, alt=0, S=465, vel=225, flap=45, slat=15, stab_driver='PM')
    
    #testing 2
    # Cruise 3D ClMax = 0.5352
    '''fig, ax = plt.subplots()
    cruise_cl, cruise_cdi = avl.Sweep_ALFA(ax=ax, name='Cruise', alfa_lwr=-15, alfa_upr=25, steps=30, slat=0, flap=0, mach=0.85)
    TO_cl, TO_cdi = avl.Sweep_ALFA(ax=ax, name='Takeoff', alfa_lwr=-15, alfa_upr=25, steps=30, slat=15, flap=30, mach=0.242)
    land_cl, land_cdi = avl.Sweep_ALFA(ax=ax, name='Landing', alfa_lwr=-15, alfa_upr=25, steps=30, slat=15, flap=45, mach=0.202)
    plt.show()'''

    '''clcdi = {
        'Cruise_CL': cruise_cl,
        'Cruise_CDi': cruise_cdi,
        'Takeoff_CL': TO_cl,
        'Takeoff_CDi': TO_cdi,
        'Landing_CL': land_cl,
        'Landing_CDi': land_cdi
    }

    clcdi_df = pd.DataFrame(clcdi)

    print(clcdi_df)

    clcdi_df.to_csv('Prelim_Drag_Polar_Data.csv', index=False)'''



    #print(cl_res)
