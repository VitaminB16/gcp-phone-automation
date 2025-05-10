from dotenv import load_dotenv

load_dotenv()

import os
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go

import dash
from dash import dcc, html, Input, Output, State, callback_context


# --- Helper Functions ---
def get_screen_dimensions():
    try:
        from screeninfo import get_monitors

        monitor = get_monitors()[0]
        # For web app, let's use a more constrained default if screeninfo fails
        # The figure height/width will be relative to the dcc.Graph component
        return monitor.height * 0.8, monitor.width * 0.9  # Example scaling
    except ImportError:
        return 700, 1000  # Adjusted for typical web view
    except Exception as e:
        print(f"Error getting screen dimensions: {e}")
        return 700, 1000


def format_datetime_for_display(dt_obj):
    if pd.isna(dt_obj):
        return "Invalid Date"
    try:
        return dt_obj.strftime("%Y %b %d %I:%M:%S%p")
    except AttributeError:
        return str(dt_obj)


def create_location_figure(df_filtered: pd.DataFrame, add_lines: bool = True):
    fig_height, fig_width = get_screen_dimensions()

    if df_filtered.empty:
        fig = go.Figure()
        fig.update_layout(
            height=fig_height,
            width=fig_width,  # Use consistent dimensions
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[
                {
                    "text": "No data to display for the selected period.",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20},
                }
            ],
        )
        return fig

    # Avoid SettingWithCopyWarning by working on a copy for modifications
    df_plot = df_filtered.copy()

    if "DisplayDate" not in df_plot.columns and "datetime_obj" in df_plot.columns:
        df_plot.loc[:, "DisplayDate"] = df_plot["datetime_obj"].apply(
            format_datetime_for_display
        )
    elif "DisplayDate" not in df_plot.columns:
        df_plot.loc[:, "DisplayDate"] = "Date N/A"

    df_plot = df_plot.assign(size=1)

    fig_point = px.scatter_mapbox(
        df_plot,
        lat="Latitude",
        lon="Longitude",
        hover_name="DisplayDate",
        zoom=10,  # Adjusted zoom, can be dynamic later
        size="size",
        size_max=8,
        height=fig_height,
        width=fig_width,
    )

    if add_lines:
        # Sort by datetime_obj to ensure lines are drawn in correct order
        df_plot_sorted_for_lines = df_plot.sort_values(by="datetime_obj")
        fig_line = px.line_mapbox(
            df_plot_sorted_for_lines,
            lat="Latitude",
            lon="Longitude",
            hover_name="DisplayDate",
            zoom=10,
            height=fig_height,
            width=fig_width,
        )
        fig = go.Figure(data=fig_point.data + fig_line.data)
        fig.update_traces(line=dict(color="rgba(50,50,50,1)"))
    else:
        fig = fig_point

    fig.update_traces(marker_opacity=1)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_traces(
        hovertemplate=(
            "<b>Date:</b> %{hovertext}<br>"
            "<b>Lat:</b> %{lat:.4f}<br>"
            "<b>Lon:</b> %{lon:.4f}<br>"
            "<extra></extra>"
        )
    )
    return fig


# --- Dash App ---
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Location Tracker"

DEFAULT_DEVICE_ID = os.environ.get("FOLLOWMEE_DEVICE_ID", "YOUR_DEFAULT_DEVICE_ID_HERE")
CSV_FILE_PATH = f"output/location_export_{DEFAULT_DEVICE_ID}.csv"

initial_today_str = date.today().isoformat()  # YYYY-MM-DD format

