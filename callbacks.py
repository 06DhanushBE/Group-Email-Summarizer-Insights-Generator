from datetime import date

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

from data_access import load_data
from graph_access import get_qa_chain


def _filter_dept(df, dept):
    if dept and not df.empty and "department" in df.columns:
        return df[df["department"] == dept]
    return df


def register_callbacks(app):
    @app.callback(
        Output("data-store", "data"),
        Output("mode-store", "data"),
        Output("department-filter", "options"),
        Input("mode-toggle", "value"),
    )
    def refresh_data(mode):
        emails, tasks = load_data(mode)
        departments = sorted(emails["department"].dropna().unique().tolist()) if not emails.empty else []
        dept_options = [{"label": d, "value": d} for d in departments]
        return (
            {"emails": emails.to_dict("records"), "tasks": tasks.to_dict("records")},
            mode,
            dept_options,
        )

    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def route(pathname):
        if pathname == "/tasks":
            return app.pages["tasks"]()
        if pathname == "/knowledge":
            return app.pages["knowledge"]()
        return app.pages["dashboard"]()

    @app.callback(
        Output("kpi-open-tasks", "children"),
        Output("kpi-overdue-tasks", "children"),
        Output("kpi-active-threads", "children"),
        Output("kpi-total-emails", "children"),
        Output("chart-tasks-by-owner", "figure"),
        Output("chart-priority-breakdown", "figure"),
        Output("chart-active-topics", "figure"),
        Output("chart-volume-trend", "figure"),
        Input("data-store", "data"),
        Input("department-filter", "value"),
    )
    def update_dashboard(data, dept):
        if not data:
            raise dash.exceptions.PreventUpdate

        emails = pd.DataFrame(data["emails"])
        tasks = pd.DataFrame(data["tasks"])

        if not emails.empty:
            emails["sent_timestamp"] = pd.to_datetime(emails["sent_timestamp"])
        emails = _filter_dept(emails, dept)

        if dept and not tasks.empty and not emails.empty:
            thread_ids_in_dept = emails["thread_id"].unique()
            tasks = tasks[tasks["thread_id"].isin(thread_ids_in_dept)]

        today_str = date.today().isoformat()

        open_tasks = tasks[tasks["status"] == "open"] if not tasks.empty else tasks
        overdue_tasks = (
            open_tasks[open_tasks["due_date"].notna() & (open_tasks["due_date"] < today_str)]
            if not open_tasks.empty
            else open_tasks
        )
        active_threads = emails["thread_id"].nunique() if not emails.empty else 0
        total_emails = len(emails)

        def kpi_card(title, value, color="primary"):
            return [
                html.Div(str(value), className=f"metric-value metric-{color}"),
                html.Div(title, className="metric-label"),
            ]

        kpi1 = kpi_card("Open Tasks", len(open_tasks))
        kpi2 = kpi_card("Overdue Tasks", len(overdue_tasks), color="danger")
        kpi3 = kpi_card("Active Threads", active_threads)
        kpi4 = kpi_card("Total Emails", total_emails)

        if not tasks.empty and tasks["owner"].notna().any():
            owner_counts = tasks["owner"].fillna("Unassigned").value_counts().reset_index()
            owner_counts.columns = ["owner", "count"]
            fig_owner = px.bar(owner_counts, x="owner", y="count", title="Tasks by Owner", template="plotly_white")
        else:
            fig_owner = px.bar(title="Tasks by Owner (no data)", template="plotly_white")

        if not emails.empty and "priority" in emails.columns:
            prio_counts = emails.drop_duplicates("thread_id")["priority"].value_counts().reset_index()
            prio_counts.columns = ["priority", "count"]
            fig_priority = px.pie(prio_counts, names="priority", values="count", title="Priority Breakdown", template="plotly_white")
        else:
            fig_priority = px.pie(title="Priority Breakdown (no data)", template="plotly_white")

        if not emails.empty and "client_project_or_topic" in emails.columns:
            topic_series = (
                emails["client_project_or_topic"]
                .replace("", pd.NA)
                .replace("None", pd.NA)
                .dropna()
            )
            topic_counts = topic_series.value_counts().head(10).reset_index()
            topic_counts.columns = ["topic", "count"]
            fig_topics = px.bar(
                topic_counts, x="count", y="topic", orientation="h",
                title="Active Discussion Topics", template="plotly_white",
            )
        else:
            fig_topics = px.bar(title="Active Discussion Topics (no data)", template="plotly_white")

        if not emails.empty:
            vol = emails.copy()
            vol["date"] = vol["sent_timestamp"].dt.date
            vol_counts = vol.groupby("date").size().reset_index(name="emails")
            fig_volume = px.line(vol_counts, x="date", y="emails", title="Conversation Volume Trend", template="plotly_white")
        else:
            fig_volume = px.line(title="Conversation Volume Trend (no data)", template="plotly_white")

        chart_colorway = ["#ff6b35", "#d9843b", "#d4a373", "#f4a261", "#8d5a2b", "#e76f51"]

        for fig in [fig_owner, fig_priority, fig_topics, fig_volume]:
            fig.update_layout(
                paper_bgcolor="#f7ecd8",
                plot_bgcolor="#fff8ee",
                font={"family": "Georgia, serif", "color": "#4c2b1a"},
                title={"font": {"family": "Georgia, serif", "size": 18, "color": "#4c2b1a"}},
                colorway=chart_colorway,
                margin={"l": 30, "r": 20, "t": 50, "b": 30},
            )
            fig.update_xaxes(gridcolor="#e8d5bc", zerolinecolor="#e8d5bc")
            fig.update_yaxes(gridcolor="#e8d5bc", zerolinecolor="#e8d5bc")

        return kpi1, kpi2, kpi3, kpi4, fig_owner, fig_priority, fig_topics, fig_volume

    @app.callback(
        Output("tasks-table", "data"),
        Input("data-store", "data"),
        Input("task-status-filter", "value"),
    )
    def update_tasks_table(data, status_filter):
        if not data:
            raise dash.exceptions.PreventUpdate
        tasks = pd.DataFrame(data["tasks"])
        if tasks.empty:
            return []

        today_str = date.today().isoformat()
        if status_filter == "open":
            tasks = tasks[tasks["status"] == "open"]
        elif status_filter == "overdue":
            tasks = tasks[
                (tasks["status"] == "open")
                & tasks["due_date"].notna()
                & (tasks["due_date"] < today_str)
            ]

        return tasks.to_dict("records")

    @app.callback(
        Output("kr-answer", "children"),
        Input("kr-submit", "n_clicks"),
        State("kr-query", "value"),
        State("mode-store", "data"),
        prevent_initial_call=True,
    )
    def answer_query(n_clicks, query, mode):
        if not query:
            return dbc.Alert("Enter a question first.", color="warning")

        chain = get_qa_chain(mode or "demo")
        if chain is None:
            return dbc.Alert(
                "Knowledge repository isn't configured -- check Neo4j / Groq credentials in .env "
                "and that langchain-neo4j / langchain-groq are installed.",
                color="danger",
            )

        try:
            result = chain.invoke({"query": query})
            answer = result.get("result", str(result))
        except Exception as e:
            return dbc.Alert(f"Query failed: {e}", color="danger")

        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(f"Source: {'Live' if mode == 'live' else 'Demo'} graph", className="answer-kicker"),
                    html.P(answer),
                ]
            )
        )