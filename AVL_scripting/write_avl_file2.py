'''
Updated version of write_avl_file.py
'''

import numpy as np
import json
import os
from dataclasses import dataclass, field
from dataclass_wizard import JSONWizard
from typing import List
from pathlib import Path
from typing import Union, Any
import pprint 

@dataclass
class AVL_Config:
    plane_name: str     # name of the avl file 
    geom_def: str | dict[str, Any]      # path to aircraft definition json OR straight json dictionary
    wing_foils: list    # list of dat files for wing airfoils (root, mid, tip)
    hstab_foils: list   # list of dat files for tail foils (root, tip)
    vstab_foils: str    # airfoil dat file for vstab

    # CG
    CG: list           # [x, y, z] location of the cg
    X_wing: float      # X position of the wing wrt nose

    # Flight Condition
    Mach: float = 0.85  # Cruise mach number


@dataclass
class CONTROL:
    # make a control surface
    name: str
    gain: float
    Xhinge: float
    #XYZhvec:  # Hinge vector is for now hardcoded in to 0 0 0
    SgnDup: float

    def make_CONTROL(self) -> str:
        return f"CONTROL\n#name   gain   Xhinge   XYZhvec   SgnDup\n{self.name}  {self.gain}   {self.Xhinge}   0. 0. 0.   {self.SgnDup}"

@dataclass
class SECTION:
    # make a single 'SECTION'
    Xle: float
    Yle: float
    Zle: float
    Chord: float
    Ainc: float 
    # Nspan & Sspace are left at default for now
    AFILE: str
    controls: List[CONTROL] = field(default_factory=list)

    def make_SECTION(self) -> str:
        sec_str = f"\nSECTION\n#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace\n{self.Xle:<7.4f}  {self.Yle:<7.4f}  {self.Zle:<7.4f}  {self.Chord:<7.4f}  {self.Ainc:<7.4f}\nAFILE\n{self.AFILE}\n"
        for cntl in self.controls:
            sec_str += cntl.make_CONTROL() + '\n'
        return sec_str

class SURFACE:
    # Generic class to create surface objects
    def __init__(self, name: str, ydupl: float, xtransl: float, Nchord: int=10, Cspace: float=1.0, Nspan: int=24, Sspace: float=1.0, Ainc: float=0):
        self.name = name
        self.ydupl = ydupl
        self.xtransl = xtransl
        self.Ainc = Ainc

        self.Nchord = Nchord
        self.Cspace = Cspace
        self.Nspan = Nspan
        self.Sspace = Sspace

        self.sections: List[SECTION] = []

    def make_SURFACE(self) -> str:
        self.surf_str = f"""
#--------------------------------------------------
SURFACE
{self.name}
!Nchordwise  Cspace  Nspanwise  Sspace
{self.Nchord:<7.1f}  {self.Cspace:<7.1f}  {self.Nspan:<7.1f}  {self.Sspace:<7.1f}

YDUPLICATE
{self.ydupl}

ANGLE
{self.Ainc}

SCALE
1.0   1.0   1.0

TRANSLATE
{self.xtransl:<7.4f}  0   0
"""
        # Attach all sections
        for sec in self.sections:
            self.surf_str += sec.make_SECTION()
        #print(self.surf_str)
        return self.surf_str
    
class Hstab(SURFACE):
    # Create a HStab surface
    def __init__(self, name: str, config: AVL_Config):
        self.config = config

        # Parse either json path, or json dict
        if isinstance(self.config.geom_def, str):
            with open(f"{self.config.geom_def}", 'r') as file:
                self.geom = json.load(file)
                #print("loaded json file")
        else:
            try: 
                self.geom = self.config.geom_def
                #print('read json dict')
            except (ValueError, TypeError, json.JSONDecodeError):
                print('Input AC def. error!')

        self.hstab = self.geom['hstab']
        self.wing = self.geom['wing']
        
        super().__init__(name, xtransl=self.wing['X_loc'], ydupl=0.0, Nspan = 12, Sspace = -1.1)
        self.hstab_afile = self.config.hstab_foils

        self._build_HSTAB()

    def _build_HSTAB(self):
        # Stabilator hinge point hardcoded to 25% c_r (approx 1/4 MAC point)
        stabilator = CONTROL(name='stabilator', gain=1.0, Xhinge=0.25, SgnDup=+1)

        for i, cseq in enumerate(self.hstab['cntl_sqs']):
            if cseq == -1:
                xsec1 = SECTION(Xle=self.hstab['xLE_pts'][i], Yle=0, Zle=self.hstab['zLE_pts'][i], Chord=self.hstab['chords'][i], Ainc=0, 
                                AFILE=self.config.hstab_foils[i])
                self.sections.append(xsec1)
            elif cseq == 0:
                xsec2 = SECTION(Xle=self.hstab['xLE_pts'][i-1], Yle=self.hstab['yLE_pts'][i-1], Zle=self.hstab['zLE_pts'][i-1], Chord=self.hstab['chords'][i-1], Ainc=0,
                                AFILE=self.config.hstab_foils[i-1], controls=[stabilator])
                self.sections.append(xsec2)

        #self.make_SURFACE()
        #print(self.surf_str)


