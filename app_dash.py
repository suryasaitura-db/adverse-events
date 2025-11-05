import os
from datetime import datetime, timedelta
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Adverse Events Registry - Postmarket Safety Surveillance"
)

server = app.server

# Databricks color scheme
COLORS = {
    'primary': '#1b3139',
    'secondary': '#ff5f46',
    'info': '#016bc1',
    'background': '#f9f7f4',
    'text': '#1b3139',
    'border': '#dce0e2',
}

# Mock data for workflow status (matching FastAPI backend)
MOCK_WORKFLOW_DATA = [
    {'name': 'Germany Data Entry', 'late': 8, 'overNormal': 8, 'normal': 0, 'total': 16, 'site': 'Germany', 'stage': 'Data Entry'},
    {'name': 'Germany Expediting Reporting', 'late': 43, 'overNormal': 49, 'normal': 0, 'total': 92, 'site': 'Germany', 'stage': 'Expediting Reporting'},
    {'name': 'Germany Medical Review', 'late': 3, 'overNormal': 3, 'normal': 0, 'total': 6, 'site': 'Germany', 'stage': 'Medical Review'},
    {'name': 'Japan Reporting', 'late': 4, 'overNormal': 4, 'normal': 0, 'total': 8, 'site': 'Japan', 'stage': 'Reporting'},
    {'name': 'Japan Validation', 'late': 2, 'overNormal': 2, 'normal': 0, 'total': 4, 'site': 'Japan', 'stage': 'Validation'},
    {'name': 'US Medical Review', 'late': 12, 'overNormal': 12, 'normal': 0, 'total': 24, 'site': 'United States', 'stage': 'Medical Review'},
    {'name': 'US Data Entry', 'late': 13, 'overNormal': 13, 'normal': 0, 'total': 26, 'site': 'United States', 'stage': 'Data Entry'},
    {'name': 'US Reporting', 'late': 23, 'overNormal': 23, 'normal': 0, 'total': 46, 'site': 'United States', 'stage': 'Reporting'},
    {'name': 'US Validation', 'late': 8, 'overNormal': 8, 'normal': 0, 'total': 16, 'site': 'United States', 'stage': 'Validation'},
]

# Mock KPI data
def get_kpi_data():
    total_late = sum(item['late'] for item in MOCK_WORKFLOW_DATA)
    total_over_normal = sum(item['overNormal'] for item in MOCK_WORKFLOW_DATA)
    total_normal = sum(item['normal'] for item in MOCK_WORKFLOW_DATA)

    return {
        'totalCases': total_late + total_over_normal + total_normal,
        'totalDrugs': 150,
        'highRiskDrugs': 12,
        'totalAdverseEvents': 3
    }

# Mock drug safety data
MOCK_DRUG_SAFETY_DATA = [
    {'drug_name': 'DrugX-500mg', 'total_events': 156, 'signal_score': 8.5, 'risk_level': 'High'},
    {'drug_name': 'VaccineY', 'total_events': 89, 'signal_score': 5.2, 'risk_level': 'Medium'},
    {'drug_name': 'DrugZ-100mg', 'total_events': 234, 'signal_score': 9.1, 'risk_level': 'High'},
    {'drug_name': 'TherapyA', 'total_events': 45, 'signal_score': 3.8, 'risk_level': 'Low'},
    {'drug_name': 'MedicationB', 'total_events': 112, 'signal_score': 6.3, 'risk_level': 'Medium'},
]

# Mock adverse events data
MOCK_ADVERSE_EVENTS = [
    {'drug_name': 'DrugX-500mg', 'adverse_event': 'Severe headache', 'event_count': 45, 'severity': 'Moderate'},
    {'drug_name': 'VaccineY', 'adverse_event': 'Injection site reaction', 'event_count': 32, 'severity': 'Mild'},
    {'drug_name': 'DrugZ-100mg', 'adverse_event': 'Allergic reaction', 'event_count': 67, 'severity': 'Severe'},
    {'drug_name': 'TherapyA', 'adverse_event': 'Nausea', 'event_count': 23, 'severity': 'Mild'},
    {'drug_name': 'MedicationB', 'adverse_event': 'Dizziness', 'event_count': 38, 'severity': 'Moderate'},
]

