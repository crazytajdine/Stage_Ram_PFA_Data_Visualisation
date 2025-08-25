poetry run python -m nuitka `
    --msvc=latest `
    --standalone `
    --output-dir=build `
    --include-package=dash,dash_bootstrap_components,plotly,polars,fastexcel,dashboard `
    --include-package-data=dash,dash_bootstrap_components,plotly,polars,fastexcel `
    --include-data-files=dashboard/configurations/config.toml=configurations/config.toml `
    --include-data-dir=dashboard/assets=assets `
    --windows-company-name="Taj Eddine Marmoul" `
    --copyright="Taj Eddine Marmoul" `
    --windows-icon-from-ico="icon.ico" `
    --windows-product-name="Flight Delay Dashboard" `
    --windows-file-description="Analytics tool for RAM flight delays" `
    --windows-file-version="1.0.0" `
    --windows-product-version="1.0.0" `
    "dashboard/RAM Delay Dashboard.py"