class Vstab(SURFACE):
    # Create VStab surface
    def __init__(self, name: str,config: AVL_Config):
        self.config = config
        
        # Parse either json path, or json dict
        if isinstance(self.config.geom_def, str):
            with open(f"{self.config.geom_def}", 'r') as file:
                self.geom = json.load(file)
                #print("loaded json file")
        else:
            try: 
                self.geom = self.config.geom_def
                #print('read json dict')
            except (ValueError, TypeError, json.JSONDecodeError):
                print('Input AC def. error!')

        self.vstab = self.geom['vstab']
        self.wing = self.geom['wing']

        super().__init__(name, xtransl=self.wing['X_loc'], ydupl=0.0, Nchord=8, Nspan=14, Sspace=1.0)
        self.vstab_afile = self.config.vstab_foils

        self._build_VSTAB()

    def _build_VSTAB(self):
        rudder = CONTROL(name='rudder', gain=1.0, Xhinge=1-self.vstab['rud_c_frac'], SgnDup=-1.0)

        for i, cseq in enumerate(self.vstab['cntl_sqs']):
            if cseq == 0:
                xsec1 = SECTION(Xle=self.vstab['xLE_pts'][i], Yle=self.vstab['yLE_pts'][i], Zle=self.vstab['zLE_pts'][i], Chord=self.vstab['chords'][i],
                                AFILE=self.vstab_afile[0], Ainc=0)
                self.sections.append(xsec1)
            elif cseq == 1:
                xsec2 = SECTION(Xle=self.vstab['xLE_pts'][i], Yle=self.vstab['yLE_pts'][i], Zle=self.vstab['zLE_pts'][i], Chord=self.vstab['chords'][i],
                                AFILE=self.vstab_afile[0], controls=[rudder], Ainc=0)
                self.sections.append(xsec2)
            elif cseq == 3:
                xsec3 = SECTION(Xle=self.vstab['xLE_pts'][i], Yle=self.vstab['yLE_pts'][i], Zle=self.vstab['zLE_pts'][i], Chord=self.vstab['chords'][i],
                                AFILE=self.vstab_afile[0], controls=[rudder], Ainc=0)
                self.sections.append(xsec3)


class Wing(SURFACE):
    def __init__(self, name: str, config: AVL_Config):
        self.config = config
        self.wing_afile = self.config.wing_foils

        # Parse either json path, or json dict
        if isinstance(self.config.geom_def, str):
            with open(f"{self.config.geom_def}", 'r') as file:
                self.geom = json.load(file)
                #print("loaded json file")
        else:
            try: 
                self.geom = self.config.geom_def
                #print('read json dict')
            except (ValueError, TypeError, json.JSONDecodeError):
                print('Input AC def. error!')

        self.wing = self.geom['wing']

        super().__init__(name, ydupl=0.0, xtransl=self.wing['X_loc'], Nchord=12, Nspan=24, Sspace=1.1, Ainc=0)
        
        
        self.Ainc = self.wing['Y_rot']

        self._build_Wing()

    def _build_Wing(self):
        flap_rt = CONTROL(name='flap', gain=1.0, Xhinge=1-self.wing['flap_c_frac1'], SgnDup=1.0)
        flap_tp = CONTROL(name='flap', gain=1.0, Xhinge=1-self.wing['flap_c_frac2'], SgnDup=1.0)

        ail_rt = CONTROL(name='aileron', gain=1.0, Xhinge=1-self.wing['ail_c_frac1'], SgnDup=-1.0)
        ail_tp = CONTROL(name='aileron', gain=1.0, Xhinge=1-self.wing['ail_c_frac2'], SgnDup=-1.0)

        slat_rt = CONTROL(name='slat', gain=-1.0, Xhinge=-self.wing['slat_c_frac1'], SgnDup=1.0)
        slat_tp = CONTROL(name='slat', gain=-1.0, Xhinge=-self.wing['slat_c_frac2'], SgnDup=1.0)

        for i, cseq in enumerate(self.wing['cntl_sqs']):
            if cseq == 0:
                x1 = SECTION(Xle=self.wing['xLE_pts'][i], Yle=self.wing['yLE_pts'][i], Zle=self.wing['zLE_pts'][i], Chord=self.wing['chords'][i],
                             Ainc=0, AFILE=self.wing_afile[0])
                self.sections.append(x1)
            elif cseq == 2:
                x2 = SECTION(Xle=self.wing['xLE_pts'][i], Yle=self.wing['yLE_pts'][i], Zle=self.wing['zLE_pts'][i], Chord=self.wing['chords'][i],
                             Ainc=0, AFILE=self.wing_afile[0], controls=[slat_rt])
                self.sections.append(x2)
            elif cseq == 1:
                x3 = SECTION(Xle=self.wing['xLE_pts'][i], Yle=self.wing['yLE_pts'][i], Zle=self.wing['zLE_pts'][i], Chord=self.wing['chords'][i],
                             Ainc=0, AFILE=self.wing_afile[0], controls=[slat_rt, flap_rt])
                self.sections.append(x3)
            elif cseq == 5:
                x4 = SECTION(Xle=self.wing['xLE_pts'][i], Yle=self.wing['yLE_pts'][i], Zle=self.wing['zLE_pts'][i], Chord=self.wing['chords'][i],
                             Ainc=0, AFILE=self.wing_afile[1], controls=[slat_rt, flap_tp])
                self.sections.append(x4)
            elif cseq == 1.5:
                x5 = SECTION(Xle=self.wing['xLE_pts'][i], Yle=self.wing['yLE_pts'][i], Zle=self.wing['zLE_pts'][i], Chord=self.wing['chords'][i],
                             Ainc=0, AFILE=self.wing_afile[1], controls=[slat_rt, ail_rt])
                self.sections.append(x5)
            elif cseq == 4:
                x6 = SECTION(Xle=self.wing['xLE_pts'][i], Yle=self.wing['yLE_pts'][i], Zle=self.wing['zLE_pts'][i], Chord=self.wing['chords'][i],
                             Ainc=self.wing['Tip_X_rot'], AFILE=self.wing_afile[2], controls=[slat_tp, ail_tp])
                self.sections.append(x6)



