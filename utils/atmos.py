import ussa1976 
from pint import UnitRegistry
import numpy as np

def atmos(h: float):
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