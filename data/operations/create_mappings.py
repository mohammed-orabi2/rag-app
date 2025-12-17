def create_mappings(tables):
    """
    Create all mappings from tables.
    Moved from full_data_pipeline.py DataProcessor._create_mappings()
    """
    year_id_mapping = {}
    program_year_mapping = {}
    program_intakes_mapping = {}
    program_school_mapping = {}
    school_name_mapping = {}
    program_name_mapping = {}
    program_description_mapping = {}

    for entity in tables["program_year"]:
        year_id_mapping[entity["year_id"]] = entity["program_year"]
        program_year_mapping[entity["program_id"]] = entity["program_year"]

    for program in tables["program_intakes"]:
        if program["program_id"] in program_intakes_mapping:
            program_intakes_mapping[program["program_id"]].append(
                program["program_intake"]
            )
        else:
            program_intakes_mapping[program["program_id"]] = [program["program_intake"]]

    # mappings for each program_id with it's schools_id
    for program in tables["programs"]:
        program_school_mapping[program["program_id"]] = program["school_id"]
        program_name_mapping[program["program_id"]] = program["program_name"]
        program_description_mapping[program["program_id"]] = program["overview_en"]

    # mapping for school_id with it's name, description and rank
    for school in tables["schools"]:
        if school["school_metadata"]:
            school_name_mapping[school["school_id"]] = [
                school["school_name"],
                school["description_en"],
                school["school_metadata"].get("accreditations", []),
                school["school_metadata"]
                .get("rankings", dict())
                .get("average_fr_rank"),
            ]
        else:
            school_name_mapping[school["school_id"]] = [
                school["school_name"],
                school["description_en"],
                [],
                dict(),
            ]

    # add all mappings to mappings dict and return it
    mappings = {
        "year_id": year_id_mapping,
        "program_year": program_year_mapping,
        "program_intakes": program_intakes_mapping,
        "program_school": program_school_mapping,
        "school_name": school_name_mapping,
        "program_name": program_name_mapping,
        "program_description": program_description_mapping,
    }
    return mappings
