import json
import os
import random
import shutil
from typing import Dict, List, Any, Tuple


def load_data(input_file: str) -> List[Dict[str, Any]]:
    with open(input_file, "r", encoding="utf-8") as f:
        specialization = json.load(f)
    print(f"Loaded {len(specialization)} programs")
    return specialization


def create_document(specialization: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    specialization_name = specialization.get("specialization")
    school = specialization.get("school")
    school_type = specialization.get("school_type")
    field = specialization.get("field")
    program = specialization.get("program")
    program_id = specialization.get("program_id")
    program_type = specialization.get("program_type")
    year = specialization.get("year")
    intake = specialization.get("intake")
    campus = specialization.get("campus")
    language = specialization.get("language")
    alternance = specialization.get("alternance")
    price = specialization.get("price")
    duration = specialization.get("duration")
    entry_level = specialization.get("entry_level")
    accreditations = specialization.get("school_accreditations", [])
    school_rank = specialization.get("school_rank")
    markdown_template = f"""
# {specialization_name}

## School Information
- **School**: {school}
- **School Type**: {school_type}
- **Field**: {field}
- **School Rank**: {school_rank}
- **Accreditations**: {', '.join(accreditations) if accreditations else 'N/A'}

- **Specialization**: {specialization_name}
- **Duration**: {duration} year(s)
- **Entry Level**: {', '.join(entry_level) if entry_level else 'N/A'}

## Practical Information
- **Campus Location(s)**: {', '.join(campus) if campus else 'N/A'}
- **Language of Instruction**: {language}
- **Intake Period**: {intake}
- **Tuition Fee**: €{price:,.0f}
- **Alternance**: {alternance}

    --------End of specialization--------


    """
    # Process language into boolean keys
    French = False
    English = False
    Both = False
    Mix = False

    if language:

        if "French" in language:
            French = True
        if "English" in language:
            English = True
        if "Both" in language:
            Both = True
        if "Mix" in language:
            Mix = True

    if school_rank == "un ranked":
        school_rank = 50
    entry_levels = ["BAC","BAC1","BAC2","BAC3","BAC4","BAC5"]
    spec_entry_levels_dict = {}
    for entry_level in specialization.get("entry_level", []):
            if entry_level in entry_levels:
                spec_entry_levels_dict[entry_level] = True

    document = {
        "page_content": markdown_template,
        "metadata": {
            "program_id": program_id,
            "program_type": program_type,
            "school_type": school_type,
            "school_name": school,
            "price": price,
            "campuses": str(campus),
            "French": French,
            "English": English,
            "Both": Both,
            "Mix": Mix,
            "primos_arrivant": specialization.get("primos_arrivant", False),
            "school_rank": school_rank,
        } | spec_entry_levels_dict,
    }
    return document, markdown_template


def specialization_md_generator(
    input_file: str = "data/specialisation_data/specializations.json",
    output_file: str = "data/chroma_documents/chroma_documents_specializations.json",
) -> Tuple[Dict[str, Any], str]:
    specializations = load_data(input_file)

    documents = []
    markdowns = []

    for specialization in specializations:
        document, markdown_template = create_document(specialization)
        documents.append(document)
        markdowns.append(markdown_template)

    # remove and recreate the dir
    shutil.rmtree("data/markdown_generators/specializations_mds", ignore_errors=True)
    os.makedirs("data/markdown_generators/specializations_mds", exist_ok=True)

    # save documents to a json file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    # save random 5 markdowns to separate files in the "specializations_mds"
    for _ in range(5):
        markdown = random.choice(markdowns)
        # save each markdown to a separate file in the "specializations_mds" directory
        with open(
            f"data/markdown_generators/specializations_mds/{random.randint(1, 10000)}_markdown.md",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(markdown)
    return documents
