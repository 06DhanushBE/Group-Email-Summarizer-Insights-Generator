import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="UCIC Email Insights",
)
server = app.server

from app_config import DASH_DEBUG, DASH_PORT
from callbacks import register_callbacks
from pages import dashboard_page, knowledge_page, tasks_page

app.pages = {
    "dashboard": dashboard_page,
    "tasks": tasks_page,
    "knowledge": knowledge_page,
}

sidebar = dbc.Col(
    [
        html.Div(
            [
                html.Div("UCIC", className="brand-kicker"),
                html.H4("Email Insights", className="brand-title"),
                html.P(
                    "Warm, story-driven analysis of threads, tasks, and graph knowledge.",
                    className="brand-subtitle",
                ),
            ],
            className="brand-block",
        ),
        html.Label("Data Source", className="section-label"),
        dcc.RadioItems(
            id="mode-toggle",
            options=[
                {"label": " Demo (synthetic)", "value": "demo"},
                {"label": " Live (Supabase)", "value": "live"},
            ],
            value="demo",
            labelStyle={"display": "block", "marginBottom": "6px"},
            className="theme-radio mb-4",
        ),
        html.Label("Department", className="section-label"),
        dcc.Dropdown(id="department-filter", placeholder="All departments", className="theme-dropdown mb-4"),
        dbc.Nav(
            [
                dbc.NavLink("Dashboard", href="/", active="exact"),
                dbc.NavLink("Tasks", href="/tasks", active="exact"),
                dbc.NavLink("Knowledge Repository", href="/knowledge", active="exact"),
            ],
            vertical=True,
            pills=False,
            className="nav-stack",
        ),
        html.Div(className="sidebar-footnote", children="Switch the mode to compare demo versus live graph data."),
    ],
    width=3,
    className="app-sidebar",
)

content = dbc.Col(id="page-content", width=9, className="app-content")

app.layout = dbc.Container(
    [
        dcc.Location(id="url"),
        dcc.Store(id="data-store"),
        dcc.Store(id="mode-store"),
        dbc.Row([sidebar, content], className="g-0 app-shell"),
    ],
    fluid=True,
)

register_callbacks(app)


if __name__ == "__main__":
    app.run(debug=DASH_DEBUG, port=DASH_PORT)