# Header Component
def create_header():
    return dbc.Navbar(
        dbc.Container([
            html.Div([
                html.Img(
                    src="https://www.databricks.com/en-website-assets/static/bf40f53c30ee6a1ec6e8e2b7de57b6c1/db-nav-logo.svg",
                    height="24px",
                    style={'marginRight': '16px'}
                ),
                html.H6(
                    "Postmarket Safety Surveillance",
                    style={'fontWeight': 600, 'marginRight': '16px', 'marginBottom': 0}
                ),
                html.Div([
                    html.Div(
                        "Adverse Events Registry",
                        style={'fontWeight': 500, 'lineHeight': 1.2, 'fontSize': '1rem'}
                    ),
                    html.Small(
                        "Powered by Lakebase",
                        style={'fontSize': '0.65rem', 'opacity': 0.8, 'lineHeight': 1}
                    ),
                ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], fluid=True),
        color=COLORS['primary'],
        dark=True,
        sticky="top",
        style={'boxShadow': '0px 2px 8px rgba(27, 49, 57, 0.15)'}
    )

# Sidebar Navigation
def create_sidebar():
    menu_items = [
        {'id': 'overview', 'label': 'Overview', 'icon': '📊'},
        {'id': 'drug-safety', 'label': 'Drug Safety', 'icon': '⚠️'},
        {'id': 'adverse-events', 'label': 'Adverse Events', 'icon': '📋'},
        {'id': 'aibi-dashboards', 'label': 'Databricks AI/BI Dashboards', 'icon': '📈'},
    ]

    return html.Div([
        html.Div([
            dbc.Nav([
                dbc.NavLink(
                    [
                        html.Span(item['icon'], style={'marginRight': '10px', 'minWidth': '40px'}),
                        html.Span(item['label']),
                    ],
                    id=f"nav-{item['id']}",
                    href=f"/{item['id']}",
                    style={
                        'borderRadius': '4px',
                        'margin': '4px 8px',
                        'padding': '10px',
                        'fontWeight': 500,
                        'fontSize': '0.95rem',
                        'color': COLORS['text'],
                    }
                ) for item in menu_items
            ], vertical=True, pills=True),
        ], style={'overflow': 'auto', 'marginTop': '16px'}),
    ], style={
        'position': 'fixed',
        'top': '56px',
        'left': 0,
        'bottom': 0,
        'width': '280px',
        'backgroundColor': '#ffffff',
        'borderRight': f"1px solid {COLORS['border']}",
        'zIndex': 1000,
    })

# Overview Page
def create_overview_page():
    kpis = get_kpi_data()
    kpi_cards = [
        {'label': 'Total Cases', 'value': kpis['totalCases'], 'color': COLORS['info']},
        {'label': 'Total Drugs', 'value': kpis['totalDrugs'], 'color': COLORS['primary']},
        {'label': 'High Risk Drugs', 'value': kpis['highRiskDrugs'], 'color': '#ff3621'},
        {'label': 'Total Adverse Events', 'value': kpis['totalAdverseEvents'], 'color': COLORS['secondary']},
    ]

    return html.Div([
        html.H4("Overview Dashboard", style={'marginBottom': '24px', 'fontWeight': 600, 'color': COLORS['primary']}),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P(kpi['label'], style={'color': '#5a6f77', 'marginBottom': '8px'}),
                        html.H3(f"{kpi['value']:,}", style={'fontWeight': 700, 'color': kpi['color']}),
                    ])
                ], style={
                    'height': '100%',
                    'background': f"linear-gradient(135deg, {kpi['color']}15 0%, {kpi['color']}05 100%)",
                    'boxShadow': '0px 2px 8px rgba(27, 49, 57, 0.08)',
                    'transition': 'all 0.3s ease',
                })
            ], width=12, md=6, lg=3, style={'marginBottom': '24px'}) for kpi in kpi_cards
        ])
    ])

# Drug Safety Page
def create_drug_safety_page():
    return html.Div([
        html.H4("Drug Safety Summary", style={'marginBottom': '24px', 'fontWeight': 600, 'color': COLORS['primary']}),
        dbc.Card([
            dbc.CardBody([
                dash_table.DataTable(
                    data=MOCK_DRUG_SAFETY_DATA,
                    columns=[
                        {'name': 'Drug Name', 'id': 'drug_name'},
                        {'name': 'Total Events', 'id': 'total_events'},
                        {'name': 'Signal Score', 'id': 'signal_score'},
                        {'name': 'Risk Level', 'id': 'risk_level'},
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '12px',
                        'fontFamily': '"DM Sans", sans-serif',
                    },
                    style_header={
                        'backgroundColor': COLORS['background'],
                        'fontWeight': 600,
                        'color': COLORS['text'],
                    },
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{risk_level} = "High"'},
                            'backgroundColor': '#ffebee',
                            'color': '#c62828',
                        },
                        {
                            'if': {'filter_query': '{risk_level} = "Medium"'},
                            'backgroundColor': '#fff8e1',
                            'color': '#f57f17',
                        },
                        {
                            'if': {'filter_query': '{risk_level} = "Low"'},
                            'backgroundColor': '#e8f5e9',
                            'color': '#2e7d32',
                        },
                    ],
                )
            ])
        ], style={'boxShadow': '0px 2px 8px rgba(27, 49, 57, 0.08)'})
    ])

