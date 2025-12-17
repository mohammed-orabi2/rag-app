import json
import pandas as pd
from helper_functions import (
    save_json_file,
    read_json_file,
    simple_fuzzy_match,
    remove_emojis,
    normalize_name
)
from program_type_classifier_optimized import classify_program


def add_specializations_and_prices(data):
    """
    Add specializations list and price range to each program.
    Moved from full_data_pipeline.py DataProcessor.add_specializations_and_prices()
    """
    for entry in data:

        # Extract all specializations
        specializations = []
        prices = []

        # Access year data from year_details structure
        year_details = entry.get("year_details", {})

        for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
            if year_key in year_details:
                for year_data in year_details[year_key]:

                    if isinstance(year_data, dict) and "specialization" in year_data:
                        spec = year_data["specialization"]
                        if spec and spec not in specializations:
                            specializations.append(spec.strip())

                    if isinstance(year_data, dict) and "price" in year_data:
                        try:
                            # Clean and convert price to float
                            price_str = str(year_data["price"]).strip()
                            if price_str and price_str.lower() not in [
                                "nan",
                                "none",
                                "",
                                "null",
                            ]:
                                # Remove currency symbols and commas
                                clean_price = (
                                    price_str.replace("€", "")
                                    .replace(",", "")
                                    .replace(" ", "")
                                )
                                price_value = float(clean_price)
                                if price_value > 0:  # Only add positive prices
                                    prices.append(price_value)
                        except (ValueError, TypeError):
                            # Skip invalid price values
                            continue

        # Add specializations to top level
        entry["specializations"] = (
            specializations if specializations else "no specializations"
        )

        if prices:
            min_price = min(prices)
            max_price = max(prices)
            if min_price == max_price:
                entry["price_range"] = f"€{int(min_price)}"
            else:
                entry["price_range"] = f"€{int(min_price)}-€{int(max_price)}"
        else:
            entry["price_range"] = "Price not available"

        if prices:
            entry["price_average"] = sum(prices) / len(prices)

    save_json_file("data/programs/programs.json", data)
    print("✅ Added specializations and prices, saved to programs/programs.json")
    return data

def add_campuses(data):
    """
    Add campuses list to each program containing all unique campuses across all years.
    """
    for entry in data:
        # Set to store unique campuses
        all_campuses = set()
        
        # Access year data from year_details structure
        year_details = entry.get("year_details", {})
        
        for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
            if year_key in year_details:
                for year_data in year_details[year_key]:
                    if isinstance(year_data, dict) and "campus" in year_data:
                        campus_list = year_data["campus"]
                        if isinstance(campus_list, list):
                            # Add all campuses from this year_data to the set
                            for campus in campus_list:
                                if campus and campus.strip():  # Only add non-empty campuses
                                    all_campuses.add(campus.strip())
        
        # Convert set to sorted list and add to entry
        entry["campuses"] = sorted(list(all_campuses)) if all_campuses else []

    save_json_file("data/programs/programs.json", data)
    print("✅ Added campuses, saved to programs/programs.json")
    return data

def add_accreditations(data):
    """
    Add accreditation information to each program.
    """
    for entry in data:
        # Set to store unique campuses
        all_accreditations = set()
        
        # Access year data from year_details structure
        year_details = entry.get("year_details", {})
        print(year_details)
        for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
            if year_key in year_details:
                for year_data in year_details[year_key]:
                    if isinstance(year_data, dict) and "accreditations" in year_data:
                        accreditation_list = year_data["accreditations"]
                        if isinstance(accreditation_list, list):
                            # Add all accreditations from this year_data to the set
                            for accreditation in accreditation_list:
                                if accreditation and accreditation.strip():  # Only add non-empty accreditations
                                    all_accreditations.add(accreditation.strip())

        # Convert set to sorted list and add to entry
        entry["accreditations"] = sorted(list(all_accreditations)) if all_accreditations else []

    save_json_file("data/programs/programs.json", data)
    print("✅ Added accreditations, saved to programs/programs.json")
    return data


def add_language(data):
    """
    Add languages list to each program containing all unique languages across all years.
    Moved from full_data_pipeline.py DataProcessor.add_language()
    """
    for entry in data:
        # Set to store unique languages
        all_languages = set()

        # Access year data from year_details structure
        year_details = entry.get("year_details", {})

        for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
            if year_key in year_details:
                for year_data in year_details[year_key]:
                    if isinstance(year_data, dict) and "intake_language" in year_data:
                        language = year_data["intake_language"]
                        if language and language.strip():
                            all_languages.add(language.strip())

        # Convert set to sorted list and add to entry
        entry["languages"] = sorted(list(all_languages)) if all_languages else []

    save_json_file("data/programs/programs.json", data)
    print("✅ Added languages, saved to programs/programs.json")
    return data


