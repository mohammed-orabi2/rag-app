from helper_functions import save_json_file


def create_program_data(tables, mappings):
    """
    Build the core program data structure with intakes and specializations.
    Moved from full_data_pipeline.py DataProcessor._create_data()
    """
    dummy_data = []

    program_ids = {program["program_id"] for program in tables["programs"]}

    for program_id in program_ids:

        program_intakes_temp = []  # Storing all intakes for a program
        program_specializations_temp = []  # Storing all specializations for a program

        dummy_dict = (
            {}
        )  # The smallest unit of data that will be appended to the data list
        dummy_dict["program"] = mappings["program_name"][
            program_id
        ].strip()  # Get the program name
        dummy_dict["program_description"] = mappings["program_description"][
            program_id
        ]  # Get the program description

        school_id = mappings["program_school"][program_id]
        dummy_dict["school"] = mappings["school_name"][school_id][
            0
        ]  # Get the school name
        dummy_dict["school_accreditations"] = mappings["school_name"][school_id][2]

        dummy_dict["school_rankings"] = mappings["school_name"][school_id][3]

        dummy_dict["school_rank"] = 0

        dummy_dict["program_id"] = 0

        # Add primos_arrivant key with empty string at program level
        dummy_dict["primos_arrivant"] = ""

        # Initialize year_details dictionary and available_intakes set
        year_details = {}
        available_intakes = set()

        for program_intake in tables["program_intakes"]:
            if program_intake["program_id"] == program_id:
                program_intakes_temp.append(program_intake)

                # Collect intake names for available_intakes (filter out None values)
                if (
                    "program_intake" in program_intake
                    and program_intake["program_intake"] is not None
                ):
                    available_intakes.add(program_intake["program_intake"])

                # Remove unwanted keys
                keys_to_exclude = {"program_id", "intake_id", "year_id"}
                filtered_intake = {
                    k: v for k, v in program_intake.items() if k not in keys_to_exclude
                }

                # Add primos_arrivant key with empty string
                filtered_intake["primos_arrivant"] = ""

                year_key = f"year_{mappings['year_id'][program_intake['year_id']]}"
                if year_key in year_details:
                    year_details[year_key].append(filtered_intake)
                else:
                    year_details[year_key] = [filtered_intake]

        for program_specialization in tables["program_specializations"]:
            if program_specialization["program_id"] == program_id:
                program_specializations_temp.append(program_specialization)

                # Remove unwanted keys
                keys_to_exclude = {
                    "program_id",
                    "specialization_id",
                    "year_id",
                    "live_in_eu",
                    "not_live_in_eu",
                    "price",
                }
                filtered_specialization = {
                    k: v
                    for k, v in program_specialization.items()
                    if k not in keys_to_exclude
                }

                year_key = (
                    f"year_{mappings['year_id'][program_specialization['year_id']]}"
                )
                if year_key in year_details:
                    year_details[year_key].append(filtered_specialization)

        # Add year_details to dummy_dict instead of individual year keys
        dummy_dict["year_details"] = year_details

        # Add available_intakes only if not empty
        # if available_intakes:
        #     dummy_dict["available_intakes"] = sorted(list(available_intakes))

        dummy_data.append(dummy_dict)

    print(f"Sample program data entry: {dummy_data[3]}")
    save_json_file("data/programs/raw_data.json", dummy_data)
    print("✅ Saved raw program data to programs/raw_data.json")
    return dummy_data
