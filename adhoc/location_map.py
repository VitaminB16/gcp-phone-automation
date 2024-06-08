from dotenv import load_dotenv

load_dotenv()

import os
import pandas as pd
import plotly.express as px


def plot_location(device_id: str = None):
    device_id = device_id or os.environ["FOLLOWMEE_DEVICE_ID"]
    df = pd.read_csv(f"output/location_export_{device_id}.csv")
    df = df.assign(size=1)
    fig = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Date",
        zoom=8,
        size="size",
        size_max=8,
        height=1080,
        width=1920,
    )
    # Set the alpha value of the markers to 1
    fig.update_traces(marker_opacity=1)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()


if __name__ == "__main__":
    plot_location()
