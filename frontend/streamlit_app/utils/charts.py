from utils.styles import get_current_theme


def chart_axis(**kwargs) -> dict:
    color = get_current_theme()["text_color"]
    axis = {
        "tickfont": {"color": color, "size": 13},
        "title_font": {"color": color, "size": 14},
        "color": color,
    }
    axis.update(kwargs)
    return axis


def apply_readable_layout(fig, **kwargs):
    color = get_current_theme()["text_color"]
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": color, "size": 13},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "font": {"color": color, "size": 13},
        },
        hovermode="x unified",
        **kwargs,
    )
    return fig
