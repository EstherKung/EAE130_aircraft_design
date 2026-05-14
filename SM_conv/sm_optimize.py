'''
Optimize a given aircraft's wing and hstab placement to hit the design static margin at minimum weight
'''
from sm_convergence import SM_Iteration as smit

import numpy as np
from scipy.optimize import minimize


### Caching system ###
cache = {}
worker_pool = None

def run_plane(x):
    '''
    Evaluate the SM_iteration function & cache results for a given input vector to save computation time

    Args: 
        x (list): Input vector, in this case, [X_wing, L_HT/L_fuse, c_HT]

    Returns:
        cache[key]: Stores the four outputs of SM_Iteration for a given input vector
    '''
    key = (round(x[0], 6), round(x[1], 6), round(x[2], 6))  # Round to prevent floating point misses 

    if key not in cache:
        # unpack input vector
        X_wing, L_HT_f, c_HT = x
        print(f'Evaluating X_wing = {X_wing:.3f}, L_HT/L_fuse = {L_HT_f:.3f}, c_HT = {c_HT:.3f}')

        # Call SM_Iteration
        global worker_pool
        SM, stabl_defl, x_end_hstab, fs_weight_lbf, alpha, dCmdq = smit(X_wing=X_wing, L_HT_f=L_HT_f, c_HT=c_HT, pool=worker_pool)

        # Save to cache
        cache[key] = (SM, stabl_defl, x_end_hstab, fs_weight_lbf, alpha, dCmdq)

    return cache[key]


### Objective Function ###
def objective(x):
    SM, stabl_defl, x_end_hstab, fs_weight_lbf, _, _ = run_plane(x)
    return fs_weight_lbf / 1000


# Constraint Functions
def cons_sm_lwr(x):
    SM, _, _, _, _, _ = run_plane(x)
    return SM - (-0.06)

def cons_sm_upr(x):
    SM, _, _, _, _, _ = run_plane(x)
    return (-0.04) - SM

def cons_stabl(x):
    _, stabl_defl, _, _, _, _ = run_plane(x)
    return 20 - stabl_defl 

def cons_len_plane(x):
    _, _, x_end_hstab, _, _, _ = run_plane(x)
    return 49.5 - x_end_hstab

def cons_AOA(x):
    _, _, _, _, alpha, _ = run_plane(x)
    return 13 - alpha

def cons_Cmq(x):
    _, _, _, _, _, dCmdq = run_plane(x)
    return -3 - dCmdq


# Optimization Run
if __name__=='__main__':
    import multiprocessing as mp

    # Initial Guess
    x0 = [18.0, 0.29, 0.3]

    # Bounds for X_wing, L_HT/L_fuse, c_HT
    bounds = [(16, 20), (0.25, 0.35), (0.25, 0.40)]

    # Constraints
    constr = [
        {'type': 'ineq', 'fun': cons_sm_lwr},
        {'type': 'ineq', 'fun': cons_sm_upr},
        {'type': 'ineq', 'fun': cons_stabl},
        {'type': 'ineq', 'fun': cons_len_plane},
        {'type': 'ineq', 'fun': cons_AOA},
        {'type': 'ineq', 'fun': cons_Cmq}
    ] 

    print('Starting Optimizer...')

    worker_pool = mp.Pool(processes=1, maxtasksperchild=15)

    # Run Scipy SLSQP
    result = minimize(
        objective,
        x0,
        method='SLSQP',
        bounds=bounds,
        constraints=constr,
        options={'disp':True, 'eps':[1e-3, 1e-4, 1e-4], 'maxiter': 200} # 'maxiter': 200
    )

    worker_pool.close()
    worker_pool.join()

    print('Optimization Complete')

    if result.success:
        print('Success: Found Feasable Minimum')
    else:
        print(f'Failed - {result.message}')

    # access results
    print(f'X_wing: {result.x[0]:.4f} ft')
    print(f'L_HT/L_fuse: {result.x[1]:.4f}')
    print(f'c_HT: {result.x[2]:.4f}')

    # Final state of aircraft
    SM_f, stabl_f, len_f, wfsurf_f, alpha_f, dCmq_f = run_plane(result.x)
    print(f'SM: {SM_f:.4f} | Stabl. Defl.: {stabl_f:.2f} deg | AC Len: {len_f:.2f} ft | Weight Fsurf: {wfsurf_f:.2f} lbf | AOA: {alpha_f:.2f} deg | dCm/dq: {dCmq_f:.3f}')