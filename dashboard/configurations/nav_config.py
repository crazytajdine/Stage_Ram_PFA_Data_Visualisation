from pages.home.metadata import metadata as home_metadata
from pages.analytics.metadata import metadata as tech_metadata
from pages.weekly.metadata import metadata as weekly_metadata
from pages.performance_metrics.metadata import metadata as perf_metrics_metadata
from pages.settings.metadata import metadata as settings_metadata
from pages.undefined.metadata import metadata as undefined_metadata
from pages.about.metadata import metadata as about_metadata

NAV_CONFIG = [
    # content
    home_metadata,
    tech_metadata,
    weekly_metadata,
    perf_metrics_metadata,
    undefined_metadata,
    # manage
    settings_metadata,
    # about
    about_metadata,
]
