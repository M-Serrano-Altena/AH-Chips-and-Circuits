import plotly.graph_objects as go

# Define the coordinates for the line
x = [0, 1, 2, 3, 4]
y = [0, 1, 2, 3, 4]
z = [0, 1, 2, 3, 4]

# Create the 3D line plot
fig = go.Figure(data=[go.Scatter3d(
    x=x,
    y=y,
    z=z,
    mode='lines',  # Use 'lines' for a connected line
    line=dict(
        color='blue',
        width=3
    )
)])

# Update layout for better appearance
fig.update_layout(
    scene=dict(
        xaxis_title='X Axis',
        yaxis_title='Y Axis',
        zaxis_title='Z Axis'
    ),
    title="3D Line Plot"
)

# Show the plot
fig.show()
