import shutil
from get_tables import fetch_and_save_filtered_data
from data_loaders import load_tables
from create_mappings import create_mappings
from data_transformers import create_program_data
from data_enrichers import (
    add_specializations_and_prices,
    school_type_field_adder,
    program_mapper,
    add_campuses,
    add_language,
    map_entry_level_with_programs
)
from rankings_formatting import add_rankings_numbers
from specialization_extractors import create_specializations_json
from programs_generator import program_md_generator
from specializations_generator import specialization_md_generator
from school_type_splitter import split_school_types
from create_vdb import create_vectorstore
from primos_arrivant_mapper import map_primos_arrivant
# from entry_level_mapping import map_entry_level_with_programs


def run_full_pipeline():
    """
    Run the complete data processing pipeline.
    """
    print("\n" + "=" * 60)
    print(" STARTING FULL DATA PIPELINE")
    print("=" * 60 + "\n")

    print("Step 1: Fetching data from API...")
    fetch_and_save_filtered_data(output_path="data/raw/new_tables.json")
    print()

    print("Step 2: Loading tables...")
    tables = load_tables("data/raw/new_tables.json")
    print()

    print("Step 3: Creating mappings...")
    mappings = create_mappings(tables)
    print(" Mappings created")
    print()

    print("Step 4: Creating program data structure...")
    data = create_program_data(tables, mappings)
    print()

    print("Step 5: Mapping the entry levels with programs...")
    data = map_entry_level_with_programs(data)
    print()
    print("Step 6: Adding specializations and prices...")
    data = add_specializations_and_prices(data)
    print()

    print("step 7: Adding campuses to programs...")
    data = add_campuses(data)
    print()

    print("Step 8: Adding language information to programs...")
    data = add_language(data)
    print()


    print("Step 9 : Adding school types and fields to programs...")
    data = school_type_field_adder(data)
    print()

    print("Step 10: Classifying programs and applying business rules...")
    data = program_mapper(data)
    print()

    print("Step 11: Mapping primos arrivant values...")

    # data = map_primos_arrivant(
    #     programs_json_path="data/programs/programs.json",
    #     csv_path="data/raw/domain expert knowledge - Sheet1.csv",
    #     output_path="data/programs/programs.json",
    # )

    data = add_rankings_numbers(data, output_path="data/programs/programs.json")

    print("intermediary step")
    specializations_data = create_specializations_json(data)
    print()

    print("=" * 60)
    print(
        f"PIPELINE COMPLETE - Processed {len(data)} programs and {len(specializations_data)} specializations"
    )

    print("=" * 60)
    program_md_generator(child_parent_split=True)
    print(f"Generated programs markdowns")
    print("=" * 60)
    specialization_md_generator()
    print(f"Generated specializations markdowns")
    print("=" * 60 + "\n")

    print("Step 12: Splitting programs by school type...")
    split_school_types()
    print("Programs split into GE and ES")
    print("=" * 60 + "\n")

    print("Step 13: Cleaning up old vector store...")
    shutil.rmtree("data/vector_store/combined_collections", ignore_errors=True)

    print("Step 14: Creating vector database...")
    ge_coll, es_coll, spec_coll = create_vectorstore(
        persist_directory="data/vector_store/combined_collections"
    )
    print("Vector database created with 3 collections (GE, ES, Specializations)")
    print("=" * 60 + "\n")

    return data


if __name__ == "__main__":
    run_full_pipeline()
