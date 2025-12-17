"""
Convert programs JSON data to structured text description for LLM context.
"""

import json
import os


def convert_programs_to_text(json_file_path, output_file_path=None, max_programs=None):
    """
    Convert programs JSON data to structured text description for LLM context.

    Args:
        json_file_path: Path to the JSON file
        output_file_path: Optional path to save the text output
        max_programs: Optional limit on number of programs to process (for testing)

    Returns:
        String containing the formatted text description
    """
    # Load JSON data
    with open(json_file_path, "r", encoding="utf-8") as f:
        programs = json.load(f)

    text_output = []
    text_output.append("# EDUCATIONAL PROGRAMS DATABASE\n")
    text_output.append(
        "This dataset contains information about educational programs offered by various institutions in France.\n\n"
    )

    # Limit programs for testing if specified
    programs_to_process = programs[:max_programs] if max_programs else programs

    # Process each program
    for idx, program in enumerate(programs_to_process, 1):
        if not isinstance(program, dict):
            continue

        text_output.append(f"## PROGRAM {idx}\n")

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
        text_output.append("\n### Program Details\n")

        if program.get("specializations"):
            if isinstance(program["specializations"], list):
                specs = ", ".join(program["specializations"])
            else:
                specs = program["specializations"]
            text_output.append(f"**Specializations:** {specs}\n")

        if program.get("languages"):
            langs = (
                ", ".join(program["languages"])
                if isinstance(program["languages"], list)
                else program["languages"]
            )
            text_output.append(f"**Languages of Instruction:** {langs}\n")

        if program.get("campuses"):
            campuses = (
                ", ".join(program["campuses"])
                if isinstance(program["campuses"], list)
                else program["campuses"]
            )
            text_output.append(f"**Campus Locations:** {campuses}\n")

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
                        text_output.append(
                            f"    - Intake: {detail['program_intake']}\n"
                        )
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
                        text_output.append(
                            f"    - Duration: {detail['duration']} years\n"
                        )
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
                        text_output.append(
                            f"    - Live in EU: {detail['live_in_eu']}\n"
                        )
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

        text_output.append("\n" + "=" * 80 + "\n\n")

    # Join all text
    final_text = "".join(text_output)

    # Save to file if path provided
    if output_file_path:
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(final_text)
        print(f"✓ Text output saved to: {output_file_path}")
        print(f"✓ Total programs processed: {len(programs_to_process)}")
        print(f"✓ Output file size: {len(final_text):,} characters")

    return final_text


if __name__ == "__main__":
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "programs", "programs.json")
    output_path = os.path.join(base_dir, "programs", "programs_text_output.txt")
    test_output_path = os.path.join(base_dir, "programs", "programs_text_sample.txt")

    print("=" * 80)
    print("PROGRAM JSON TO TEXT CONVERTER")
    print("=" * 80)
    print()

    # Test with first 3 programs
    print("Testing with first 3 programs...")
    print("-" * 80)
    text_sample = convert_programs_to_text(json_path, test_output_path, max_programs=3)

    print("\nSample output (first 1500 characters):")
    print("-" * 80)
    print(text_sample[:1500])
    print("\n... [truncated]\n")

    # Ask if user wants to process all programs
    print("=" * 80)
    response = input("\nDo you want to convert ALL programs? (y/n): ").strip().lower()

    if response == "y":
        print("\nProcessing all programs...")
        print("-" * 80)
        convert_programs_to_text(json_path, output_path)
        print("\n✓ Complete! All programs have been converted to text.")
    else:
        print("\n✓ Test complete. Only sample file was generated.")

    print("\n" + "=" * 80)
