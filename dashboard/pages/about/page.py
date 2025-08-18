# dashboard/pages/about/page.py
from dash import html
import dash_bootstrap_components as dbc

from server_instance import get_app

# kept to mirror your login file's imports (not used here, but harmless):

app = get_app()

# ─────────────────────────── Data you can edit ───────────────────────────
# Place photos under: assets/<file>
TEAM = [
    {
        "name": "Taj Eddine Marmoul",
        "role": "AI Engineer",
        "photo": "team/1732545400901.jpg",
        "email": "tajdinetajdine1@gmail.com",
        "linkedin": "https://www.linkedin.com/in/tajeddine-marmoul/",
        # optional: add when ready
        "phone": "+212664410196",
    },
    {
        "name": "Benider Abderrahman",
        "role": "General Engineer",
        "photo": "team/IMG_0812 3 Large.jpeg",
        "email": "abderrahman.benider@centrale-casablanca.ma",
        "linkedin": "https://www.linkedin.com/in/abderrahman-benider/",
        "phone": "+212655823419",
    },
    {
        "name": "Mehdi Ezzahraoui",
        "role": "Software Engineer",
        "photo": "team/1748123614592.jpeg",
        "email": "mehdiezzahraoui35@gmail.com",
        "linkedin": "https://www.linkedin.com/in/mehdi-ezzahraoui-36676b334/",
        "phone": "+212694631607",
    },
    {
        "name": "Adam Hafidi",
        "role": "Software Engineer",
        "photo": "team/n_bakkali.jpg",
        "email": "Hafidi.adam2005@gmail.com",
        "linkedin": "",
        "phone": "+212675202526",
    },
    {
        "name": "Othmane Moutaouakil",
        "role": "Software Engineer",
        "photo": "team/r_chafik.jpg",
        "email": "othmanemtk662@gmail.com",
        "linkedin": "https://www.linkedin.com/in/othmane-moutaouakil-52a333268/",
        "phone": "+212766330723",
    },
]

SUPERVISORS = [
    {
        "name": "M Taoufik Houssam",
        "title": "Aircraft Maintenance Manager",
        "org": "RAM",
    },
    {"name": "Mme El Meskini Ikrame", "title": "Aircraft Scheduler", "org": "RAM"},
    {"name": "M Dchieche Idriss", "title": "Reliability Analyst", "org": "RAM"},
    {"name": "Mme Arbaoui Wijdane", "title": "Software Engineer", "org": "RAM"},
]

# (You can keep STATS/TECH_STACK/MILESTONES if used elsewhere; they’re unused below)

