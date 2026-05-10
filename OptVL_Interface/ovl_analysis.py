'''
General interface to the OptVL to perform aerodynamic analyses
'''
from optvl import OVLSolver
from pprint import pprint

ovl = OVLSolver(r'SM_conv\F24HH_SM.avl')
ovl.set_constraint("stabilator", "Cm", 0.00)
ovl.execute_run()

force_data = ovl.get_total_forces()



class ovl_analysis:
    def __init__(self, avlfile: str):
        '''
        General class for handling analysis, inputs/outputs

        Args:
            avlfile(str): path to .avl file
        '''

        # Create the aircraft object in ovl
        self.ovl = OVLSolver(geo_file=avlfile)


    def SM(self, Mach: float, cref: float, xcg: float, CL: float):
        '''
        Calculates the (longitudinally) trimmed static margin at a given flight speed
        
        Args:
            Mach (float): Mach number of the flight condition
            cref (float): Reference chord; MAC
            xcg (float): x CG reference point
            CL (float): CL of the aircraft in trim

        Returns:
            SM (float): Static margin for trimmed flight state
            stabl_defl (float): Stabilator deflection at flight state
        '''
        # Trim aircraft (elevator, PM = 0) at flight mach, run analysis
        self.ovl.set_parameter('Mach', Mach)
        self.ovl.set_constraint("stabilator", "Cm", 0.00)
        self.ovl.execute_run()

        # Access results
        self.stab_deriv = self.ovl.get_stab_derivs()
        xnp = self.stab_deriv['neutral point']

        stabl_defl = self.ovl.get_control_deflection('stabilator')

        # Calculate SM
        SM = (xnp - xcg) / cref

        print(f'Static Margin: {SM:.4f}, Elevator Deflection: {stabl_defl:.2f} degrees')
        
        return SM, stabl_defl



if __name__=='__main__':
    ovlplane = ovl_analysis('SM_conv\F24HH_SM.avl')
    ovlplane.SM(Mach=0.2, cref=12.7958, xcg = 27.7943, CL=1.77)