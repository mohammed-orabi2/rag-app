"""
Primos Arrivant Mapper

This module maps primos_arrivant values to programs based on domain expert knowledge.
It reads a CSV file containing school names, programs, and year information, then updates
the programs JSON with appropriate primos_arrivant flags.
"""

import pandas as pd
import json
import os
from helper_functions import save_json_file
import gspread
from google.oauth2.service_account import Credentials

def normalize_year(year_str):
    """
    Convert 'Year 1', 'Year 2', etc. to 'year_1', 'year_2' format.

    Args:
        year_str (str): Year string from CSV (e.g., 'Year 1', 'Year 2', 'None')

    Returns:
        str or None: Normalized year string (e.g., 'year_1') or None
    """
    if year_str == "None":
        return None
    # Extract the year number
    if "Year" in year_str:
        year_num = year_str.split()[1]
        return f"year_{year_num}"
    return None


def load_primos_arrivant_csv():
    """
    Load and preprocess the primos arrivant CSV file.

    Args:
        csv_path (str): Path to the CSV file

    Returns:
        dict: Mapping of (school, program) -> year
    """
        # --- Authentication with Google ---
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(
        r"C:\Users\apder\Downloads\phonic-oxide-478015-f5-b83f121f9ad9.json",
        scopes=scopes
    )
    client = gspread.authorize(credentials)

    # --- Opening the Sheet ---
    sheet_id = "1S2arFhbhGviXxN5qquDXZPrxCrjovCEqEg3lnRSvkz0"
    sheet = client.open_by_key(sheet_id).sheet1  # first worksheet
    values_list = sheet.get_all_values()
    
    # --- Convert to DataFrame ---
    head=values_list[0]
    values=values_list[1:]
    for i, h in enumerate(head):
        if h.strip() == '':
            head[i] = f'Unnamed:{i}'
    csv=pd.DataFrame(values,columns=head)
    print(f"📄 Loaded {len(csv)} rows from Google Sheet")


    # Rename columns
    csv.rename(columns={csv.columns[3]: "year"}, inplace=True)
    csv.rename(columns={csv.columns[4]: "language"}, inplace=True)
    csv.fillna("None", inplace=True)

    # Clean up year values (e.g., 'Year 2 only' -> 'Year 2')
    csv["year"] = csv.apply(
        lambda row: row["year"] if row["year"] != "Year 2 only" else "Year 2", axis=1
    )

    # Create mapping
    school_program_year_map = {}
    for _, row in csv.iterrows():
        key = (row["School name"].strip(), row["Programms"].strip())
        school_program_year_map[key] = row["year"]

    print(f"✅ Loaded {len(school_program_year_map)} CSV entries")
    return school_program_year_map


