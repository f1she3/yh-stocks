from datetime import date, timedelta

import plotly.graph_objects as go
import yfinance as yf

_ACCENT = "#2563eb"


def build(symbols: list[str], years: int = 5) -> str:
    end = date.today()
    start = end - timedelta(days=years * 365)

    try:
        batch = yf.download(
            tickers=symbols,
            start=start,
            end=end,
            progress=False,
            group_by="ticker",
            timeout=30,
        )
    except Exception:
        return ""

    if batch.empty:
        return ""

    fig = go.Figure()
    colors = [_ACCENT, "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2"]

    for idx, symbol in enumerate(symbols[:10]):  # cap at 10 lines for readability
        try:
            sym_df = batch[symbol] if len(symbols) > 1 else batch
            close = sym_df["Close"].dropna()
            if close.empty:
                continue
            # Normalize to 100 so multiple stocks are comparable
            normalized = close / close.iloc[0] * 100
            fig.add_trace(go.Scatter(
                x=normalized.index,
                y=normalized.values,
                name=symbol,
                line={"color": colors[idx % len(colors)], "width": 1.5},
            ))
        except (KeyError, IndexError):
            continue

    if not fig.data:
        return ""

    fig.update_layout(
        title=f"Historique des cours sur {years} ans (base 100)",
        xaxis_title="Date",
        yaxis_title="Indice (base 100)",
        height=360,
        margin={"l": 10, "r": 10, "t": 50, "b": 40},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        font={"family": "system-ui, sans-serif", "size": 12},
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

    return fig.to_html(full_html=False, include_plotlyjs=False)
