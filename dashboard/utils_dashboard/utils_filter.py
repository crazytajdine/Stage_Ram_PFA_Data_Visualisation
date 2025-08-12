# filter_state.py

import logging
from schemas.filter import FilterType

filter_name = ""
filter_list = []


def load_filtering():
    logging.info("Loading filter file...")


def set_name_from_filter(filters: FilterType) -> None:
    global filter_name, filter_list
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
        start,
        end,
        seg,
        segmentation_unit,
        subtypes,
        code_delays,
        matricules,
    )

    filter_list = []
    # Add date info
    if not start and not end:
        logging.debug("No start and end dates provided, adding 'all_dates'")
        filter_list.append("all_dates")
    else:
        if start:
            logging.debug("Adding start date part: from_%s")
            filter_list.append(f"from_{start.replace(' ', '_').replace('_', '/')}")
        if end:
            logging.debug("Adding end date part: to_%s")
            filter_list.append(f"to_{end.replace(' ', '_').replace('_', '/')}")

    # Add segmentation
    if seg:
        logging.debug(
            "Adding segmentation part: segmentation_%s%s", seg, segmentation_unit
        )
        filter_list.append(f"segmentation_{seg}{segmentation_unit}")
    else:
        logging.debug("No segmentation provided, adding 'without_segmentation'")
        filter_list.append("without_segmentation")

    # Add delay codes
    if code_delays:
        logging.debug("Adding delay codes part: delays_%s")
        filter_list.append(f"delays_{'_'.join(str(cd) for cd in code_delays)}")
    else:
        logging.debug("No delay codes provided, adding 'all_delays'")
        filter_list.append("all_delays")

    # Add fleet subtypes
    if subtypes:
        logging.debug("Adding fleet subtypes part: subtype_%s")
        filter_list.append(f"subtype_{'_'.join(subtypes)}")
    else:
        logging.debug("No subtypes provided, adding 'all_subtypes'")
        filter_list.append("all_subtypes")

    # Add aircraft registrations
    if matricules:
        logging.debug("Adding aircraft registrations part: matricule_%s")
        filter_list.append(f"matricule_{'_'.join(matricules)}")
    else:
        logging.debug("No matricules provided, adding 'all_matricules'")
        filter_list.append("all_matricules")
    filter_name = "_".join(filter_list)
    logging.debug(f"Filter list generated: {filter_list}")
    logging.info(f"Generated filter name: {filter_name}")


def get_filter_name() -> str:
    global filter_name
    if not filter_name:
        logging.warning("Filter name is empty. Generating default filter name...")
        set_name_from_filter({})

    logging.info(f"Returning filter name: {filter_name}")
    return filter_name


def get_filter_list() -> list[str]:
    global filter_list
    if not filter_list:
        logging.warning("Filter list is empty. Generating default filter list...")
        set_name_from_filter({})

    logging.info(f"Returning filter list: {filter_list}")
    return filter_list
