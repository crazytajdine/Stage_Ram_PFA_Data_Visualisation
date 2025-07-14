📋 Precise File Descriptions

  🏠 dashboard/pages/home/page.py

  Purpose: Home dashboard page with dynamic metricsContent:
  - Layout: Welcome page with 3 metric cards (Total Users, Active Sessions, Errors)
  - Interactive Elements: Refresh button, monthly user growth chart
  - Callbacks: refresh_data() - generates random dummy metrics on button click
  - Data: Simulated metrics using random.randint() for demo purposes
  - Visual: Bootstrap cards with color coding (primary, success, danger)

  📊 dashboard/pages/tech/page.py

  Purpose: Technical monitoring dashboardContent:
  - Layout: Static tech metrics display
  - Metrics: Server Load (58%), Deployments (4)
  - Chart: Bar chart showing CPU load trend over 24 hours
  - Data: Hardcoded static values for demonstration
  - No Callbacks: Pure static content, no interactivity

  📈 dashboard/pages/tech/delay_codes.py

  Purpose: Excel data analysis for flight delay codesContent:
  - Data Loading: Reads Excel files using Polars, processes TEC delay codes
  - Layout: Two-panel interface (filters left, charts/tables right)
  - Filters: Aircraft type, registration, delay codes, date/time range
  - Analysis: Aggregates delay occurrences by code, airports, statistics
  - Visualization: Horizontal bar chart (top 10 codes), data table with export
  - Dynamic: Reloads data based on configuration, real-time filtering

  ⚙️ dashboard/pages/config/data_config.py

  Purpose: Data source configuration interfaceContent:
  - File Selection: Input field for Excel file path (Mac compatible)
  - Sheet Selection: Input for Excel sheet name
  - Validation: Real-time file existence and format checking
  - Persistence: Saves config to dashboard_config.json
  - Status Display: Live feedback on file validity and data preview
  - Instructions: User guide for required Excel column format

  🎯 dashboard/root.py

  Purpose: Main application controller and routerContent:
  - Navigation Setup: Defines all tabs (Dashboard, Analytics, Delay Codes, Config, Settings)
  - Routing Logic: URL-based page switching with dynamic layout loading
  - Page Imports: Imports all page modules and manages their layouts
  - Callback Hub: Contains ALL application callbacks (delay codes + config)
  - App Layout: Bootstrap navigation bar + dynamic content container
  - Dynamic Rendering: Special handling for data-dependent pages

  🔧 dashboard/server_instance.py

  Purpose: Dash application singleton factoryContent:
  - Singleton Pattern: Ensures only one Dash app instance exists
  - App Initialization: Creates Dash app with Bootstrap theme
  - Global State: Manages global app and server variables
  - Configuration: Sets app title, suppresses callback exceptions
  - Factory Function: get_app() returns shared app instance
  - Thread Safety: Prevents duplicate app creation in multi-import scenarios

  🔄 Architecture Flow:

  server_instance.py → Creates Dash app singleton
         ↓
  root.py → Imports app, sets up navigation, routing, callbacks
         ↓
  page.py files → Define individual page layouts
         ↓
  delay_codes.py → Reads from config, processes Excel data
         ↓
  data_config.py → Manages file configuration

  Each file has a specific, well-defined role in the multi-page dashboard architecture.