def school_field_type_matcher(data):
    """
    Match schools with their type and field from CSV.
    Moved from full_data_pipeline.py DataProcessor.school_field_type_matcher()
    """
    programs = pd.read_csv("data/raw/programs.csv")

    # Replace all columns names spaces with underscores and lowercase them
    programs.columns = programs.columns.str.replace(" ", "_")
    programs.columns = programs.columns.str.lower()

    # Apply to specific columns
    programs["field"] = programs["field"].apply(remove_emojis)
    programs["grande_ecole_or_ecole_spécialisée"] = programs[
        "grande_ecole_or_ecole_spécialisée"
    ].apply(remove_emojis)

    csv_schools = programs["school_name"].unique().tolist()
    # make all school names lowercase and strip spaces
    csv_schools = [school.strip() for school in csv_schools]
    # make all school names lowercase and strip spaces in programs csv
    programs["school_name"] = programs["school_name"].str.strip()

    data_entry_schools = [item["school"].strip() for item in data]

    matched_schools = {}
    unmatched_schools = []
    for csv_school in csv_schools:
        # print(csv_school)
        match = False
        for data_entry_school in data_entry_schools:
            score = simple_fuzzy_match(csv_school, data_entry_school)
            if score == 1:  # If the match is good enough
                match = True
                filtered_programs = programs[programs["school_name"] == csv_school]
                dummy = {
                    f"{data_entry_school}": {
                        "school_type": filtered_programs[
                            "grande_ecole_or_ecole_spécialisée"
                        ].values[0],
                        "field": filtered_programs["field"].values[0],
                    }
                }
                matched_schools.update(dummy)
                break

        if not match:
            unmatched_schools.append(csv_school)
            print(f"no match found for csv school {csv_school}")

    save_json_file("data/mappings/school_type_and_field.json", matched_schools)
    save_json_file("data/mappings/unmatched_schools.json", unmatched_schools)
    print("✅ Matched schools, saved to data/mappings/school_type_and_field.json")


def school_type_field_adder(data):
    """
    Add school type and field to each program from matched schools.
    Moved from full_data_pipeline.py DataProcessor.school_type_field_adder()
    """
    data_with_school_type = read_json_file("data/mappings/school_type_and_field.json")
    # add for each index of the list data the school type and field according to the school name
    for item in data:
        school_name = item["school"].strip()  # Get the school name and strip spaces
        if school_name in data_with_school_type:
            item["school_type"] = data_with_school_type[school_name][
                "school_type"
            ].strip()
            item["field"] = data_with_school_type[school_name]["field"].strip()
            continue
        else:
            print(f"no match found for {school_name}")
            item["school_type"] = None
            item["field"] = None

    save_json_file("data/programs/programs.json", data)
    print("✅ Added school types and fields, saved to programs/programs.json")
    return data


