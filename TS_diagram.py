from TS_formulation import * 
from constraint_equations import *
from functools import partial
plt.figure(figsize=(10, 5))


S_guess = np.linspace(300, 600, 400)

# 7g load factor
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(load_factor, Ma=0.9, alt=0, n=7), mission='strike',
        plot_styling={'label': '7g load factor','linestyle': '-', 'color': 'tab:pink'})
# 8g load factor
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(load_factor, Ma=0.9, alt=0, n=8), mission='strike',
        plot_styling={'label': '8g load factor','linestyle': '--', 'color': 'tab:pink'})
# Ma 1.6 dash, 30k ft
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(dash, Ma=1.6, alt=30000), mission='combat',
        plot_styling={'label': 'Ma 1.6 dash, 30k ft','linestyle': '-', 'color':'tab:orange'})
#Ma 2.0 dash, 30k ft
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(dash, Ma=2.0, alt=30000), mission='combat',
        plot_styling={'label': 'Ma 2.0 dash, 30k ft','linestyle': '--', 'color':'tab:orange'})
#Ma 0.85 dash, sea level
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(dash, Ma=0.85, alt=0), mission='strike',
        plot_styling={'label': 'Ma 0.85 dash, sea level','linestyle': '-', 'color':'tab:blue'})
#Ma 0.9 dash, sea level
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(dash, Ma=0.9, alt=0), mission='strike',
        plot_styling={'label': 'Ma 0.9 dash, sea level','linestyle': '--', 'color':'tab:blue'})
# sustained turn 8 deg/sec
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(sustained_turn, Ma=0.85, alt=20000, deg=8.0), mission='combat',
        plot_styling={'label': r'sustained turn at 8.0$^\circ$/sec','linestyle': '-', 'color':'tab:green'})
# sustained turn 10 deg/sec
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(sustained_turn, Ma=0.85, alt=20000, deg=10.0), mission='combat',
        plot_styling={'label': r'sustained turn at 10.0$^\circ$/sec','linestyle': '--', 'color':'tab:green'})
# climb at 500 ft/min
TS_line(S_guess, W_guess=50000, T_0=44000,
        segment_function=partial(climb_curve, vertical_climb_rate=500, V_horizontal=135), mission='strike',
        plot_styling={'label':'climb at 500 ft/min','linestyle': '-', 'color': 'tab:gray'})

T_sweep = np.linspace(1000, 80000, 1000)
# takeoff at 160 kts
WS_line(W_guess=50000, T_0=T_sweep, mission='strike',
        segment_function=takeoff(160),
        plot_styling={'label': 'catapult takeoff at 160 kts', 'linestyle': '-', 'color': 'tab:brown'})
# approach 

# stall
V_engage = 135
V_approach = V_engage / 1.05
V_stall = V_approach / 1.10

WS_line(W_guess=50000, T_0=T_sweep, mission='strike',
        segment_function=stall(V_stall=V_stall, alt=0),
        plot_styling={'label': f'stall at {V_stall:.0f} kts', 'linestyle': '-', 'color': 'tab:red'})
# approach 
WS_line(W_guess=5000, T_0=T_sweep,
        segment_function=approach(V_stall), mission='strike',
        plot_styling={'label': f'approach at {V_approach:.0f} kts', 'linestyle': '--', 'color': 'tab:purple', 'alpha': 0.5})

plt.scatter(500, 44000, marker='*', color='navy', label='FA-18 E/F')
plt.scatter(460, 41000, marker='*', color='goldenrod', label='F-35C')


plt.xlabel('Wing Area, ft$^2$')
plt.ylabel('Thrust, lbf')
plt.title('T-S Diagram')
plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left')
plt.xlim([300, 600])
plt.ylim([5000, 1e5])
plt.tight_layout()
plt.show()

