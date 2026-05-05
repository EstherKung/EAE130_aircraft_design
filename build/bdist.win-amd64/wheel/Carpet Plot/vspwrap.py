from Surface_to_VSP import surf_to_VSP as vspa
from pathlib import Path


def runVSP(W_dg: float = 42449, M_cruise: float = 0.85, M_dash: float = 1.6, get_CD0: bool = False, get_CD_wave: bool = False,
           geom_def: str = r'C:\Users\14153\Desktop\Skewl\EAE 130\Python\EAE130_aircraft_design\Flying_Surfaces\airplane_geom2.json',
           save_dir: str = None, fname = 'test'):
    '''
    wraps the surf_to_VSP script for easy manipulation

    Args:
        W_dg (float): Design Gross Weight empty + 50% fuel
        M_cruise (float): Cruise mach number
        M_dash (float): Dash mach number
        get_CD0 (bool): If true, run a Parasite Drag Analysis
        get_CD_wave (bool): If true, run a wave drag analysis
        geom_def (str): path to airplane_geom.json

    Returns:
        W_fsurf (float): Weight of wings and tail, lbf
        W_fuel_wings (float): Weight, in lbf, of fuel stored in wing tanks
        CD0 (float): Parasite Drag Coefficient
        CD_wave (float): Wave Drag Coefficient
    '''
    # Configure VSPInterface
    config = vspa.Config(vsp_filename=fname,
                        W_dg=W_dg,
                        geom_def_path=geom_def,
                        fuse_file_path=r"C:\Users\14153\Desktop\Skewl\EAE 130\Python\EAE130_aircraft_design\VSP_Files\4_SIMPLE_F24HH_FUSE.vsp3",
                        wing_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A006_TEST.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A005.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 64A004_TEST.dat"],
                        tail_foils=[r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A004.dat", r"C:\Users\14153\Desktop\Airfoil Library\NACA 65A005.dat"])

    # Build Aircraft
    vspfile = vspa.VSP_Interface(config=config, global_x_transl=17, save_dir=save_dir)
    vspfile.BuildPlane(include_fuse=True)
    vspfile.Run_CompGeom()

    # Run Parasite Drag if desired
    CD0 = 0 # default CD0 value
    if get_CD0 == True:
        CD0 = vspfile.calc_CD0(Mach=M_cruise, alt=35000)
    else:
        print('No Parasite Drag Analysis')

    # Run Wave Drag if desired
    CD_wave = 0 # default CD_wave value
    if get_CD_wave == True:
        CD_wave = vspfile.calc_CD_wave(Mach=M_dash)
    else:
        print('No Wave Drag Analysis')

    # Calculate Mass
    mass = vspa.Weigh_Plane(manager=vspfile)
    desnities, comp_mass = mass.Mass()

    ### ACCESS RESULTS
    W_fuel_wings = comp_mass.loc['Wing Fuel Tanks', 'Weight [lbf]']

    print(mass.tot_surf_weight, W_fuel_wings, CD0, CD_wave)

    return mass.tot_surf_weight, W_fuel_wings, CD0, CD_wave
    

if __name__ == "__main__":
    wrap_dir = Path(__file__).resolve().parent
    runVSP(get_CD0=True, get_CD_wave=False, save_dir=wrap_dir)

