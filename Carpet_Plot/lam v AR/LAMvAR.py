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

def sweep2(AR, LE_swp, run_id):
    # Stagger so parallel doesn't die
    time.sleep(random.uniform(0, 3))

    # Define file name
    fname=f'F24HH_AR_{AR}_LEs_{LE_swp}'

    # Create directory for each run
    run_dir = Path(__file__).resolve().parent / f"temp_run_{run_id}"
    run_dir.mkdir(exist_ok=True)

    # move each worker process into isolated folder
    original_cwd = os.getcwd()
    os.chdir(run_dir)

    try:
        from Carpet_Plot import vspwrap
        from Flying_Surfaces import surf_def as sdef
        from Initial_Weight_Est import weight

        # Generate json
        geom_def = sdef.define_plane(AR=AR, LE_swp=LE_swp, lam_w=0.27, save_dir=run_dir, fname=fname)

        # Calculate initial weights 
        W0, W_empty, W_fuel, W_dg, W_fuse_empty = weight.weight_convergence(S = {'wing': 465, 'htail': geom_def['hstab']['S_HT'], 'vtail': geom_def['vstab']['S_VT'], 'fuse_wet': 678.915,}, 
                                        AR=AR, M_cruise=0.85, Swet_Sref=3.911, 
                                        mission='strike')
        
        # Model in OpenVSP, return weights and drags
        W_fsurf, W_wing_fuel, CD0, CD_wave = vspwrap.runVSP(W_dg=W_dg, M_cruise=0.85, get_CD_wave=True, geom_def=geom_def, save_dir=run_dir, fname=fname)

        # Drop Tank Weight (6773.946 = internal fuel tanks)
        W_dtank = W_fuel - 6773.946 - W_wing_fuel

        # Weight from components (7080 = strike payload)
        W0_compo = W_fuse_empty + W_fsurf + W_wing_fuel + 6773.946 + W_dtank + 7080

    finally:
        # move back into original dir
        os.chdir(original_cwd)

        # Clean up created directories
        shutil.rmtree(run_dir, ignore_errors=True)

    return CD_wave, W0_compo


if __name__=='__main__':
    AR_range = np.linspace(3.0, 4.5, 7)
    LEs_range = np.linspace(35, 45, 7)

    # Rows for taper ratio, columns for le sweep
    W0_arr = np.zeros((len(AR_range), len(LEs_range)))
    CD0_arr = np.zeros((len(AR_range), len(LEs_range)))

    # Create a list to hold 'delayed' tasks (dask)
    delayed_tasks = []

    # sweep thru variables
    for i, ARi in enumerate(AR_range):
        for j, LEi in enumerate(LEs_range):
            run_id = f'AR_{ARi:.2f}_LEs_{LEi:.2f}'

            # Wrap sweep in dask delayed fn
            task = delayed(sweep2)(AR=ARi, LE_swp=LEi, run_id=run_id)
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

    fig = go.Figure()

    # define plot boundaries for efficient labeling
    # define plot boundaries for efficient labeling
    AR_line_labels = [f"AR={AR:.2f}" if (k == 0 or k == len(AR_range)-1) else "" for k, AR in enumerate(AR_range)]
    LES_line_labels = [f"LE_Swp={LEs:.1f}°" if (k == 0 or k == len(LEs_range)-1) else "" for k, LEs in enumerate(LEs_range)]

    # Plot constant Lam
    for i, AR in enumerate(AR_range):
        fig.add_trace(go.Scatter(
            x=W0_arr[i, :],
            y=CD0_arr[i, :],
            mode='lines+markers+text',
            text=LES_line_labels,
            textposition="top center",
            name='Constant AR', # Keep the name generic for the legend
            legendgroup='AR',   # Group them together
            showlegend=(i == 0),
            line=dict(color='blue')
        ))

    # Plot constant LE Swp
    for j, LEs in enumerate(LEs_range):
        fig.add_trace(go.Scatter(
            x = W0_arr[:, j],
            y=CD0_arr[:, j],
            mode='lines+markers+text',
            text=AR_line_labels,
            textposition="bottom right",
            name='Constant LE Sweep',
            legendgroup='LEs',
            showlegend=(j == 0),
            line=dict(color='red')
        ))

    fig.update_layout(
        title = 'Carpet Plot: Effect of Aspect Ratio & Leading Edge Sweep on W0, CD_wave',
        xaxis_title = 'MTOW [lbs]',
        yaxis_title = 'CD_wave',
        legend_title = 'Sweep Variables'
    )

    # Export Figure
    fig.write_image(
        "LamvLEs_carpet3.pdf",
        width=900,
        height=600,
        scale=2)

    fig.show()

        
