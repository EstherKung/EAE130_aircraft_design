'''
Optimize a given aircraft's wing and hstab placement to hit the design static margin at minimum weight
'''
from sm_convergence import SM_Iteration as smit

import numpy as np
from scipy.optimize import minimize


### Caching system ###
cache = {}

def run_plane(x):
    '''
    Evaluate the SM_iteration function & cache results for a given input vector to save computation time

    Args: 
        x (list): Input vector, in this case, [X_wing, L_HT/L_fuse]

    Returns:
        cache[key]: Stores the four outputs of SM_Iteration for a given input vector
    '''
    key = (round(x[0], 4), round(x[1], 4))  # Round to prevent floating point misses 

    if key not in cache:
        # unpack input vector
        X_wing, L_HT_f = x
        print(f'Evaluating X_wing = {X_wing:.3f}, L_HT/L_fuse = {L_HT_f:.3f}')

        # Call SM_Iteration
        SM, stabl_defl, x_end_hstab, fs_weight_lbf = smit(X_wing=X_wing, L_HT_f=L_HT_f)

        # Save to cache
        cache[key] = (SM, stabl_defl, x_end_hstab, fs_weight_lbf)

    return cache[key]


### Objective Function ###




