import json
import os
from pathlib import Path


def create_specializations_json(programs_data):
    print("Creating specializations.json")
    print(f" Processing {len(programs_data)} programs")

    specializations = []

    for program in programs_data:
        # program-level data
        school = program.get("school", "")
        school_type = program.get("school_type", "")
        field = program.get("field", "")
        program_name = program.get("program", "")
        program_id = program.get("program_id", "")
        program_type = program.get("program_type", "")
        rank = program.get("school_rank", "")
        school_accreditations = program.get("school_accreditations", [])
        year_details = program.get("year_details", {})

        # Iterate through each year
        for year in year_details.keys():
            current_specialization_list = year_details[year]

            # program intake info for this year
            program_intake_info = {}
            for item in current_specialization_list:
                if "program_intake" in item.keys():
                    program_intake_info = item
                    break

            # specializations for this year
            for specialization_dict in current_specialization_list:
                if "specialization" in specialization_dict.keys():
                    specialization_name = specialization_dict["specialization"]
                    spec_intake = specialization_dict.get("intake", [])
                    spec_campus = specialization_dict.get("campus", "")
                    spec_language = specialization_dict.get("language", "")
                    spec_alternance = specialization_dict.get("alternance", "")

                    # Get price from program_intake_info
                    price = (
                        program_intake_info.get("price", "")
                        if program_intake_info
                        else ""
                    )
                    duration = (
                        program_intake_info.get("duration", "")
                        if program_intake_info
                        else ""
                    )
                    entry_level = (
                        program_intake_info.get("entry_level", [])
                        if program_intake_info
                        else []
                    )
                    primos_arrivant = (
                        program_intake_info.get("primos_arrivant", False)
                        if program_intake_info
                        else False
                    )

                    # specialization entry
                    specialization_entry = {
                        "specialization": specialization_name,
                        "school": school,
                        "school_type": school_type,
                        "field": field,
                        "program": program_name,
                        "program_id": program_id,
                        "program_type": program_type,
                        "rank": rank,
                        "year": year,
                        "intake": spec_intake,
                        "campus": spec_campus,
                        "language": spec_language,
                        "alternance": spec_alternance,
                        "price": price,
                        "duration": duration,
                        "entry_level": entry_level,
                        "school_accreditations": school_accreditations,
                        "school_rank": rank,
                        "primos_arrivant": primos_arrivant,
                    }

                    specializations.append(specialization_entry)

    # Save to file using absolute path
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "specialisation_data" / "specializations.json"

    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(specializations, f, indent=4, ensure_ascii=False)

    print(f"   - Processed {len(specializations)} specialization entries")
    print(f"Saved specializations to {output_path}")

    return specializations