# ─────────────────────────── Layout ───────────────────────────
layout = html.Div(
    className="about-page-enhanced",
    children=[
        # Animated background pattern
        html.Div(className="about-bg-pattern"),
        dbc.Container(
            fluid=True,
            className="about-container px-4",
            children=[
                # ─────── Hero Section (kept) ───────
                dbc.Row(
                    className="about-hero-section",
                    children=[
                        dbc.Col(
                            lg=12,
                            className="text-center",
                            children=[
                                html.Div(
                                    className="hero-badge",
                                    children=[
                                        html.I(className="bi bi-airplane-fill me-2"),
                                        html.Span("RAM DELAY DASHBOARD"),
                                    ],
                                ),
                                html.H1(
                                    "Empowering Operational Excellence",
                                    className="hero-title animate-fade-in",
                                ),
                                html.P(
                                    "A cutting-edge analytics platform transforming flight delay data into actionable insights. ",
                                    className="hero-subtitle animate-fade-in-delay",
                                ),
                            ],
                        )
                    ],
                ),
                # ─────── Team Section (focus/expertise removed; contact lines added) ───────
                html.Div(
                    className="team-section-wrapper",
                    children=[
                        html.H2("Meet Our Team", className="section-title text-center"),
                        html.P(
                            "Passionate professionals dedicated to excellence",
                            className="section-subtitle text-center",
                        ),
                        dbc.Row(
                            className="team-grid g-4 mt-3",
                            children=[
                                dbc.Col(
                                    xs=12,
                                    sm=6,
                                    lg=4,
                                    xl=4,
                                    className="d-flex",
                                    children=[
                                        dbc.Card(
                                            className="team-member-card glass-card h-100",
                                            children=[
                                                html.Div(
                                                    className="member-photo-wrapper",
                                                    children=[
                                                        html.Img(
                                                            src=app.get_asset_url(
                                                                member["photo"]
                                                            ),
                                                            alt=member["name"],
                                                            className="member-photo",
                                                        ),
                                                        # overlay removed via CSS previously; keeping node is harmless
                                                    ],
                                                ),
                                                dbc.CardBody(
                                                    [
                                                        html.H4(
                                                            member["name"],
                                                            className="member-name",
                                                        ),
                                                        html.Span(
                                                            member["role"],
                                                            className="member-role",
                                                        ),
                                                        # REMOVED: member["focus"]
                                                        # REMOVED: expertise tags
                                                        # ADDED: one-line contact rows
                                                        html.Div(
                                                            [
                                                                html.Span("Email: "),
                                                                html.A(
                                                                    member["email"],
                                                                    href=f"mailto:{member['email']}",
                                                                ),
                                                            ],
                                                            className="contact-line mt-2",
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Span("LinkedIn: "),
                                                                html.A(
                                                                    member["linkedin"],
                                                                    href=member[
                                                                        "linkedin"
                                                                    ],
                                                                    target="_blank",
                                                                ),
                                                            ],
                                                            className="contact-line",
                                                        ),
                                                        (
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Phone: "
                                                                    ),
                                                                    html.A(
                                                                        member.get(
                                                                            "phone"
                                                                        ),
                                                                        href=f"tel:{member.get('phone')}",
                                                                    ),
                                                                ],
                                                                className="contact-line",
                                                            )
                                                            if member.get("phone")
                                                            else None
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        )
                                    ],
                                )
                                for member in TEAM
                            ],
                        ),
                    ],
                ),
                # ─────── Technology Stack Section (DELETED) ───────
                # (removed completely per your request)
                # ─────── Supervisors / Advisory Section (kept) ───────
                html.Div(
                    className="supervisors-enhanced-section mt-5",
                    children=[
                        html.H2(
                            "Advisory Board", className="section-title text-center"
                        ),
                        html.P(
                            "Guided by industry experts",
                            className="section-subtitle text-center",
                        ),
                        dbc.Row(
                            className="supervisors-grid g-3 mt-3",
                            children=[
                                dbc.Col(
                                    xs=12,
                                    sm=6,
                                    md=3,
                                    children=[
                                        dbc.Card(
                                            className="supervisor-card glass-card text-center",
                                            children=[
                                                dbc.CardBody(
                                                    [
                                                        html.I(
                                                            className="bi bi-person-circle supervisor-avatar"
                                                        ),
                                                        html.H6(
                                                            sup["name"],
                                                            className="supervisor-name",
                                                        ),
                                                        html.Small(
                                                            sup["title"],
                                                            className="supervisor-title d-block",
                                                        ),
                                                        html.Small(
                                                            sup["org"],
                                                            className="supervisor-org",
                                                        ),
                                                    ]
                                                )
                                            ],
                                        )
                                    ],
                                )
                                for sup in SUPERVISORS
                            ],
                        ),
                    ],
                ),
                # ─────── Footer ───────
                html.Div(
                    className="about-footer-enhanced text-center mt-5",
                    children=[
                        html.Hr(className="footer-divider"),
                        html.P(
                            [
                                "© 2025 Royal Air Maroc • Delay Dashboard",
                                html.Br(),
                                "All rights reserved.",
                            ]
                        ),
                    ],
                ),
            ],
        ),
    ],
)
