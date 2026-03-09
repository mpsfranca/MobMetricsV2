import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from  ...models import TraceModel, StayPointModel

def plot_trace_entities(file_name, max_points=5000, is_geographical=False):
    queryset = TraceModel.objects.filter(file_name=file_name).values(
        'uid', 'lng', 'lat', 'datetime'
    )

    df = pd.DataFrame.from_records(queryset)

    if df.empty:
        return "<p>No data available for this file.</p>"

    if len(df) > max_points:
        df = df.sample(n=max_points, random_state=42)

    if is_geographical:
        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lng",
            color=df["uid"].astype(str),
            hover_data=["uid", "datetime"],
            title=f"Geographical Trace Plot - {file_name}",
            zoom=10,
            height=480,
            width=480
        )
        fig.update_layout(mapbox_style="open-street-map")
    else:
        fig = px.scatter(
            df,
            x="lng",
            y="lat",
            color=df["uid"].astype(str),
            hover_data=["uid", "datetime"],
            title=f"Trace Scatter Plot - {file_name}",
            labels={"lng": "X", "lat": "Y", "uid": "Entity ID"},
            height=480,
            width=480
        )

    fig.update_layout(template="plotly_white", legend_title="Entity ID")

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def plot_trace_in_time(file_name, uid=1, is_geographical=False):
    queryset = TraceModel.objects.filter(
        file_name=file_name,
        uid=uid
    ).values("lng", "lat", "datetime")

    df = pd.DataFrame.from_records(queryset)

    if df.empty:
        return f"<p>No data available for entity {uid} in file {file_name}.</p>"

    df = df.sort_values("datetime")
    df['time'] = df['datetime'].dt.strftime("%H:%M:%S")

    if is_geographical:
        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lng",
            color="time",
            color_continuous_scale="Viridis",
            hover_data=["time"],
            title=f"Entity {uid} - Geo Trace Over Time",
            zoom=10,
            height=480,
            width=480
        )
        fig.update_layout(mapbox_style="open-street-map")
    else:
        fig = px.scatter(
            df,
            x="lng",
            y="lat",
            color="time",
            color_continuous_scale="Viridis",
            hover_data=["time"],
            title=f"Entity {uid} - Trace Over Time",
            labels={"lng": "X", "lat": "Y", "time": "Time"},
            height=480,
            width=480
        )
        fig.update_layout(
            coloraxis_colorbar=dict(title="Timestamp", tickformat=".0f")
        )

    fig.update_layout(template="plotly_white")

    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def plot_stay_points(file_name, highlight_spId=1, is_geographical=False):
    queryset = StayPointModel.objects.filter(file_name=file_name).values(
        "stay_point_id", "lng_center", "lat_center"
    )

    df_plot = pd.DataFrame.from_records(queryset)

    if df_plot.empty:
        raise ValueError("DataFrame is empty or does not contain enough points.")

    df_highlight = df_plot[df_plot["stay_point_id"] == highlight_spId]
    df_others = df_plot[df_plot["stay_point_id"] != highlight_spId]

    if is_geographical:
        fig = go.Figure()

        fig.add_trace(go.Scattermapbox(
            lat=df_others["lat_center"],
            lon=df_others["lng_center"],
            mode="markers",
            marker=dict(size=9, color="lightgray"),
            name="Other Stay Points",
            text=df_others["stay_point_id"],
            hoverinfo="text"
        ))

        fig.add_trace(go.Scattermapbox(
            lat=df_highlight["lat_center"],
            lon=df_highlight["lng_center"],
            mode="markers",
            marker=dict(size=12, color="red"),
            name=f"Stay Point {highlight_spId}",
            text=df_highlight["stay_point_id"],
            hoverinfo="text"
        ))

        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox_zoom=10,
            mapbox_center={"lat": df_plot["lat_center"].mean(), "lon": df_plot["lng_center"].mean()},
            height=480,
            width=480,
            title=f"Stay Points - Highlight spId {highlight_spId}"
        )
    else:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_others["lng_center"],
            y=df_others["lat_center"],
            mode="markers",
            marker=dict(color="lightgray", size=10),
            hovertext=df_others["stay_point_id"],
            hoverinfo="text",
            name="Other Stay Points"
        ))

        fig.add_trace(go.Scatter(
            x=df_highlight["lng_center"],
            y=df_highlight["lat_center"],
            mode="markers",
            marker=dict(color="red", size=12),
            hovertext=df_highlight["stay_point_id"],
            hoverinfo="text",
            name=f"Stay Point {highlight_spId}"
        ))

        fig.update_layout(
            width=480,
            height=480,
            template="plotly_white",
            title=f"Stay Points Scatter Plot - Highlight spId {highlight_spId}",
            xaxis=dict(title="X"),
            yaxis=dict(title="Y"),
            showlegend=False,
            font=dict(color="black")
        )

    return fig.to_html(full_html=False)
