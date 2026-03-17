# %%
from TS_formulation import * 
from constraint_equations import *
from functools import partial
plt.figure(figsize=(15, 10))


S_guess = np.linspace(300, 600, 400)
# %%
# # 7g load factor
# TS_line(S_guess, W_guess=50000, T_0=44000, 
#         segment_function=partial(load_factor, Ma=0.9, alt=0, n=7), mission='strike',
#         plot_styling={'label': '7g load factor','linestyle': '-', 'color': 'tab:pink'},
#         fill=True)
# # 8g load factor
# TS_line(S_guess, W_guess=50000, T_0=44000, 
#         segment_function=partial(load_factor, Ma=0.9, alt=0, n=8), mission='strike',
#         plot_styling={'label': '8g load factor','linestyle': '--', 'color': 'tab:pink', 'alpha': 0.5})
# Ma 1.6 dash, 30k ft
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(dash, Ma=1.6, alt=30000), mission='combat',
        plot_styling={'label': 'Ma 1.6 dash, 30k ft','linestyle': '-', 'color':'tab:orange'},
        fill=True)
#Ma 2.0 dash, 30k ft
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(dash, Ma=2.0, alt=30000), mission='combat',
        plot_styling={'label': 'Ma 2.0 dash, 30k ft','linestyle': '--', 'color':'tab:orange', 'alpha':0.5})
#Ma 0.85 dash, sea level
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(dash, Ma=0.85, alt=0), mission='strike',
        plot_styling={'label': 'Ma 0.85 dash, sea level','linestyle': '-', 'color':'tab:blue'},
        fill=True)
#Ma 0.9 dash, sea level
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(dash, Ma=0.9, alt=0), mission='strike',
        plot_styling={'label': 'Ma 0.9 dash, sea level','linestyle': '--', 'color':'tab:blue', 'alpha': 0.5})
# sustained turn 8 deg/sec
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(sustained_turn, Ma=0.85, alt=20000, deg=8.0), mission='combat',
        plot_styling={'label': r'sustained turn at 8.0$^\circ$/sec','linestyle': '-', 'color':'tab:green'},
        fill=True)
# sustained turn 10 deg/sec
TS_line(S_guess, W_guess=50000, T_0=44000, 
        segment_function=partial(sustained_turn, Ma=0.85, alt=20000, deg=10.0), mission='combat',
        plot_styling={'label': r'sustained turn at 10.0$^\circ$/sec','linestyle': '--', 'color':'tab:green', 'alpha':0.5})
# climb at 500 ft/min
# TS_line(S_guess, W_guess=50000, T_0=44000,
#         segment_function=partial(climb_curve, vertical_climb_rate=500, V_horizontal=135), mission='strike',
#         plot_styling={'label':'climb at 500 ft/min','linestyle': '-', 'color': 'tab:gray'},
#         fill=True)

T_sweep = np.linspace(1000, 80000, 400)


TS_line(S_guess, W_guess=50000, T_0=44000,
        segment_function=partial(service_ceiling, RoC=500), mission='strike',
        plot_styling={'label': "service ceiling 50k ft, 500 ft/min", 'linestyle':'-', 'color': 'tab:gray'},
        fill=True)

# stall
V_engage = 140.0
V_approach = V_engage / 1.05
V_stall = V_approach / 1.10

WS_line(W_guess=50000, T_0=T_sweep, mission='strike',
        segment_function=stall(V_stall=V_stall, alt=0),
        plot_styling={'label': f'stall at {V_stall:.0f} kts', 'linestyle': '-', 'color': 'tab:red'})

# takeoff at 160 kts
V_end = 160.0

WS_line(W_guess=50000, T_0=T_sweep, mission='strike',
        segment_function=takeoff(V_end), 
        weight_fraction=partial(weight_fraction, fuel_fraction=0),
        unloaded_weight=0,
        plot_styling={'label': f'catapult takeoff at {V_end:.0f} kts', 'linestyle': '-', 'color': 'tab:brown', },
        fill=True)

WS_line(W_guess=50000, T_0=T_sweep, mission='strike',
        segment_function=takeoff(V_end-5), 
        weight_fraction=partial(weight_fraction, fuel_fraction=0),
        unloaded_weight=0,
        plot_styling={'label': f'catapult takeoff at {V_end-5:.0f} kts', 'linestyle': '--', 'color': 'tab:brown','alpha':0.6},
        fill=False)

WS_line(W_guess=50000, T_0=T_sweep, mission='strike',
        segment_function=takeoff(V_end-10), 
        weight_fraction=partial(weight_fraction, fuel_fraction=0),
        unloaded_weight=0,
        plot_styling={'label': f'catapult takeoff at {V_end-10:.0f} kts', 'linestyle': '--', 'color': 'tab:brown','alpha':0.4},
        fill=False)


