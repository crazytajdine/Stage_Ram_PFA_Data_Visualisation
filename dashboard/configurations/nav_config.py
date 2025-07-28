from pages.home.metadata import metadata as home_metadata
from pages.tech.metadata import metadata as tech_metadata
from pages.weekly.metadata import metadata as weekly_metadata
from pages.performance_metrics.metadata import metadata as perf_metrics_metadata
from pages.settings.metadata import metadata as settings_metadata
from pages.verify.metadata import metadata as verify_metadata

NAV_CONFIG = [
    home_metadata,
    tech_metadata,
    weekly_metadata,
    perf_metrics_metadata,
    settings_metadata,
]

NAV_CONFIG_VERIFY = [verify_metadata]
