import os
import sys
import subprocess
import dash
from dash import html, dcc, callback, Input, Output, State

# Register page with Dash multi-page plugin
dash.register_page(
    __name__,
    path="/simulator",
    name="Game Simulator",
    order=5,
    title="BAS | Simulator"
)

# Resolve project paths relative to frontend/src/pages/
PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(PAGES_DIR, "../../../"))
SIMULATOR_SCRIPT = os.path.join(PROJECT_ROOT, "simulator.py")

# Retrosheet 3-letter franchise codes supported in the database
TEAM_CODES = [
    "ANA", "ARI", "ATH", "ATL", "BAL", "BOS", "CHA", "CHN", "CIN", "CLE",
    "COL", "DET", "HOU", "KCA", "LAN", "MIA", "MIL", "MIN", "NYA", "NYN",
    "PHI", "PIT", "SDN", "SEA", "SFN", "SLN", "TBA", "TEX", "TOR", "WAS"
]

DAYS_OF_WEEK = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

# --- Theme Palette (Night Game / Stadium Scoreboard) ---
CARD_STYLE = {
    "padding": "1.5rem",
    "borderRadius": "10px",
    "backgroundColor": "#1f2429",
    "border": "1px solid #343a40",
    "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.35)",
    "color": "#f1f3f5",
}

LABEL_STYLE = {
    "fontWeight": "600",
    "display": "block",
    "marginBottom": "0.35rem",
    "color": "#dee2e6",
    "fontSize": "0.9rem",
}

DROPDOWN_STYLE = {
    "color": "#1a1a1a",  # Ensures dark text inside Dash's light dropdown menus
}

# --- UI Subcomponents ---

def render_control_panel():
    return html.Div(
        className="simulator-form card",
        style={**CARD_STYLE, "borderTop": "4px solid #c62828"},  # Baseball seam red accent
        children=[
            html.H3(
                "Matchup & Lineup Card",
                style={"marginTop": 0, "marginBottom": "1.25rem", "color": "#f8f9fa", "letterSpacing": "0.3px"}
            ),

            # Matchup Row
            html.Div(
                style={"display": "flex", "gap": "1rem", "marginBottom": "1rem"},
                children=[
                    html.Div(style={"flex": 1}, children=[
                        html.Label("Home Team", style=LABEL_STYLE),
                        dcc.Dropdown(
                            id="sim-home",
                            options=TEAM_CODES,
                            value="BOS",
                            clearable=False,
                            style=DROPDOWN_STYLE
                        ),
                    ]),
                    html.Div(style={"flex": 1}, children=[
                        html.Label("Visiting Team", style=LABEL_STYLE),
                        dcc.Dropdown(
                            id="sim-vis",
                            options=TEAM_CODES,
                            value="NYA",
                            clearable=False,
                            style=DROPDOWN_STYLE
                        ),
                    ]),
                ]
            ),

            # Scheduling Row
            html.Div(
                style={"display": "flex", "gap": "1rem", "marginBottom": "1rem"},
                children=[
                    html.Div(style={"flex": 1}, children=[
                        html.Label("Day of Week", style=LABEL_STYLE),
                        dcc.Dropdown(
                            id="sim-dow",
                            options=DAYS_OF_WEEK,
                            value="Saturday",
                            clearable=False,
                            style=DROPDOWN_STYLE
                        ),
                    ]),
                    html.Div(style={"flex": 1}, children=[
                        html.Label("First Pitch", style=LABEL_STYLE),
                        dcc.RadioItems(
                            id="sim-dn",
                            options=[
                                {"label": "Day Game", "value": "day"},
                                {"label": "Night Game", "value": "night"}
                            ],
                            value="day",
                            inline=True,
                            style={"marginTop": "0.55rem"},
                            labelStyle={"marginRight": "1.25rem", "color": "#f1f3f5", "cursor": "pointer"},
                            inputStyle={"marginRight": "0.4rem", "accentColor": "#2e7d32"}
                        ),
                    ]),
                ]
            ),

            # Stitched Divider
            html.Hr(style={"border": "none", "borderTop": "1px dashed #c62828", "opacity": "0.6", "margin": "1.35rem 0"}),

            # Weather Row
            html.H4("Ballpark Weather", style={"margin": "0 0 0.25rem 0", "color": "#f5c542", "fontSize": "1.05rem"}),
            html.Small(
                "Weather modifiers apply only when Sky, Precipitation, and Temp are all set.",
                style={"color": "#adb5bd", "display": "block", "marginBottom": "0.85rem"}
            ),
            html.Div(
                style={"display": "flex", "gap": "1rem", "marginBottom": "1.5rem"},
                children=[
                    html.Div(style={"flex": 1}, children=[
                        html.Label("Sky Condition", style={**LABEL_STYLE, "fontSize": "0.82rem"}),
                        dcc.Dropdown(
                            id="sim-sky",
                            options=["sunny", "cloudy", "overcast", "dome"],
                            placeholder="e.g. sunny",
                            style=DROPDOWN_STYLE
                        ),
                    ]),
                    html.Div(style={"flex": 1}, children=[
                        html.Label("Precipitation", style={**LABEL_STYLE, "fontSize": "0.82rem"}),
                        dcc.Dropdown(
                            id="sim-precip",
                            options=["none", "drizzle", "rain", "showers", "snow"],
                            placeholder="e.g. none",
                            style=DROPDOWN_STYLE
                        ),
                    ]),
                    html.Div(style={"flex": 1}, children=[
                        html.Label("Temp (°F)", style={**LABEL_STYLE, "fontSize": "0.82rem"}),
                        dcc.Input(
                            id="sim-temp",
                            type="number",
                            placeholder="70",
                            min=0,
                            max=120,
                            style={
                                "width": "100%",
                                "height": "36px",
                                "padding": "0 0.6rem",
                                "borderRadius": "4px",
                                "border": "1px solid #ccc",
                                "backgroundColor": "#ffffff",
                                "color": "#1a1a1a",
                            }
                        ),
                    ]),
                ]
            ),

            # Action Button (Outfield Turf Green)
            html.Button(
                "Play Ball — Run Simulation",
                id="sim-run-btn",
                n_clicks=0,
                style={
                    "width": "100%",
                    "backgroundColor": "#2e7d32",
                    "color": "#ffffff",
                    "border": "1px solid #43a047",
                    "padding": "0.7rem 1.25rem",
                    "borderRadius": "6px",
                    "cursor": "pointer",
                    "fontWeight": "700",
                    "fontSize": "1rem",
                    "letterSpacing": "0.4px",
                    "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.3)"
                }
            )
        ]
    )


