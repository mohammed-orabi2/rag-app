def create_filter_conditions(
    program_types, exclude_ids_list, exclude, price_campus_info=None, entry_level=None
):
    """
    Returns filtering conditions based on 'program_types', "exclude", "exclude_ids"

    Args:
        - program_types, List[str]: program types to filter on
        - exclude_ids_list, List[str]: the ids of the documents to exclude

    Returns:
        - filter_conditions, dict
    """
    conditions = []
    language_conditions = []
    entry_level_conditions = []
    if price_campus_info.price:
        if price_campus_info.price_condition == "gt":
            conditions.append({"price": {"$gte": price_campus_info.price - 1000}})
        elif price_campus_info.price_condition == "lt":
            conditions.append({"price": {"$lte": price_campus_info.price + 2000}})

    if price_campus_info.primos_arrivant:
        conditions.append({"primos_arrivant": {"$eq": True}})

    if price_campus_info.languages:
        for lang in price_campus_info.languages:
            language_conditions.append({lang: {"$eq": True}})
        if len(language_conditions) == 1:
            conditions.append(language_conditions[0])
        else:
            conditions.append({"$or": language_conditions})

    # TODO: add entry level conditions
    if entry_level:
        for level in entry_level:
            entry_level_conditions.append({level: {"$eq": True}})
        if len(entry_level_conditions) == 1:
            conditions.append(entry_level_conditions[0])
        else:
            conditions.append({"$or": entry_level_conditions})

    if price_campus_info.school_rank:
        conditions.append({"school_rank": {"$lte": price_campus_info.school_rank}})
    # Always add program type filter

    conditions.append({"new_program_type": {"$in": program_types}})

    # Only add exclude filter if there are IDs to exclude
    if exclude_ids_list and len(exclude_ids_list) > 0 and exclude:
        conditions.append({"program_id": {"$nin": exclude_ids_list}})
    # If only one condition, return it directly; if multiple, use $and
    if len(conditions) == 1:
        return conditions[0]
    else:
        print("Conditions: ", conditions)
        return {"$and": conditions}


def child_parent_retriever_search_params(
    program_types, k, exclude_ids, price_campus_info, entry_level, exclude=True
):
    """
    returns a dict with keyword arguments for the retriever, mainly 'search_type' and 'search_kwargs'

    if 'program_types' is empty, apply filter to all program types available as a default
    else apply filter to all programs in 'program_types'

    Args:
        - program_types, List[str]: list of program types
        - k, int: number of docs that retriever will return
        - exclude_ids, list[str]: the ids of the documents that will be excluded

    Returns:
        search_params, Dict
    """
    search_params = {}
    k += 1

    if program_types:

        conditions = create_filter_conditions(
            program_types, exclude_ids, exclude, price_campus_info, entry_level
        )

        search_params["search_kwargs"] = {
            "k": k,
            "filter": conditions,
        }

    else:
        conditions = create_filter_conditions(
            [
                "less selective master",
                "Mastère Spécialisé®",
                "MSc",
                "BBA",
                "Other",
                "Bachelor",
                "MBA",
                "Cycle Préparatoire",
                "BTS",
            ],
            exclude_ids,
        )

        search_params["search_kwargs"] = {"k": k, "filter": conditions}
    print("Search params:", search_params)
    return search_params


def filter_retriever_search_params(program_types, k):
    """
    returns a dict with keyword arguments for the retriever, mainly 'search_type' and 'search_kwargs'

    if 'program_types' is empty apply filter to all program types available as a default
    else apply filter to all programs in 'program_types'

    Args:
        - program_types, List[str]: list of program types
        - k, int: number of docs that retriever will return

    Returns:
        search_params, Dict
    """
    search_params = {}
    filters = {}

    if len(program_types) == 0:

        filters["program_type"] = {
            "$in": [
                "less selective master",
                "Mastère Spécialisé®",
                "MSc",
                "BBA",
                "Other",
                "Bachelor",
                "MBA",
                "Cycle Préparatoire",
                "BTS",
            ]
        }

        search_params["search_kwargs"] = {"k": k, "filter": filters}

    else:
        search_params["search_type"] = "mmr"

        filters["program_type"] = {"$in": program_types}

        search_params["search_kwargs"] = {"k": k, "filter": filters}

    return search_params
