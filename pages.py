from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc


def dashboard_page():
    return html.Div(
        [
            html.Div(
                [
                    html.Div("Email thread intelligence", className="page-kicker"),
                    html.H1("Dashboard", className="page-title"),
                    html.P(
                        "A warm, editorial view of threads, tasks, and topics across the UCIC workspace.",
                        className="page-lead",
                    ),
                    dbc.Badge("Data Updated: live from selected source", className="header-badge"),
                ],
                className="page-hero",
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Card(id="kpi-open-tasks", body=True, className="metric-card"), width=3),
                    dbc.Col(dbc.Card(id="kpi-overdue-tasks", body=True, className="metric-card"), width=3),
                    dbc.Col(dbc.Card(id="kpi-active-threads", body=True, className="metric-card"), width=3),
                    dbc.Col(dbc.Card(id="kpi-total-emails", body=True, className="metric-card"), width=3),
                ],
                className="mb-4 g-3",
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Card(dcc.Graph(id="chart-tasks-by-owner", className="chart-surface"), className="panel-card"), width=6),
                    dbc.Col(dbc.Card(dcc.Graph(id="chart-priority-breakdown", className="chart-surface"), className="panel-card"), width=6),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Card(dcc.Graph(id="chart-active-topics", className="chart-surface"), className="panel-card"), width=6),
                    dbc.Col(dbc.Card(dcc.Graph(id="chart-volume-trend", className="chart-surface"), className="panel-card"), width=6),
                ],
                className="mb-4",
            ),
        ]
    )


def tasks_page():
    return html.Div(
        [
            html.Div(
                [
                    html.Div("Operational view", className="page-kicker"),
                    html.H1("Tasks", className="page-title"),
                    html.P("Track action items from the extracted thread tasks.", className="page-lead"),
                ],
                className="page-hero",
            ),
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.Div("Task filters", className="panel-title"),
                            dbc.RadioItems(
                                id="task-status-filter",
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "Open", "value": "open"},
                                    {"label": "Overdue", "value": "overdue"},
                                ],
                                value="all",
                                inline=True,
                                className="theme-radio mb-3",
                            ),
                        ]
                    )
                ],
                className="panel-card mb-4",
            ),
            dbc.Card(
                html.Div(
                    dash_table.DataTable(
                        id="tasks-table",
                        columns=[
                            {"name": "Task", "id": "task"},
                            {"name": "Owner", "id": "owner"},
                            {"name": "Due Date", "id": "due_date"},
                            {"name": "Status", "id": "status"},
                            {"name": "Thread ID", "id": "thread_id"},
                        ],
                        page_size=15,
                        sort_action="native",
                        filter_action="native",
                        style_table={"overflowX": "auto", "width": "100%"},
                        style_cell={
                            "textAlign": "left",
                            "padding": "12px 14px",
                            "whiteSpace": "normal",
                            "height": "auto",
                            "fontFamily": 'Inter, "Segoe UI", sans-serif',
                        },
                        style_header={
                            "textAlign": "left",
                            "padding": "12px 14px",
                            "fontFamily": '"Libre Baskerville", Georgia, serif',
                            "fontWeight": "700",
                        },
                        style_filter={"textAlign": "left"},
                    ),
                    className="theme-table",
                ),
                className="panel-card",
            ),
        ]
    )


def knowledge_page():
    return html.Div(
        [
            html.Div(
                [
                    html.Div("Graph assistant", className="page-kicker"),
                    html.H1("Knowledge Repository", className="page-title"),
                    html.P(
                        "Ask about bottlenecks, decisions, and lessons learned across threads.",
                        className="page-lead",
                    ),
                ],
                className="page-hero",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Ask the graph", className="panel-title"),
                        dbc.InputGroup(
                            [
                                dbc.Input(id="kr-query", placeholder="e.g. What bottlenecks came up with GreenSprout?", className="query-input"),
                                dbc.Button("Ask", id="kr-submit", className="query-button"),
                            ],
                            className="mb-3",
                        ),
                        dcc.Loading(html.Div(id="kr-answer", className="mt-3 answer-surface")),
                    ]
                ),
                className="panel-card",
            ),
        ]
    )