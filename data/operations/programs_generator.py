import json
import ast
import re
from typing import Dict, List, Any
from collections import defaultdict
import os
import random
import shutil


def generate_program_text(program: Dict[str, Any]) -> str:
    """
    Generate structured text description for a single program (for parent document).
    Based on json_to_text_converter.py logic.
    """
    text_output = []

    # Basic Program Information
    if program.get("program"):
        text_output.append(f"**Program Name:** {program['program']}\n")

    if program.get("program_id"):
        text_output.append(f"**Program ID:** {program['program_id']}\n")

    if program.get("program_type"):
        text_output.append(f"**Program Type:** {program['program_type']}\n")

    # Institution Details
    text_output.append("\n### Institution Information\n")

    if program.get("school"):
        text_output.append(f"**School:** {program['school']}\n")

    if program.get("school_type"):
        text_output.append(f"**School Type:** {program['school_type']}\n")

    if program.get("field"):
        text_output.append(f"**Field:** {program['field']}\n")

    if program.get("rank"):
        text_output.append(f"**Ranking:** {program['rank']}\n")

    if program.get("school_accreditations"):
        accreditations = ", ".join(program["school_accreditations"])
        text_output.append(f"**Accreditations:** {accreditations}\n")

    # Program Characteristics
    # text_output.append("\n### Program Details\n")

    # if program.get("specializations"):
    #     if isinstance(program["specializations"], list):
    #         specs = ", ".join(program["specializations"])
    #     else:
    #         specs = program["specializations"]
    #     text_output.append(f"**Specializations:** {specs}\n")

    # if program.get("languages"):
    #     langs = (
    #         ", ".join(program["languages"])
    #         if isinstance(program["languages"], list)
    #         else program["languages"]
    #     )
    #     text_output.append(f"**Languages of Instruction:** {langs}\n")

    # if program.get("campuses"):
    #     campuses = (
    #         ", ".join(program["campuses"])
    #         if isinstance(program["campuses"], list)
    #         else program["campuses"]
    #     )
    #     text_output.append(f"**Campus Locations:** {campuses}\n")

    if program.get("duration"):
        text_output.append(f"**Duration:** {program['duration']} years\n")

    # Financial Information
    text_output.append("\n### Financial Information\n")

    if program.get("price_range"):
        text_output.append(f"**Price Range:** {program['price_range']}\n")

    if program.get("price_average"):
        text_output.append(f"**Average Price:** €{program['price_average']:.2f}\n")

    # Year Details
    if program.get("year_details"):
        text_output.append("\n### Year-by-Year Information\n")
        year_details = program["year_details"]

        for year, details_list in sorted(year_details.items()):
            if not details_list:
                continue

            text_output.append(f"\n**{year.replace('_', ' ').title()}:**\n")

            for detail_idx, detail in enumerate(details_list, 1):
                if not isinstance(detail, dict):
                    continue

                text_output.append(f"  Option {detail_idx}:\n")

                if detail.get("program_intake"):
                    text_output.append(f"    - Intake: {detail['program_intake']}\n")
                if detail.get("intake"):
                    text_output.append(f"    - Intake: {detail['intake']}\n")
                if detail.get("campus"):
                    campus_str = (
                        ", ".join(detail["campus"])
                        if isinstance(detail["campus"], list)
                        else detail["campus"]
                    )
                    text_output.append(f"    - Campus: {campus_str}\n")
                if detail.get("price"):
                    text_output.append(f"    - Price: €{detail['price']}\n")
                if detail.get("duration"):
                    text_output.append(f"    - Duration: {detail['duration']} years\n")
                if detail.get("entry_level"):
                    entry = (
                        ", ".join(detail["entry_level"])
                        if isinstance(detail["entry_level"], list)
                        else detail["entry_level"]
                    )
                    text_output.append(f"    - Entry Level: {entry}\n")
                if detail.get("alternance"):
                    text_output.append(
                        f"    - Work-Study Option: {detail['alternance']}\n"
                    )
                if detail.get("live_in_eu"):
                    text_output.append(f"    - Live in EU: {detail['live_in_eu']}\n")
                if detail.get("not_live_in_eu"):
                    text_output.append(
                        f"    - Not Live in EU: {detail['not_live_in_eu']}\n"
                    )
                if detail.get("intake_language"):
                    text_output.append(
                        f"    - Intake Language: {detail['intake_language']}\n"
                    )
                if detail.get("language"):
                    text_output.append(f"    - Language: {detail['language']}\n")
                if detail.get("specialization"):
                    text_output.append(
                        f"    - Specialization: {detail['specialization']}\n"
                    )

    return "".join(text_output)