app.layout = html.Div(
    [
        dcc.Store(
            id="current-target-date-store", data=initial_today_str
        ),  # Stores YYYY-MM-DD string
        html.H1("Device Location History"),
        html.Div(
            [
                html.Label(
                    "Filter Mode:",
                    style={"font-weight": "bold", "margin-right": "10px"},
                ),
                dcc.RadioItems(
                    id="filter-mode-radio",
                    options=[
                        {"label": "Single Day", "value": "single_day"},
                        {"label": "All History", "value": "all_history"},
                        {"label": "Custom Range", "value": "custom_range"},
                    ],
                    value="single_day",
                    labelStyle={"display": "inline-block", "margin-right": "15px"},
                ),
            ],
            style={"padding": "10px 0px"},
        ),
        html.Div(
            id="date-controls-wrapper",
            children=[
                # Controls for Single Day View
                html.Div(
                    id="single-day-controls-div",
                    children=[
                        html.Button(
                            "◀ Previous Day",
                            id="prev-day-button",
                            n_clicks=0,
                            style={"margin-right": "5px"},
                        ),
                        dcc.DatePickerSingle(
                            id="single-date-picker",
                            date=initial_today_str,
                            display_format="YYYY-MM-DD",
                            min_date_allowed=date(2000, 1, 1),  # Sensible min
                            max_date_allowed=date.today()
                            + timedelta(days=365),  # Sensible max
                            style={
                                "margin-right": "5px",
                                "width": "150px",
                                "text-align": "center",
                            },
                        ),
                        html.Button("Next Day ▶", id="next-day-button", n_clicks=0),
                    ],
                    style={
                        "padding": "10px 0",
                        "display": "flex",
                        "align-items": "center",
                    },
                ),
                # Controls for Custom Range View
                html.Div(
                    id="custom-range-controls-div",
                    children=[
                        dcc.DatePickerRange(
                            id="custom-date-range-picker",
                            min_date_allowed=date(2000, 1, 1),
                            max_date_allowed=date.today() + timedelta(days=1),
                            initial_visible_month=date.today(),
                            start_date=(date.today() - timedelta(days=7)),
                            end_date=date.today(),
                            display_format="YYYY-MM-DD",
                        )
                    ],
                    style={"padding": "10px 0", "display": "none"},
                ),  # Initially hidden
            ],
        ),
        dcc.Loading(
            id="loading-map", type="circle", children=dcc.Graph(id="location-map-graph")
        ),
        html.Div(id="data-info", style={"padding": "10px", "font-style": "italic"}),
    ],
    style={"padding": "20px"},
)


# Callback to update visibility of control groups
@app.callback(
    [
        Output("single-day-controls-div", "style"),
        Output("custom-range-controls-div", "style"),
    ],
    [Input("filter-mode-radio", "value")],
)
def toggle_control_visibility(selected_mode):
    single_day_style = {"padding": "10px 0", "display": "flex", "align-items": "center"}
    custom_range_style = {
        "padding": "10px 0",
        "display": "block",
    }  # Or 'flex' if needed

    if selected_mode == "single_day":
        return single_day_style, {**custom_range_style, "display": "none"}
    elif selected_mode == "custom_range":
        return {**single_day_style, "display": "none"}, custom_range_style
    else:  # 'all_history'
        return {**single_day_style, "display": "none"}, {
            **custom_range_style,
            "display": "none",
        }


# Callback to update the current target date (dcc.Store) and sync DatePickerSingle
@app.callback(
    [Output("current-target-date-store", "data"), Output("single-date-picker", "date")],
    [
        Input("prev-day-button", "n_clicks"),
        Input("next-day-button", "n_clicks"),
        Input("single-date-picker", "date"),
    ],  # Input from DatePickerSingle
    [State("current-target-date-store", "data")],  # Current date from store
    prevent_initial_call=True,
)
def update_target_date_store(
    prev_clicks, next_clicks, picked_date_str, current_stored_date_str
):
    triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]

    # Use current_stored_date_str as the source of truth if buttons are clicked
    # If DatePickerSingle is changed, picked_date_str is the new truth

    if triggered_id == "single-date-picker":
        if picked_date_str:
            new_date_obj = datetime.strptime(picked_date_str, "%Y-%m-%d").date()
        else:  # DatePicker cleared, revert to stored or handle as error/default
            new_date_obj = datetime.strptime(current_stored_date_str, "%Y-%m-%d").date()
    else:  # A button was clicked
        current_date_obj = datetime.strptime(current_stored_date_str, "%Y-%m-%d").date()
        if triggered_id == "prev-day-button":
            new_date_obj = current_date_obj - timedelta(days=1)
        elif triggered_id == "next-day-button":
            new_date_obj = current_date_obj + timedelta(days=1)
        else:  # Should not happen
            new_date_obj = current_date_obj

    new_date_iso_str = new_date_obj.isoformat()
    return new_date_iso_str, new_date_iso_str  # Update store and DatePickerSingle


