# filter_state.py

import logging
from schemas.filter import FilterType

filter_name = ""

def load_filtering():
    logging.info("Loading filter file...")

def set_name_from_filter(filters: FilterType) -> None:
    global filter_name
    logging.info("Starting to generate filter name from filters: %s", filters)

    start = filters.get("dt_start") or ""
    end = filters.get("dt_end") or ""
    seg = filters.get("fl_segmentation") or ""
    subtypes = filters.get("fl_subtypes") or []
    code_delays = filters.get("fl_code_delays") or []
    matricules = filters.get("fl_matricules") or []
    segmentation_unit = filters.get("fl_unit_segmentation") or "d"

    logging.debug(
        "Extracted values: start=%s, end=%s, seg=%s, unit=%s | subtypes=%s, code_delays=%s, matricules=%s",
        start, end, seg, segmentation_unit, subtypes, code_delays, matricules
    )

    fname_parts = []

    # Add date info
    if not start and not end:
        logging.debug("No start and end dates provided, adding 'all_dates'")
        fname_parts.append("all_dates")
    else:
        if start:
            logging.debug("Adding start date part: from_%s")
            fname_parts.append(f"from_{start.replace(' ', '_').replace('_', '/')}")
        if end:
            logging.debug("Adding end date part: to_%s")
            fname_parts.append(f"to_{end.replace(' ', '_').replace('_', '/')}")

    # Add segmentation
    if seg:
        logging.debug("Adding segmentation part: segmentation_%s%s", seg, segmentation_unit)    
        fname_parts.append(f"segmentation_{seg}{segmentation_unit}")
    else:
        logging.debug("No segmentation provided, adding 'without_segmentation'")
        fname_parts.append("without_segmentation")

    # Add delay codes
    if code_delays:
        logging.debug("Adding delay codes part: delays_%s")
        fname_parts.append(f"delays_{'_'.join(str(cd) for cd in code_delays)}")
    else:
        logging.debug("No delay codes provided, adding 'all_delays'")
        fname_parts.append("all_delays")

    # Add fleet subtypes
    if subtypes:
        logging.debug("Adding fleet subtypes part: subtype_%s")
        fname_parts.append(f"subtype_{'_'.join(subtypes)}")
    else:
        logging.debug("No subtypes provided, adding 'all_subtypes'")
        fname_parts.append("all_subtypes")

    # Add aircraft registrations
    if matricules:
        logging.debug("Adding aircraft registrations part: matricule_%s")
        fname_parts.append(f"matricule_{'_'.join(matricules)}")
    else:
        logging.debug("No matricules provided, adding 'all_matricules'")
        fname_parts.append("all_matricules")

    filter_name = "_".join(fname_parts)
    logging.info("Generated filter name: %s", filter_name)


def get_filter_name() -> str:
    global filter_name
    if not filter_name:
        logging.warning("Filter name is empty. Generating default filter name...")
        set_name_from_filter({})

    logging.info("Returning filter name: %s", filter_name)
    return filter_name
