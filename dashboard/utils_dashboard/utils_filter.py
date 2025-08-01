# filter_state.py
from schemas.filter import FilterType

filter_name = ""


def set_name_from_filter(filters: FilterType) -> None:

    global filter_name
    start = filters.get("dt_start") or ""
    end = filters.get("dt_end") or ""
    seg = filters.get("fl_segmentation") or ""
    subtypes = filters.get("fl_subtypes") or []
    code_delays = filters.get("fl_code_delays") or []
    matricules = filters.get("fl_matricules") or []
    segmentation_unit = filters.get("fl_unit_segmentation") or "d"

    fname_parts = []

    # Ajout des dates
    if not start and not end:
        fname_parts.append("all_dates")
    else:
        if start:
            fname_parts.append(f"from_{start.replace(' ', '_').replace('_', '/')}")
        if end:
            fname_parts.append(f"to_{end.replace(' ', '_').replace('_', '/')}")

    # Ajout de la segmentation
    if seg:
        fname_parts.append(f"segmentation_{seg}{segmentation_unit}")
    else:
        fname_parts.append("without_segmentation")

    # Ajout des codes delay
    if code_delays:
        fname_parts.append(f"delays_{'_'.join(str(cd) for cd in code_delays)}")
    else:
        fname_parts.append("all_delays")

    # Ajout de la flotte (liste)
    if subtypes:
        fname_parts.append(f"subtype_{'_'.join(subtypes)}")
    else:
        fname_parts.append("all_subtypes")

    # Ajout des matricules (liste)
    if matricules:
        fname_parts.append(f"matricule_{'_'.join(matricules)}")
    else:
        fname_parts.append("all_matricules")

    filter_name = "_".join(fname_parts)


def get_filter_name() -> str:
    global filter_name
    if not filter_name:
        set_name_from_filter({})

    return filter_name