# Adverse Events Page
def create_adverse_events_page():
    return html.Div([
        html.H4("Top Adverse Events", style={'marginBottom': '24px', 'fontWeight': 600, 'color': COLORS['primary']}),
        dbc.Card([
            dbc.CardBody([
                dash_table.DataTable(
                    data=MOCK_ADVERSE_EVENTS,
                    columns=[
                        {'name': 'Drug Name', 'id': 'drug_name'},
                        {'name': 'Adverse Event', 'id': 'adverse_event'},
                        {'name': 'Event Count', 'id': 'event_count'},
                        {'name': 'Severity', 'id': 'severity'},
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '12px',
                        'fontFamily': '"DM Sans", sans-serif',
                    },
                    style_header={
                        'backgroundColor': COLORS['background'],
                        'fontWeight': 600,
                        'color': COLORS['text'],
                    },
                )
            ])
        ], style={'boxShadow': '0px 2px 8px rgba(27, 49, 57, 0.08)'})
    ])

# AI/BI Dashboard Page
def create_aibi_dashboard_page():
    dashboards = [
        {'id': 'executive-kpis', 'name': 'Executive KPIs', 'description': 'Key performance indicators and executive summary'},
        {'id': 'drug-safety-analysis', 'name': 'Drug Safety Risk Analysis', 'description': 'Comprehensive drug safety signal analysis and risk heatmap'},
        {'id': 'outcome-analytics', 'name': 'Outcome Analytics', 'description': 'Adverse event outcome distribution and trends'},
        {'id': 'time-series', 'name': 'Time Series Analysis', 'description': 'Monthly case trends and temporal patterns'},
    ]

    return html.Div([
        html.H4("Databricks AI/BI Dashboards", style={'marginBottom': '24px', 'fontWeight': 600, 'color': COLORS['primary']}),
        dbc.Card([
            dbc.CardBody([
                dbc.Label("Select Dashboard"),
                dcc.Dropdown(
                    id='dashboard-dropdown',
                    options=[{'label': d['name'], 'value': d['id']} for d in dashboards],
                    placeholder="Choose a dashboard...",
                    style={'marginBottom': '16px'}
                ),
                html.Div(id='dashboard-description', style={'marginBottom': '16px', 'color': '#5a6f77'}),
            ])
        ], style={'marginBottom': '24px', 'boxShadow': '0px 2px 8px rgba(27, 49, 57, 0.08)'}),

        html.Div(id='dashboard-content')
    ])

# Main Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    create_header(),
    create_sidebar(),
    html.Div([
        html.Div(id='page-content', style={'padding': '24px'})
    ], style={
        'marginLeft': '280px',
        'marginTop': '56px',
        'backgroundColor': COLORS['background'],
        'minHeight': 'calc(100vh - 56px)',
    })
])

# Callback for page navigation
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/' or pathname == '/overview':
        return create_overview_page()
    elif pathname == '/drug-safety':
        return create_drug_safety_page()
    elif pathname == '/adverse-events':
        return create_adverse_events_page()
    elif pathname == '/aibi-dashboards':
        return create_aibi_dashboard_page()
    else:
        return create_overview_page()

# Callback for dashboard description
@app.callback(
    Output('dashboard-description', 'children'),
    Output('dashboard-content', 'children'),
    Input('dashboard-dropdown', 'value')
)
def update_dashboard(dashboard_id):
    if not dashboard_id:
        return "", dbc.Alert(
            [
                html.H5("Select a Dashboard", className="alert-heading"),
                html.P("Choose a dashboard from the dropdown above to view AI/BI analytics.")
            ],
            color="info"
        )

    dashboards = {
        'executive-kpis': ('Key performance indicators and executive summary', ''),
        'drug-safety-analysis': ('Comprehensive drug safety signal analysis and risk heatmap', ''),
        'outcome-analytics': ('Adverse event outcome distribution and trends', ''),
        'time-series': ('Monthly case trends and temporal patterns', ''),
    }

    description, url = dashboards.get(dashboard_id, ('', ''))

    content = dbc.Alert(
        [
            html.H5("Dashboard URL Not Configured", className="alert-heading"),
            html.P("Please configure the dashboard URL in the application."),
            html.Hr(),
            html.P("To configure:", className="mb-1"),
            html.Ol([
                html.Li("Create AI/BI Dashboards in Databricks"),
                html.Li("Get the embed URL for each dashboard"),
                html.Li("Update the dashboard URLs in the application"),
            ]),
            html.P("Embed URL format:", className="mt-2 mb-1"),
            html.Code("https://your-workspace.cloud.databricks.com/sql/dashboards/dashboard-id?o=workspace-id"),
        ],
        color="warning"
    )

    return description, content

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run_server(debug=False, host='0.0.0.0', port=port)