# Main callback to update the map and data info
@app.callback(
    [Output("location-map-graph", "figure"), Output("data-info", "children")],
    [
        Input("filter-mode-radio", "value"),
        Input("current-target-date-store", "data"),
        Input("custom-date-range-picker", "start_date"),
        Input("custom-date-range-picker", "end_date"),
    ],
)
def update_map(
    filter_mode, target_date_store_str, custom_start_date_str, custom_end_date_str
):
    try:
        df_full = pd.read_csv(CSV_FILE_PATH)
    except FileNotFoundError:
        error_fig = go.Figure()
        fig_height, fig_width = get_screen_dimensions()
        error_fig.update_layout(
            height=fig_height,
            width=fig_width,
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[
                {
                    "text": f"Error: CSV file not found at {CSV_FILE_PATH}",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 16},
                }
            ],
        )
        return error_fig, f"Error: Could not load data for device {DEFAULT_DEVICE_ID}."

    if df_full.empty:
        return (
            create_location_figure(
                pd.DataFrame(columns=["Latitude", "Longitude", "datetime_obj"])
            ),
            "No data in CSV file.",
        )

    # Convert 'Date' column to datetime objects.
    # Original 'Date' is ISO format e.g., "2024-07-02T09:08:10+01:00"
    # pd.to_datetime handles this well, creating timezone-aware objects if offset is present.
    df_full["datetime_obj"] = pd.to_datetime(df_full["Date"], errors="coerce")
    df_full.dropna(
        subset=["datetime_obj"], inplace=True
    )  # Remove rows where date conversion failed

    if df_full.empty:  # Check after attempting conversion and dropping NaT
        return (
            create_location_figure(
                pd.DataFrame(columns=["Latitude", "Longitude", "datetime_obj"])
            ),
            "No valid date entries found in CSV.",
        )

    # Create a 'date_only' column for date-based filtering.
    # .dt.date gives the date part based on the datetime_obj's local time (if timezone-aware).
    df_full["date_only"] = df_full["datetime_obj"]
    # Convert timestamp to date only
    df_full["date_only"] = df_full["date_only"].apply(
        lambda x: x.date() if isinstance(x, datetime) else pd.NaT
    )

    df_filtered = pd.DataFrame(columns=df_full.columns)
    time_range_info = "No data selected."

    if filter_mode == "single_day":
        if not target_date_store_str:
            return create_location_figure(df_filtered), "Please select a date."
        target_date_obj = datetime.strptime(target_date_store_str, "%Y-%m-%d").date()
        df_filtered = df_full[df_full["date_only"] == target_date_obj]
        time_range_info = (
            f"Showing data for {target_date_obj.strftime('%A, %B %d, %Y')}."
        )

    elif filter_mode == "all_history":
        df_filtered = df_full.copy()  # Use all data
        if not df_filtered.empty:
            min_date_disp = (
                df_filtered["datetime_obj"].min().strftime("%Y-%m-%d %H:%M:%S")
            )
            max_date_disp = (
                df_filtered["datetime_obj"].max().strftime("%Y-%m-%d %H:%M:%S")
            )
            time_range_info = (
                f"Showing all data from {min_date_disp} to {max_date_disp}."
            )
        else:
            time_range_info = "Showing all data (none available)."

    elif filter_mode == "custom_range":
        if not custom_start_date_str or not custom_end_date_str:
            return (
                create_location_figure(df_filtered),
                "Please select a start and end date for the custom range.",
            )

        custom_start_date_obj = datetime.strptime(
            custom_start_date_str, "%Y-%m-%d"
        ).date()
        custom_end_date_obj = datetime.strptime(custom_end_date_str, "%Y-%m-%d").date()

        df_filtered = df_full[
            (df_full["date_only"] >= custom_start_date_obj)
            & (df_full["date_only"] <= custom_end_date_obj)  # Inclusive range
        ]
        time_range_info = (
            f"Showing data from {custom_start_date_obj.strftime('%Y-%m-%d')} "
            f"to {custom_end_date_obj.strftime('%Y-%m-%d')}."
        )

    # The 'DisplayDate' column for hover tooltips is now created inside create_location_figure
    # if it doesn't exist, operating on the df_filtered.

    fig = create_location_figure(df_filtered, add_lines=True)
    num_points = len(df_filtered)
    info_text = f"Displaying {num_points} location points. {time_range_info}"

    return fig, info_text


if __name__ == "__main__":
    if DEFAULT_DEVICE_ID == "YOUR_DEFAULT_DEVICE_ID_HERE":
        print(
            "Warning: FOLLOWMEE_DEVICE_ID environment variable is not set or is using the placeholder."
        )
        print("Please set it in your .env file or environment.")
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Warning: The CSV file '{CSV_FILE_PATH}' does not exist.")
        print("Make sure the file is present and the device ID is correct.")
    app.run(debug=True)
