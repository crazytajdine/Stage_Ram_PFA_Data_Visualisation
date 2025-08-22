poetry run python -m nuitka `
    --msvc=latest `
    --standalone `
    --output-dir=build `
    --include-package=dash,dash_bootstrap_components,plotly,polars,fastexcel,dashboard `
    --include-package-data=dash,dash_bootstrap_components,plotly,polars,fastexcel `
    --include-data-files=dashboard/configurations/config.toml=configurations/config.toml `
    dashboard/main.py
