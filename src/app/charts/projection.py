import plotly.graph_objects as go

from app.services.simulation_service import SimulationResult

_GROSS_COLOR = "#6b7280"
_CTO_COLOR = "#dc2626"
_PEA_COLOR = "#2563eb"
_AV_COLOR = "#16a34a"


def build(result: SimulationResult) -> str:
    years = [s.year for s in result.snapshots]
    gross = [s.gross_value for s in result.snapshots]
    cto = [s.cto_net for s in result.snapshots]
    pea = [s.pea_net for s in result.snapshots]
    av = [s.av_net for s in result.snapshots]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years, y=gross, name="Brut (sans frais ni impôts)",
        line={"color": _GROSS_COLOR, "dash": "dot", "width": 1.5},
    ))
    fig.add_trace(go.Scatter(
        x=years, y=cto, name="CTO net",
        line={"color": _CTO_COLOR, "width": 2},
    ))
    fig.add_trace(go.Scatter(
        x=years, y=pea, name="PEA net",
        line={"color": _PEA_COLOR, "width": 2},
    ))
    fig.add_trace(go.Scatter(
        x=years, y=av, name="AV net",
        line={"color": _AV_COLOR, "width": 2},
    ))

    fig.update_layout(
        title=f"Projection sur {len(years)} ans — CAGR historique {result.cagr:.1f}%",
        xaxis_title="Année",
        yaxis_title="Valeur du portefeuille (€)",
        height=420,
        margin={"l": 10, "r": 10, "t": 50, "b": 40},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        font={"family": "system-ui, sans-serif", "size": 12},
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", tickformat=",.0f", ticksuffix=" €")

    return fig.to_html(full_html=False, include_plotlyjs=False)
