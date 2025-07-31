from datetime import date
from typing import Optional, TypedDict


class FilterType(TypedDict, total=False):
    fl_segmentation: Optional[int]
    fl_unit_segmentation: str
    fl_subtypes: Optional[list[str]]
    fl_code_delays: Optional[list[str]]
    fl_matricules: Optional[list[str]]
    dt_start: Optional[date]
    dt_end: Optional[date]
