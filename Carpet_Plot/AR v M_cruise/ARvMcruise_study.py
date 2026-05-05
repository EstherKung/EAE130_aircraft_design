from pathlib import Path
import numpy as np
from pprint import pprint
import plotly.graph_objects as go
import shutil
import time
import random
import multiprocessing
from dask import delayed, compute
import os

# get cwd
cwd = r'Carpet_Plot\AR v M_cruise\resdump'

# Global Variables
#AR = 3.5
#M_cruise = 0.85

def sweep(AR, M_cruise, run_id):
    # Stagger so parallel doesn't die
    time.sleep(random.uniform(0, 3))

    # Define file name
    fname=f'F24HH_AR_{AR}_Mcrs_{M_cruise}'

    # Create directory for each run
    run_dir = Path(__file__).resolve().parent / f"temp_run_{run_id}"
    run_dir.mkdir(exist_ok=True)

    # move each worker process into isolated folder
    original_cwd = os.getcwd()
    os.chdir(run_dir)

    try:
        # import
        from Carpet_Plot import vspwrap
        from Flying_Surfaces import surf_def as sdef
        from Initial_Weight_Est import weight
        
        # Generate json
        geom_def = sdef.define_plane(AR=AR, LE_swp=35, lam_w=0.27, save_dir=run_dir, fname=fname)

        # Calculate initial weights 
        W0, W_empty, W_fuel, W_dg, W_fuse_empty = weight.weight_convergence(S = {'wing': 465, 'htail': geom_def['hstab']['S_HT'], 'vtail': geom_def['vstab']['S_VT'], 'fuse_wet': 678.915,}, 
                                        AR=AR, M_cruise=M_cruise, Swet_Sref=3.911, 
                                        mission='strike')

        # Model in OpenVSP, return weights and drags
        W_fsurf, W_wing_fuel, CD0, CD_wave = vspwrap.runVSP(W_dg=W_dg, M_cruise=M_cruise, get_CD0=True, geom_def=geom_def, save_dir=run_dir, fname=fname)
        
        # Drop Tank Weight (6773.946 = internal fuel tanks)
        W_dtank = W_fuel - 6773.946 - W_wing_fuel

        # Weight from components (7080 = strike payload)
        W0_compo = W_fuse_empty + W_fsurf + W_wing_fuel + 6773.946 + W_dtank + 7080

        # weight dict
        wdict = {
            'W0': W0,
            'W_empty': W_empty,
            'W_fuel': W_fuel,
            'W_dg': W_dg,
            'W_fuse_empty': W_fuse_empty,
            'W_fsurf': W_fsurf,
            'W_wing_fuel': W_wing_fuel,
            'W_dtank': W_dtank
        }
        #pprint(wdict)

        print(f'MTOW: {W0:.2f} lbs | CD0: {CD0:.5f} | Drop Tank Reqs: {W_dtank:.2f} lbs | Compo MTOW: {W0_compo:.2f} lbs')

    finally:
        # move back into original dir
        os.chdir(original_cwd)

        # Clean up created directories
        shutil.rmtree(run_dir, ignore_errors=True)

    return CD0, W0_compo


if __name__=="__main__":
    # Sweep thru range of AR, see results
    AR_range = np.linspace(3.0, 4.5, 7)
    Mc_range = np.linspace(0.75, 0.95, 7)

    # Initialize 2D array to hold results (rows for AR, columns for M_cruise)
    W0_arr = np.zeros((len(AR_range), len(Mc_range)))
    CD0_arr = np.zeros((len(AR_range), len(Mc_range)))

    # Create a list to hold 'delayed' tasks (dask)
    delayed_tasks = []

    for i, ARi in enumerate(AR_range):
        for j, Mj in enumerate(Mc_range):
            # Create ID for each run
            run_id = f'AR_{ARi:.2f}_M_{Mj:.2f}'

            #Wrap sweep in dask delayed function
            task = delayed(sweep)(AR=ARi, M_cruise=Mj, run_id=run_id)
            delayed_tasks.append((i, j, task))

    # Extract just task objects for computation
    tasks = [t[2] for t in delayed_tasks]

    # Use dask to perform paralell computation
    safe_cores = min(6, multiprocessing.cpu_count() - 1) # Don't use all cores
    print(f'Computing {len(tasks)} in parallel...')
    results = compute(*tasks, scheduler='processes', num_workers=safe_cores)

    # Unpack results for plotting
    for idx, (i, j, _) in enumerate(delayed_tasks):
        CD0_arr[i, j], W0_arr[i, j] = results[idx]

    # plot
    fig = go.Figure()

    # define plot boundaries for efficient labeling
    ar_line_labels = [f"M={M:.2f}" if (k == 0 or k == len(Mc_range)-1) else "" for k, M in enumerate(Mc_range)]
    m_line_labels = [f"AR={AR:.2f}" if (k == 0 or k == len(AR_range)-1) else "" for k, AR in enumerate(AR_range)]

    # Plot constant AR
    for i, AR in enumerate(AR_range):
        fig.add_trace(go.Scatter(
            x=W0_arr[i, :],
            y=CD0_arr[i, :],
            mode='lines+markers+text',
            text=ar_line_labels,
            textposition="top center",
            name='Constant AR', 
            legendgroup='AR',
            showlegend=(i == 0),
            line=dict(color='blue')
        ))

    # Plot constant M_cruise
    for j, M in enumerate(Mc_range):
        fig.add_trace(go.Scatter(
            x = W0_arr[:, j],
            y=CD0_arr[:, j],
            mode='lines+markers+text',
            text=m_line_labels,
            textposition="bottom right",
            name='Constant M_cruise',
            legendgroup='Mcruise',
            showlegend=(j == 0),
            line=dict(color='red')
        ))

    fig.update_layout(
        title = 'Carpet Plot: Effect of AR & M_cruise on W0, CD0',
        xaxis_title = 'MTOW [lbs]',
        yaxis_title = 'CD0',
        legend_title = 'Sweep Variables'
    )

    # Export Figure
    fig.write_image(
        "ARvM_carpet2.pdf",
        width=900,
        height=600,
        scale=2)

    fig.show()