WS_line(W_guess=50000, T_0=T_sweep, mission='strike',
        segment_function=takeoff(V_end-15), 
        weight_fraction=partial(weight_fraction, fuel_fraction=0),
        unloaded_weight=0,
        plot_styling={'label': f'catapult takeoff at {V_end-15:.0f} kts', 'linestyle': '--', 'color': 'tab:brown','alpha':0.2},
        fill=False)


# instantaneous load factor, usable (7g)
WS_line(W_guess=50000, T_0=T_sweep,
        segment_function=instant_load_factor(Ma=0.90, alt=20000, n=7), mission='strike',
        weight_fraction=partial(weight_fraction, fuel_fraction=0),
                plot_styling={'label': '7g load factor','linestyle': '-', 'color': 'tab:pink'}, fill=False)

#instantaneous load factor, usable (8g)
WS_line(W_guess=50000, T_0=T_sweep,
        segment_function=instant_load_factor(Ma=0.90, alt=20000, n=8), mission='strike',
        weight_fraction=partial(weight_fraction, fuel_fraction=0),
                plot_styling={'label': '8g load factor','linestyle': '--', 'color': 'tab:pink', 'alpha':0.5}, fill=False)
# approach 
# WS_line(W_guess=5000, T_0=T_sweep,
#         segment_function=approach(V_stall), mission='strike',
#         plot_styling={'label': f'approach at {V_approach:.0f} kts', 'linestyle': '--', 'color': 'tab:purple', 'alpha': 0.5})

chosen_point = {'s': [465, 465], 't':[29160,  17800]}
text_spacer = 5
### Plot Comparable Aircrafts
plt.scatter(500, 44000, marker='*', color='goldenrod') # F/A-18 E/F
plt.scatter(460, 43000, marker='*', color='navy') # F-35C
plt.scatter(492, 34000, marker='*', color='firebrick') # Dassault Rafale
plt.scatter(530, 35690, marker='*', color='olivedrab') # F-4 
# plt.scatter(551, 40400, marker='*', color='cadetblue') # Eurofighter Typhoon
plt.annotate("F/A-18 E/F", (500+text_spacer, 44000), fontsize=12, color='goldenrod') #F/A-18 E/F
plt.annotate("F-35C", (460+text_spacer, 43000), fontsize=12, color='navy') # F-35C
plt.annotate("Rafale", (492+text_spacer, 34000), fontsize=12, color='firebrick') # Dassault Rafale
plt.annotate("F-4", (530+text_spacer, 35690), fontsize=12, color='olivedrab') # F-4
# plt.annotate("Eurofighter", (551+text_spacer, 40400), fontsize=10, color='cadetblue') # Eurofighter 


plt.scatter(chosen_point['s'][0], chosen_point['t'][0], marker='*', color='slategray', label=f'chosen point (a/b, {chosen_point['t'][0]} lbf thrust)')
plt.scatter(chosen_point['s'][1], chosen_point['t'][1], marker='*', color='slategray', alpha=0.5, label=f'chosen point (dry, {chosen_point['t'][1]} lbf thrust)')
W_chosen, _, _ = weight_convergence(50000, T_0 = chosen_point['t'][0], 
                                    S={'wing': chosen_point['s'][0], 'htail': 78.41, 'vtail': 78.41, 'fuse_wet': 529.81}, 
                                    mission='strike')
# W_chosen2, _, _ = weight_convergence(50000, T_0 = chosen_point['t'][1], 
#                                     S={'wing': chosen_point['s'][1], 'htail': 78.41, 'vtail': 78.41, 'fuse_wet': 529.81}, 
#                                     mission='strike')
plt.annotate(f"MTOW:\n{W_chosen:.0f} lbs", (chosen_point['s'][0]-10, chosen_point['t'][0]-4500), fontsize=12, color='slategray')
# plt.annotate(f"MTOW: {W_chosen2:.0f} lbs", (chosen_point['s'][1], chosen_point['t'][1]-4000), fontsize=10, color='slategray')
# %%
plt.xlabel('Wing Area, ft$^2$', fontsize=16)
plt.ylabel('Thrust, lbf', fontsize=16)
plt.title('T-S Diagram', fontsize=20)
plt.legend(bbox_to_anchor=(0.5, -0.1), loc='upper center', ncols=4, fontsize=14)
plt.xlim([300, 600])
plt.xticks(fontsize=14)
plt.ylim([5000, 50000])
plt.yticks(fontsize=14)
plt.tight_layout()


plt.savefig("TS_diagram.pdf")
plt.show()
# %%