def render_simulator_output():
    return html.Div(
        className="simulator-terminal card",
        style={**CARD_STYLE, "borderTop": "4px solid #2e7d32"},  # Turf green accent
        children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "1rem"},
                children=[
                    html.H3("Scoreboard Forecast", style={"margin": 0, "color": "#f8f9fa", "letterSpacing": "0.3px"}),
                    html.Span(
                        "LIVE CLI FEED",
                        style={
                            "fontSize": "0.72rem",
                            "fontWeight": "700",
                            "letterSpacing": "1px",
                            "color": "#f5c542",
                            "backgroundColor": "#121619",
                            "padding": "0.25rem 0.6rem",
                            "borderRadius": "4px",
                            "border": "1px solid #343a40"
                        }
                    )
                ]
            ),
            dcc.Loading(
                type="default",
                color="#f5c542",
                children=html.Pre(
                    id="sim-output-text",
                    style={
                        "backgroundColor": "#0f1214",
                        "color": "#4af626",
                        "border": "2px solid #2b3035",
                        "fontFamily": "Menlo, Consolas, 'Courier New', monospace",
                        "fontSize": "0.85rem",
                        "lineHeight": "1.5",
                        "padding": "1.25rem",
                        "borderRadius": "6px",
                        "whiteSpace": "pre-wrap",
                        "minHeight": "340px",
                        "maxHeight": "550px",
                        "overflowY": "auto",
                        "margin": 0,
                        "boxShadow": "inset 0 0 12px rgba(0, 0, 0, 0.7)"
                    },
                    children="Select matchup and ballpark conditions, then click 'Play Ball' to display the attendance & ticket report."
                )
            )
        ]
    )

# --- Master Layout ---

layout = html.Div(
    style={"padding": "2rem", "maxWidth": "1200px", "margin": "0 auto", "fontFamily": "system-ui, -apple-system, sans-serif"},
    children=[
        html.H1(
            "MLB Game Attendance & Ticket Pricing Simulator",
            style={"marginBottom": "0.4rem", "color": "#000000", "fontWeight": "700"}
        ),
        html.P(
            "Run parameterized game forecasts against historical Retrosheet logs and secondary ticket listings.",
            style={"color": "#000000", "marginBottom": "1.75rem", "fontSize": "1rem"}
        ),
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(420px, 1fr))",
                "gap": "1.5rem",
                "alignItems": "start"
            },
            children=[
                render_control_panel(),
                render_simulator_output()
            ]
        )
    ]
)

# --- Callback ---

@callback(
    Output("sim-output-text", "children"),
    Input("sim-run-btn", "n_clicks"),
    State("sim-home", "value"),
    State("sim-vis", "value"),
    State("sim-dow", "value"),
    State("sim-dn", "value"),
    State("sim-sky", "value"),
    State("sim-precip", "value"),
    State("sim-temp", "value"),
    prevent_initial_call=True
)
def run_simulation(n_clicks, home, vis, dow, dn, sky, precip, temp):
    # Validation: prevent identical matchups
    if home == vis:
        return "Error: Home team and visiting team cannot be the same franchise."

    if not os.path.exists(SIMULATOR_SCRIPT):
        return f"Error: simulator.py could not be found at:\n{SIMULATOR_SCRIPT}"

    # Build CLI command vector
    cmd = [
        sys.executable,
        SIMULATOR_SCRIPT,
        "--home", home,
        "--vis", vis,
        "--dow", dow,
        "--dn", dn
    ]

    # Weather: only pass flags if all 3 are provided
    if sky and precip and temp is not None:
        cmd.extend([
            "--sky", str(sky),
            "--precip", str(precip),
            "--temp", str(temp)
        ])

    try:
        # Run simulator.py with working directory at PROJECT_ROOT so SQLite DB path resolves properly
        res = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=12
        )

        if res.returncode != 0:
            return f"CLI Error (Exit Code {res.returncode}):\n\n{res.stderr or res.stdout}"

        return res.stdout if res.stdout.strip() else "Simulation completed with no output."

    except subprocess.TimeoutExpired:
        return "Error: Simulation timed out after 12 seconds."
    except Exception as exc:
        return f"System Exception during execution:\n{str(exc)}"