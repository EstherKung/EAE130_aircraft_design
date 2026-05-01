from weight import weight_convergence
import numpy as np

for m in np.linspace(0.85, 1, 10):
    test = weight_convergence(S = {'wing': 465, 'htail': 123.10441485216471, 'vtail': 107.19521577810403, 'fuse_wet': 702.3,}, 
                            AR=3.5, M_cruise=m, Swet_Sref=4.3, 
                            mission='strike')
    print(test)