def apply_primos_arrivant_mapping(programs, school_program_year_map):
    """
    Apply primos_arrivant mapping to programs based on CSV data.

    Args:
        programs (list): List of program dictionaries
        school_program_year_map (dict): Mapping of (school, program) -> year

    Returns:
        tuple: (updated_programs, stats_dict)
    """
    print("\n🔄 Applying primos_arrivant mapping...")

    updated_count = 0
    matched_programs = []

    for program in programs:
        school_name = program["school"].strip()
        program_name = program["program"].strip()

        # Check if this school+program combination exists in CSV
        key = (school_name, program_name)

        if key in school_program_year_map:
            # Program found in CSV - set program-level primos_arrivant to True
            program["primos_arrivant"] = True
            csv_year = school_program_year_map[key]
            normalized_year = normalize_year(csv_year)

            matched_programs.append(
                {
                    "school": school_name,
                    "program": program_name,
                    "csv_year": csv_year,
                    "normalized_year": normalized_year,
                }
            )

            # Update year-level primos_arrivant
            if "year_details" in program and program["year_details"]:
                for year_key, intakes in program["year_details"].items():
                    for intake in intakes:
                        # Set to True only if this is the specified year, otherwise False
                        if normalized_year and year_key == normalized_year:
                            intake["primos_arrivant"] = True
                        elif normalized_year is None:
                            # If no specific year mentioned, set all years to True
                            intake["primos_arrivant"] = True
                        else:
                            intake["primos_arrivant"] = False

            updated_count += 1
        else:
            # Program not found in CSV - set all primos_arrivant to False
            program["primos_arrivant"] = False

            if "year_details" in program and program["year_details"]:
                for year_key, intakes in program["year_details"].items():
                    for intake in intakes:
                        intake["primos_arrivant"] = False

    # Check for CSV entries that didn't match any program
    csv_entries = set(school_program_year_map.keys())
    json_entries = set((p["school"].strip(), p["program"].strip()) for p in programs)
    unmatched_in_csv = csv_entries - json_entries

    stats = {
        "total_programs": len(programs),
        "matched_programs": updated_count,
        "unmatched_programs": len(programs) - updated_count,
        "unmatched_csv_entries": len(unmatched_in_csv),
    }

    print(f"✅ Updated {updated_count} programs with primos_arrivant = True")
    print(f"📊 Total programs processed: {len(programs)}")
    print(f"🔍 Programs not in CSV (set to False): {len(programs) - updated_count}")

    if unmatched_in_csv:
        print(f"\n⚠️  {len(unmatched_in_csv)} CSV entries not found in JSON:")
        for school, program in list(unmatched_in_csv)[:5]:
            year = school_program_year_map[(school, program)]
            print(f"  - {school}: {program} (Year: {year})")
        if len(unmatched_in_csv) > 5:
            print(f"  ... and {len(unmatched_in_csv) - 5} more")

    return programs, stats


def map_primos_arrivant(
    programs_json_path="data/programs/programs.json",
    csv_path="data/raw/domain expert knowledge - Sheet1.csv",
    output_path="data/programs/programs.json",
):
    """
    Main function to map primos_arrivant values to programs.

    Args:
        programs_json_path (str): Path to the programs JSON file
        csv_path (str): Path to the CSV file with primos arrivant data
        output_path (str): Path to save the updated programs JSON

    Returns:
        list: Updated programs list
    """
    print("\n" + "=" * 60)
    print(" PRIMOS ARRIVANT MAPPING")
    print("=" * 60 + "\n")

    # Handle relative paths - check if file exists, if not try with ../ prefix
    def resolve_path(path):
        if os.path.exists(path):
            return path
        # Try with ../ prefix (for when running from operations directory)
        alt_path = os.path.join("..", path.replace("data/", ""))
        if os.path.exists(alt_path):
            return alt_path
        return path  # Return original if neither works

    programs_json_path = resolve_path(programs_json_path)
    csv_path = resolve_path(csv_path)
    output_path = resolve_path(output_path)

    # Load programs JSON
    print(f"📄 Loading programs from: {programs_json_path}")
    with open(programs_json_path, "r", encoding="utf-8") as f:
        programs = json.load(f)
    print(f"✅ Loaded {len(programs)} programs")

    # Load and process CSV
    school_program_year_map = load_primos_arrivant_csv()

    # Apply mapping
    programs, stats = apply_primos_arrivant_mapping(programs, school_program_year_map)

    # Save updated programs
    print(f"\n💾 Saving updated programs to: {output_path}")
    save_json_file(output_path, programs)

    print("\n" + "=" * 60)
    print(" PRIMOS ARRIVANT MAPPING COMPLETE")
    print("=" * 60)
    print(f"Summary:")
    print(f"  - Total programs: {stats['total_programs']}")
    print(f"  - Programs with primos_arrivant=True: {stats['matched_programs']}")
    print(f"  - Programs with primos_arrivant=False: {stats['unmatched_programs']}")
    print(f"  - Unmatched CSV entries: {stats['unmatched_csv_entries']}")
    print("=" * 60 + "\n")

    return programs


if __name__ == "__main__":
    # Run the mapping as a standalone script
    map_primos_arrivant()
