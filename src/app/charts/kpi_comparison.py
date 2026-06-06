import plotly.graph_objects as go

from app.models.results import KpiRow

_ACCENT = "#2563eb"
_MUTED = "#93c5fd"


def build(kpi_rows: list[KpiRow], max_stocks: int = 20) -> str:
    rows = sorted(
        (r for r in kpi_rows if r.avg_roi_pct is not None),
        key=lambda r: r.avg_roi_pct or 0,
        reverse=True,
    )[:max_stocks]

    if not rows:
        return ""

    names = [r.name for r in rows]
    avg_rois = [r.avg_roi_pct for r in rows]
    avg_apys = [r.avg_apy_pct for r in rows]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="ROI moyen (%)", x=avg_rois, y=names, orientation="h", marker_color=_ACCENT))
    fig.add_trace(go.Bar(name="APY moyen (%)", x=avg_apys, y=names, orientation="h", marker_color=_MUTED))

    fig.update_layout(
        barmode="overlay",
        title="ROI et APY moyens (10 ans)",
        xaxis_title="%",
        height=max(300, len(rows) * 28),
        margin={"l": 10, "r": 10, "t": 40, "b": 30},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        font={"family": "system-ui, sans-serif", "size": 12},
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0", zeroline=True, zerolinecolor="#d1d5db")
    fig.update_yaxes(showgrid=False)

    return fig.to_html(full_html=False, include_plotlyjs=False)
