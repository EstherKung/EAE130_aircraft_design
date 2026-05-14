'''
General interface to the OptVL to perform aerodynamic analyses
'''
from optvl import OVLSolver
from pprint import pprint

'''ovl = OVLSolver(r'SM_conv\F24HH_SM.avl')
ovl.set_constraint("stabilator", "Cm", 0.00)
ovl.execute_run()

force_data = ovl.get_total_forces()

'''

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
        Calculates the (longitudinally) trimmed static margin at landing and cruise conditions
        
        Args:
            Mach (float): Mach number of the flight condition
            cref (float): Reference chord; MAC
            xcg (float): x CG reference point
            CL (float): CL of the aircraft in trim

        Returns:
            SM (float): Static margin for trimmed flight state
            stabl_defl (float): Stabilator deflection at flight state
            alpha (float): aircraft AOA at trimmed state


        '''
        # Trim aircraft in landing configuration
        self.ovl.set_parameter('Mach', Mach)
        self.ovl.set_control_deflection('flap', 45.0)
        self.ovl.set_control_deflection('slat', 15.0)
        self.ovl.set_constraint("stabilator", "Cm", 0.00)
        self.ovl.set_constraint("alpha", "CL", CL)
        self.ovl.execute_run()

        # Access results
        # Normal stability derivatives
        self.stab_deriv = self.ovl.get_stab_derivs()
        xnp = self.stab_deriv['neutral point']
        dCM_dalfa = self.stab_deriv['dCm/dalpha']   # long. static stab. deriv
        dCN_dbeta = self.stab_deriv["dCn'/dbeta"]   # directional static stab. deriv
        dCl_dbeta = self.stab_deriv["dCl'/dbeta"]   # lateral static stab deriv
        dCM_dq = self.stab_deriv["dCm/dq'"]         # pitch damping derivative
        dCl_dp = self.stab_deriv["dCl'/dp'"]        # roll damping 
        dCn_dr = self.stab_deriv["dCn'/dr'"]        # yaw damping

        #pprint(self.stab_deriv)

        # Control surface stability derivatives (control powers)
        self.cntl_deriv = self.ovl.get_control_stab_derivs()
        dCm_dstabl = self.cntl_deriv['dCm/dstabilator'] # elevator (stabilator) control power

        #pprint(self.cntl_deriv)


        alpha = self.ovl.get_variable('alpha')

        print(f'Landing Stability Derivatives: dCM/dAlpha = {dCM_dalfa:.4f} | dCN/dBeta = {dCN_dbeta:.4f} | dCl/dBeta = {dCl_dbeta:.4f} | dCM/dq = {dCM_dq:.4f} | dCl/dp = {dCl_dp:.4f} | dCn/dr = {dCn_dr:.4f} | dCM/de = {dCm_dstabl:.4f}')

        stabl_defl = self.ovl.get_control_deflection('stabilator')

        # Calculate SM
        SM = (xnp - xcg) / cref

        print(f'Landing State: Static Margin = {SM:.4f} | Elevator Deflection = {stabl_defl:.2f} deg | AOA =  {alpha:.2f} deg')
        
        return SM, stabl_defl, alpha, dCM_dq
    

    def _stab_land(self):
        pass


    def _stab_crs(self, Mach: float, cref: float, xcg: float, CL: float):
        '''
        Calculate aircraft parameters in trimmed cruise flight

        Args: 
            CL_crs (float): Required CL in cruise

        Returns:
            SM_crs (float): static margin in cruise 
            stabl_crs (float): stabilator deflection for trimmed cruise
            alpha_crs (float): aircraft aoa in trimmed cruise

        '''
        # Set up run
        self.ovl.set_parameter('Mach', Mach)
        self.ovl.set_control_deflection('flap', 0)
        self.ovl.set_control_deflection('slat', 0)
        self.ovl.set_constraint("stabilator", "Cm", 0.00)
        self.ovl.set_constraint("alpha", "CL", CL)
        self.ovl.execute_run()

        # Get stability derivatives
        self.stab_deriv = self.ovl.get_stab_derivs()
        xnp = self.stab_deriv['neutral point']
        dCM_dalfa = self.stab_deriv['dCm/dalpha']   # long. static stab. deriv
        dCN_dbeta = self.stab_deriv["dCn'/dbeta"]   # directional static stab. deriv
        dCl_dbeta = self.stab_deriv["dCl'/dbeta"]   # lateral static stab deriv
        dCM_dq = self.stab_deriv["dCm/dq'"]         # pitch damping derivative
        dCl_dp = self.stab_deriv["dCl'/dp'"]        # roll damping 
        dCn_dr = self.stab_deriv["dCn'/dr'"]        # yaw damping

        # Get control powers
        self.cntl_deriv = self.ovl.get_control_stab_derivs()
        dCm_dstabl = self.cntl_deriv['dCm/dstabilator']     # stabilator control power
        dCl_dail = self.cntl_deriv['dCl/daileron']        # aileron (roll) control power 
        dCn_dail = self.cntl_deriv['dCn/daileron']        # adverse yaw
        dCn_drud = self.cntl_deriv['dCn/drudder']         # Rudder control power

        # Get trimmed aircraft state
        alpha = self.ovl.get_variable('alpha')
        stabl_defl = self.ovl.get_control_deflection('stabilator')

        # Calcualte SM
        SM = (xnp - xcg) / cref

        # print results
        print(f'Cruise Stability Derivatives: dCm/dalpha = {dCM_dalfa:.4f} | dCn/dbeta = {dCN_dbeta:.4f} | dCl/dbeta = {dCl_dbeta:.4f} | dCM/dq = {dCM_dq:.4f} | dCl/dp = {dCl_dp:.4f} | dCn/dr = {dCn_dr:.4f}')
        print(f'Cruise Control Powers: dCm/dstabil = {dCm_dstabl:.4f} | dCl/dail = {dCl_dail:.4f} | dCn/dail = {dCn_dail:.4f} | dCn/drudder = {dCn_drud:.4f}')
        print(f'Cruise Trimmed State: Static Margin = {SM:.3f} | AOA = {alpha:.2f} deg | Stabilator Deflection = {stabl_defl:.2f} deg')




if __name__=='__main__':
    ovlplane = ovl_analysis('SM_conv\F24HH_SM.avl')
    #ovlplane = ovl_analysis('AVL_scripting\F24HH.avl')
    ovlplane.SM(Mach=0.2, cref=12.7958, xcg = 29.35, CL=1.5112)
    ovlplane._stab_crs(Mach=0.85, cref=12.7985, xcg=29.35, CL = 0.312)
