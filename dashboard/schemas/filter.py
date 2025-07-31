from datetime import date
from typing import Optional, TypedDict


class FilterType(TypedDict, total=False):
    fl_segmentation: Optional[int]
    fl_unit_segmentation: str
    fl_subtype: Optional[str]
    fl_code_delay: Optional[str]
    fl_matricule: Optional[str]
    dt_start: Optional[date]
    dt_end: Optional[date]
