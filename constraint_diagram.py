from constraint_equations import *


WL_range = np.linspace(0.01, 500, 1000) # bound for plots, adjust if needed

# %%
V_engage = 140

V_approach = V_engage / 1.05

V_stall = V_approach / 1.10

# %%
plt.figure(figsize=(10, 5))


# climb_curve(WL=WL_range, vertical_climb_rate=500, V_horizontal=135, 
#             plot_styling={'linestyle': '-', 'color': 'tab:gray'})

# service_ceiling(WL=WL_range, RoC=500,
#                 plot_styling={'linestyle': '-', 'color':'tab:gray'})
dash(WL=WL_range, Ma=1.6, alt=30000, 
     plot_styling={'linestyle': '-', 'color':'tab:orange'})
dash(WL=WL_range, Ma=2.0, alt=30000, 
     plot_styling={'linestyle': '--', 'color': 'tab:orange', 'alpha': 0.5}, fill=False)
dash(WL=WL_range, Ma=0.85, alt=0, 
     plot_styling={'linestyle': '-','color':'tab:blue'})
dash(WL=WL_range, Ma=0.90, alt=0, 
     plot_styling={'linestyle': '--','color':'tab:blue', 'alpha': 0.5}, fill=False)

# load_factor(WL=WL_range, Ma=0.9, alt=20000, n=7, 
#             plot_styling={'linestyle': '-', 'color': 'tab:pink'})
# load_factor(WL=WL_range, Ma=0.9, alt=20000, n=8, 
#             plot_styling={'linestyle': '--', 'color': 'tab:pink', 'alpha':0.5}, fill=False)
instant_load_factor(Ma=0.9, alt=20000, n=7,
                     plot_styling={'linestyle': '-', 'color': 'tab:purple'})
instant_load_factor(Ma=0.9, alt=20000, n=8,
                     plot_styling={'linestyle': '--', 'color': 'tab:purple', 'alpha':0.5})
sustained_turn(WL=WL_range, Ma=0.85, alt=20000, deg=8.0, 
               plot_styling={'linestyle': '-', 'color': 'tab:green'})
sustained_turn(WL=WL_range, Ma=0.85, alt=20000, deg=10.0, 
               plot_styling={'linestyle': '--', 'color': 'tab:green', 'alpha':0.5}, fill=False)


takeoff(160,
        plot_styling={'linestyle': '-', 'color': 'tab:brown'})
takeoff(155,
        plot_styling={'linestyle': '--', 'color': 'tab:brown', 'alpha':0.8}, fill=False)
takeoff(150,
        plot_styling={'linestyle': '--', 'color': 'tab:brown', 'alpha':0.6}, fill=False)
takeoff(145,
        plot_styling={'linestyle': '--', 'color': 'tab:brown', 'alpha': 0.4},fill=False)
stall(V_stall, 0,
      plot_styling={'linestyle': '-', 'color': 'tab:red'})



# %% 
plt.ylim([0, 2])
plt.xlim([0, 170])
plt.xlabel('Wing Loading (lb/ft$^2$)', fontsize=16)
plt.ylabel('Thrust-to-Weight Ratio (lbf/lb)', fontsize=16)
plt.scatter(94, 0.93, marker='*', c='cadetblue', s=80, label='F/A 18 E/F')
plt.scatter(107.7, 0.75, marker='*', c='navy', s=80, label='F 35-C', zorder=100)
plt.scatter(54000/492, 34000/54000, marker='*', c='firebrick', s=80, label='Rafale', zorder=100)
plt.scatter(61795/530, 35690/61795, marker='*', c='olivedrab', s=80, label='F-4', zorder=100)
# plt.scatter(90, 0.75, marker='*', c='goldenrod', s=80, label='Chosen Design Point', zorder=100)
plt.scatter(80.34, 0.58, marker='*', c='goldenrod', s=80, label='Chosen Design Point', zorder=100)
plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left')

plt.tight_layout()
plt.title("Constraint Diagram", fontsize=16)
# plt.show()
plt.savefig('constraint_diagram.pdf')