def program_mapper(data):
    """
    Classify programs using optimized classifier and add enrichment data.
    Classification is handled entirely by the classifier - no manual business rules.
    """
    # Classify each program using the optimized classifier
    classified_programs = {}
    for entity in data:
        program_name = entity["program"].strip()
        program_type = classify_program(entity)  # Pass full entity dict
        classified_programs[program_name] = program_type
        entity["program_type"] = program_type if program_type else ""
    
    # Save classification mapping
    save_json_file("data/mappings/programs_classification.json", classified_programs)

    # Add program IDs
    i = 1
    for entity in data:
        entity["program_id"] += i
        i += 1

    # Add program links with school-specific matching
    with open("data/mappings/program_links_from_google_merged_WITH_MISSING.json", "r", encoding="utf-8") as f:
        schools_with_links = json.load(f)

    # Create a mapping: {school_name: {program_name: link}}
    school_program_links = {}
    for school_entry in schools_with_links:
        school_name = school_entry['school_name'].strip()
        school_program_links[school_name] = {}
        for program_entry in school_entry.get('programs', []):
            program_name = program_entry['program_name'].strip()
            school_program_links[school_name][program_name] = program_entry.get('found_link')

    # Match programs with links based on school + program name
    matched_count = 0
    unmatched_schools = set()
    unmatched_programs = []
    
    for program in data:
        program_name = program['program'].strip()
        school_name = program['school'].strip()
        
        #initlaising program_link to None
        program['program_link'] = None
        
        # Normalize school name for matching by removing accents and lowercasing
        normalized_school = normalize_name(school_name)
        
        # Extract first word from normalized school name for pre-filtering
        school_first_word = normalized_school.split()[0] if normalized_school.split() else normalized_school
        
        # Find matching school
        matched_school = None
        best_score = 0
        
        for link_school_name in school_program_links.keys():
            normalized_link_school = normalize_name(link_school_name)
            
            # Pre-filter: Check if first word matches or has high fuzzy similarity 
            link_first_word = normalized_link_school.split()[0] if normalized_link_school.split() else normalized_link_school
            first_word_score = simple_fuzzy_match(school_first_word, link_first_word)
            
            #skip if first words don't match well enough
            if first_word_score < 0.80:
                continue
            
            # Try exact match first
            if normalized_school == normalized_link_school:
                matched_school = link_school_name
                best_score = 1.0
                break
            
            # If first word matches very well (>=90%), accept as match
            # This handles cases like "IIM Digital School" vs "IIM La grande école", where we can just check the first word
            if first_word_score >= 0.90 and first_word_score > best_score:
                best_score = first_word_score
                matched_school = link_school_name
            
            #try fuzzy match on full name
            score = simple_fuzzy_match(normalized_school, normalized_link_school)
            if score >= 0.90 and score > best_score:
                best_score = score
                matched_school = link_school_name
        
        if matched_school:
            #school is matched, now try to match program
            school_programs = school_program_links[matched_school]
            normalized_program = normalize_name(program_name)
            
            #try exact program match first
            program_matched = False
            for link_program_name, link in school_programs.items():
                normalized_link_program = normalize_name(link_program_name)
                
                if normalized_program == normalized_link_program:
                    program['program_link'] = link
                    matched_count += 1
                    program_matched = True
                    break
            
            # no exact match, try fuzzy
            if not program_matched:
                best_prog_score = 0
                best_prog_link = None
                
                for link_program_name, link in school_programs.items():
                    normalized_link_program = normalize_name(link_program_name)
                    score = simple_fuzzy_match(normalized_program, normalized_link_program)
                    
                    if score >= 0.90 and score > best_prog_score:
                        best_prog_score = score
                        best_prog_link = link
                
                if best_prog_link:
                    program['program_link'] = best_prog_link
                    matched_count += 1
                else:
                    # School matched but program didn't
                    unmatched_programs.append({
                        'school': school_name,
                        'matched_to': matched_school,
                        'program': program_name,
                        'reason': 'program_not_found_in_school'
                    })
        else:
            # School not matched
            unmatched_schools.add(school_name)
            unmatched_programs.append({
                'school': school_name,
                'best_match_score': round(best_score, 2),
                'program': program_name,
                'reason': 'school_not_found'
            })
    
    # Print statistics
    print(f"✅ Matched {matched_count}/{len(data)} programs with links")
    
    if unmatched_schools:
        print(f"⚠️  {len(unmatched_schools)} unique schools not found in links file")
    if unmatched_programs:
        print(f"⚠️  {len(unmatched_programs)} programs without links (null)")
        # Save unmatched for debugging
        save_json_file("data/mappings/unmatched_program_links.json", unmatched_programs)
        print("   Details saved to data/mappings/unmatched_program_links.json")

    save_json_file("data/programs/programs.json", data)
    print("✅ Classified programs, saved to programs/programs.json")
    return data


def map_entry_level_with_programs(data):
    years_list = ['year_1','year_2', 'year_3', 'year_4', 'year_5']
    seen_programs = {}  # To track unique school-program combinations

    for program in data:
        school_name = program['school']
        program_name = program['program']
        key = (school_name, program_name)
        
        # Initialize entry levels set for this program if not seen before
        if key not in seen_programs:
            seen_programs[key] = set()
        
        for year in program['year_details']:
            if year in years_list:
                for intake in program['year_details'][year]:
                    if 'program_intake' in intake and intake['program_intake'] is not None:
                        if 'entry_level' in intake:
                            entry_level = intake['entry_level']
                            
                            if isinstance(entry_level, list):
                                for level in entry_level:
                                    if level is not None:
                                        seen_programs[key].add(level)
                            else:
                                if entry_level is not None:
                                    seen_programs[key].add(entry_level)

    # Create a lookup dictionary for O(1) access
    entry_levels_lookup = {
        key: list(entry_levels) for key, entry_levels in seen_programs.items()
    }

    # Add entry_levels to each program
    for program in data:
        key = (program['school'], program['program'])
        program['entry_levels'] = entry_levels_lookup.get(key, [])

    save_json_file("data/programs/programs.json", data)
    print("✅ Added entry levels, saved to programs/programs.json")
    return data