def load_data(data_file) -> None:
    """Load program data from JSON file."""
    with open(data_file, "r") as f:
        programs = json.load(f)
    print(f"Loaded {len(programs)} programs")
    return programs


def format_year_entries(year_name, entries):
    year_str = f"\n## 📅 {year_name.replace('_', ' ').title()} Entry\n"

    # Separate general program info from specializations
    general_entry = None
    specialization_entries = []

    for entry in entries:
        specialization = entry.get("specialization", "").strip()
        if specialization and specialization.lower() != "no specializations":
            specialization_entries.append(entry)
        else:
            general_entry = entry

    # INTAKE SECTION - Show intake information prominently
    year_str += f"\n### 📆 **INTAKE INFORMATION**\n"
    year_str += "-" * 20 + "\n"

    if general_entry:
        intake_raw = general_entry.get("program_intake") or general_entry.get(
            "intake", "[]"
        )
        try:
            if isinstance(intake_raw, list):
                intakes = ", ".join(intake_raw) if intake_raw else "N/A"
            else:
                intakes = (
                    ", ".join(ast.literal_eval(intake_raw))
                    if intake_raw != "[]"
                    else "N/A"
                )
        except Exception:
            intakes = str(intake_raw) if intake_raw else "N/A"

        year_str += f"**Intake Periods:** {intakes}\n\n"

        # Program Requirements
        year_str += "**Program Requirements:**\n"

        # Entry Level
        entry_level_raw = general_entry.get("entry_level", "[]")
        try:
            if isinstance(entry_level_raw, list):
                entry_levels = ", ".join(entry_level_raw)
            else:
                entry_levels = ", ".join(ast.literal_eval(entry_level_raw))
        except Exception:
            entry_levels = str(entry_level_raw)

        # Campuses
        campus_raw = general_entry.get("campus") or general_entry.get("campuses", "[]")
        try:
            if isinstance(campus_raw, list):
                campuses = ", ".join(campus_raw)
            else:
                campuses = ", ".join(ast.literal_eval(campus_raw))
        except Exception:
            campuses = str(campus_raw)

        # Language
        language = general_entry.get("intake_language") or general_entry.get(
            "language", "N/A"
        )

        # Price
        price_val = general_entry.get("price")
        price = f"€{price_val}" if price_val else "N/A"

        # Duration
        duration_val = general_entry.get("duration")
        duration = f"{duration_val} year(s)" if duration_val else "N/A"

        # Alternance
        alternance = general_entry.get("alternance", "Not Available")

        # Live in EU
        live_in_eu_val = general_entry.get("live_in_eu")
        live_in_eu = (
            "Yes"
            if live_in_eu_val == "Yes"
            else ("No" if live_in_eu_val == "No" else "N/A")
        )

        year_str += f"""• Entry Level: {entry_levels}
• Campuses: {campuses}  
• Language: {language}  
• Price: {price}  
• Duration: {duration}  
• Alternance: {alternance}  
• Live in EU Required: {live_in_eu}

"""

    # SPECIALIZATIONS SECTION
    if specialization_entries:
        year_str += f"### 🎯 **SPECIALIZATIONS AVAILABLE**\n"
        year_str += "-" * 40 + "\n"
        year_str += (
            f"**Total Specializations Available:** {len(specialization_entries)}\n"
        )

        for idx, entry in enumerate(specialization_entries, 1):
            specialization = entry.get("specialization", "").strip()

            year_str += f"#### **{idx}. {specialization}**\n"

            # Specialization-specific details
            spec_details = []

            # Intake for this specialization
            intake_raw = entry.get("program_intake") or entry.get("intake", "[]")
            try:
                if isinstance(intake_raw, list):
                    intakes = ", ".join(intake_raw) if intake_raw else "Same as general"
                else:
                    intakes = (
                        ", ".join(ast.literal_eval(intake_raw))
                        if intake_raw != "[]"
                        else "Same as general"
                    )
            except Exception:
                intakes = str(intake_raw) if intake_raw else "Same as general"

            spec_details.append(f"Intake: {intakes}")

            # Campuses for this specialization
            campus_raw = entry.get("campus") or entry.get("campuses", "[]")
            try:
                if isinstance(campus_raw, list):
                    campuses = ", ".join(campus_raw)
                else:
                    campuses = ", ".join(ast.literal_eval(campus_raw))
            except Exception:
                campuses = str(campus_raw)

            spec_details.append(f"Campuses: {campuses}")

            # Language for this specialization
            language = entry.get("intake_language") or entry.get("language", "N/A")
            spec_details.append(f"Language: {language}")

            # Alternance for this specialization
            alternance = entry.get("alternance", "Not Available")
            spec_details.append(f"Alternance: {alternance}")

            # Join all details with line breaks
            year_str += "  " + "\n  ".join(spec_details) + "\n\n"

    else:
        year_str += f"### 🎯 **SPECIALIZATIONS**\n"
        year_str += "**No specific specializations available for this year.**\n"

    return year_str