class Write_AVL_File:
    def __init__(self, config: AVL_Config, surfaces: List[SURFACE]):
        '''
        Takes a list of surfaces, and assembles them with the preamble text to create full avl file

        Args:
            config (Config): configuration file
            surfaces (List[SURFACE]): A list of surfaces for the aircraft
        '''
        self.config = config
        self.surfaces = surfaces

        if isinstance(self.config.geom_def, str):
            with open(f"{self.config.geom_def}", 'r') as file:
                self.geom = json.load(file)
                #print("loaded json file")
        else:
            try: 
                self.geom = self.config.geom_def
                #print('read json dict')
            except (ValueError, TypeError, json.JSONDecodeError):
                print('Input AC def. error!')

        self.wing = self.geom['wing']

        self.xcg = self.config.CG[0]
        self.zcg = self.config.CG[2]

        #print(f'XCG = {self.xcg:.2f} ft')


    def Write_File(self, savedir: str = None):
        '''
        Exports the written avl file to a directory

        Args:
            savedir (str): Directory to save avl file in.  
                           By default, save in script loc (AVL_scripting/)
                           If specified, save to specified directory

        Returns:
            avlfile (str): Full raw text of the written avl file
        '''
        
        self._Preamble()
        
        for i, surf in enumerate(self.surfaces):
            self.filestr += surf.make_SURFACE()

        # Write File (if savedir = None, save in script root; if specified, save there.)
        self.avl_filename = f'{self.config.plane_name}.avl'
        if savedir == None:
            self.local_dir = Path(__file__).parent
            self.avlfile = os.path.join(self.local_dir, self.avl_filename)
        elif savedir is not None:
            self.local_dir = Path(savedir) 
            self.avlfile = self.local_dir / self.avl_filename

        with open(self.avlfile, 'w') as f:
            f.write(self.filestr)

        return self.filestr

    def _Preamble(self):
        # Write the preable section for the .avl file. Run first
        # by default, we set symmetries off. change here if desired
        self.filestr = f"""{self.config.plane_name}
        
#Mach
{self.config.Mach:.4f}
        
#IYsym   IZsym   Zsym
0        0       0.0

#Sref    Cref    Bref
{self.wing['S_w']:<7.4f}  {self.wing['c_bar']:<7.4f}  {self.wing['b_w']:<7.4f}

#Xref    Yref    Zref
{self.xcg:<7.4f}  0.0  {self.zcg:<7.4f}
        """



if __name__ == "__main__":
    config = AVL_Config(
        plane_name='F24HH_v2',
        geom_def=r'Flying_Surfaces\airplane_geom2.json',
        wing_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A006_TEST.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A004_TEST.dat"],
        hstab_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat"],
        vstab_foils= [r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat"],

        CG = [27.7943, 0, -0.1612],
        X_wing = 17.0
    )


    hstab = Hstab(name='Hstab', config=config)
    vstab = Vstab(name='Vstab', config=config)
    wing = Wing(name='Wing', config=config)

    avlfile = Write_AVL_File(config=config, surfaces=[hstab, vstab, wing], savedir='SM_conv')
    avlfile.Write_File()