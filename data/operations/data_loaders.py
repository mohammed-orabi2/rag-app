from helper_functions import read_json_file


def load_tables(json_file_path):
    """
    Load and structure tables from JSON file.
    Moved from full_data_pipeline.py DataProcessor._load_tables()
    """
    raw_data = read_json_file(json_file_path)
    print(f"Loaded raw data from {json_file_path}")

    tables = dict()
    tables["schools"] = raw_data[0]
    tables["programs"] = raw_data[1]
    tables["program_year"] = raw_data[2]
    tables["program_intakes"] = raw_data[3]
    tables["program_specializations"] = raw_data[4]

    return tables
