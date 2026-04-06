import plotly.graph_objects as go
import numpy as np

# Define the 4 corners of a trapezoid (x, y, z)
# Example: Base on z=0, narrower top
x = [0,
             np.float64(-14.12398621061597),
             np.float64(-19.02496127794102),
             np.float64(-18.151759508611303), 
    -18.151759508611303, -19.02496127794102, 0]
y = [0, -20.17, -20.171, 0, 20.171, 20.171, 0]
z = [0, 0, 0, 0, 0, 0, 0]

# Define two triangles to form the quadrilateral (0,1,2 and 0,2,3)
fig = go.Figure(data=[
    go.Mesh3d(
        x=x, y=y, z=z,
        i=[0, 0], # Indices of first vertex of each triangle
        j=[1, 2], # Indices of second vertex
        k=[2, 3], # Indices of third vertex
        color='blue',
        opacity=0.5
    )
])




fig.show()