def generate_markdown_content(
    program: Dict[str, Any], child_parent_split: bool = False
) -> str:
    """Generate markdown content for a program using the new format.

    Args:
        program: Program data dictionary
        child_parent_split: If True, excludes year details from markdown
    """
    # Format data to match expected structure
    data = {
        "program_name": program.get("program", "Unknown Program"),
        "school_name": program.get("school", "Unknown School"),
        "program_type": program.get("program_type", "Unknown Type"),
        "school_type": program.get("school_type", "Unknown"),
        "field": program.get("field", "Unknown Field"),
        "school_rank": program.get("school_rank"),
        "price_range": program.get("price_range", "N/A"),
        "specializations": program.get("specializations", []),
        "school_accreditations": program.get("school_accreditations", []),
    }

    # Add year data from year_details
    year_details = program.get("year_details", {})
    for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
        if year_key in year_details:
            data[year_key] = year_details[year_key]

    # Extract unique campuses, languages, and alternance options from all year details
    available_campuses = set()
    available_languages = set()
    available_alternance = set()

    for year_key, year_entries in year_details.items():
        for entry in year_entries:
            # Extract campuses
            campus_raw = entry.get("campus") or entry.get("campuses", "[]")
            try:
                if isinstance(campus_raw, list):
                    available_campuses.update(campus_raw)
                else:
                    campus_list = (
                        ast.literal_eval(campus_raw) if campus_raw != "[]" else []
                    )
                    available_campuses.update(campus_list)
            except Exception:
                if campus_raw and campus_raw != "[]":
                    available_campuses.add(str(campus_raw))

            # Extract languages
            language = entry.get("intake_language") or entry.get("language", "")
            if language and language != "N/A":
                available_languages.add(language)

            # Extract alternance options
            alternance = entry.get("alternance", "")
            if alternance and alternance != "Not Available":
                available_alternance.add(alternance)

    # Convert sets to sorted lists, filtering out empty values
    available_campuses = sorted([c for c in available_campuses if c])
    available_languages = sorted([l for l in available_languages if l])
    available_alternance = sorted([a for a in available_alternance if a])

    # Convert price range format
    price_range = data.get("price_range", "N/A")
    if price_range != "N/A":
        price_range = re.sub(r"€(\d+)-€(\d+)", r"from €\1 to €\2", price_range)

    header = f"""
# 🎓 {data['program_name']}

**School:** {data['school_name']}  
**Program Type:** {data['program_type']}  
**School Type:** {data['school_type']}  
**Field:** {data['field']}  
**School Rank** {data['school_rank']}
**Price Range:** {price_range}  
**Available Intakes:** {', '.join(program.get("available_intakes", [])) if program.get("available_intakes") else "N/A"}  
**Available Campuses:** {', '.join(available_campuses) if available_campuses else "N/A"}  
**Available Languages:** {', '.join(available_languages) if available_languages else "N/A"}  
**Alternance Options:** {', '.join(available_alternance) if available_alternance else "N/A"}  
**Available Specializations:** {', '.join(data.get("specializations", [])) if isinstance(data.get("specializations"), list) else data.get("specializations", "N/A")}
**School Accreditations:** {', '.join(data.get("school_accreditations", [])) if data.get("school_accreditations") else "N/A"}
        """

    # Add the detailed program information section heading (for child-parent split)
    detailed_section = "\n## 📅 Detailed Program Information\n"

    # Conditionally include year details based on child_parent_split parameter
    if not child_parent_split:
        years = []
        # Handle year data
        for year_key in sorted([k for k in data.keys() if k.startswith("year_")]):
            if year_key in data:
                years.append(format_year_entries(year_key, data[year_key]))

        return (
            header
            + detailed_section
            + "\n".join(years)
            + f"--------End of program--------"
        )
    else:
        # For child+parent split, return only the header without year details
        return header + f"--------End of program--------"


def create_document(
    program: Dict[str, Any], child_parent_split: bool = False
) -> Dict[str, Any]:
    """Create a Document dictionary for ChromaDB."""
    school = program.get("school", "Unknown School")
    school_type = program.get("school_type", "Unknown")
    program_id = program.get("program_id", "unknown_id")
    price = program.get("price_average", "N/A")
    campuses = program.get("campuses", [])
    languages = program.get("languages", [])
    school_rank = program.get("school_rank")
    if school_rank == "un ranked":
        school_rank = 50
    # Get program type from data (fallback to extraction if not available)
    program_type = program.get("program_type")

    # Process languages into boolean keys
    French = False
    English = False
    Both = False
    Mix = False

    if languages:

        if "French" in languages:
            French = True
        if "English" in languages:
            English = True
        if "Both" in languages:
            Both = True
        if "Mix" in languages:
            Mix = True

    page_content = generate_markdown_content(program, child_parent_split)

    # Create document structure as dictionary
    entry_levels = ["BAC","BAC1","BAC2","BAC3","BAC4","BAC5"]
    entry_levels_dict = {}
    for entry_level in program.get("entry_levels"):
        if entry_level in entry_levels:
            entry_levels_dict[entry_level] = True
    
    document = {
        "page_content": page_content,
        "metadata": {
            "program_id": program_id,
            "program_type": program_type,
            "school_type": school_type,
            "school_name": school,
            "price": price,
            "campuses": str(campuses),
            "French": French,
            "English": English,
            "Both": Both,
            "Mix": Mix,
            "primos_arrivant": program.get("primos_arrivant", False),
            "school_rank": school_rank,
        } | entry_levels_dict,
    }
    return document, page_content


def program_md_generator(
    input_file: str = "data/programs/programs.json",
    output_file: str = "data/chroma_documents/chroma_documents_programs.json",
    child_parent_split: bool = False,
):
    programs = load_data(input_file)
    json_documents = []
    markdowns = []
    parent_documents = defaultdict()
    metadata_mapping = defaultdict()
    for program in programs:
        document, page_content = create_document(program, child_parent_split)

        # Generate structured text for parent document
        # program_text = generate_program_text(program)
        parent_documents[str(program.get("program_id"))] = program

        json_documents.append(document)
        markdowns.append(page_content)
        metadata_mapping[str(document["metadata"].get("program_id"))] = document[
            "metadata"
        ]

    with open("data/raw/new_tables.json", "r", encoding="utf-8") as json_file:
        schools = json.load(json_file)[0]
    # TODO: Add school logos to parent documents
    for school in schools:
        for program in parent_documents:
            if parent_documents[program]["school"] == school["school_name"]:
                parent_documents[program]["school_logo"] = school["logo_pic_link"]

    # TODO: Add program links to parent documents
    for program in programs:
        for p in parent_documents:
            if (
                parent_documents[p]["program"] == program["program"]
                and parent_documents[p]["school"] == program["school"]
            ):
                parent_documents[p]["program_link"] = program.get("program_link", "N/A")

    with open("data/parents/parent_documents.json", "w", encoding="utf-8") as json_file:
        json.dump(parent_documents, json_file, indent=4, ensure_ascii=False)

    with open("data/mappings/metadata_mapping.json", "w", encoding="utf-8") as json_file:
        json.dump(metadata_mapping, json_file, indent=4)

    shutil.rmtree("data/markdown_generators/programs_mds", ignore_errors=True)
    os.makedirs("data/markdown_generators/programs_mds", exist_ok=True)

    for _ in range(5):
        markdown = random.choice(markdowns)
        # save each markdown to a separate file in the current directory
        with open(
            f"data/markdown_generators/programs_mds/{random.randint(1, 10000)}_markdown.md",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(markdown)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_documents, f, ensure_ascii=False, indent=2)

    return json_documents


if __name__ == "__main__":
    program_md_generator()
