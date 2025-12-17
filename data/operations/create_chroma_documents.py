"""
This script converts program data into Document objects for ChromaDB storage.
Each program becomes a document with markdown content and structured metadata.
"""

import json
import ast
import re
from typing import Dict, List, Any
from langchain_core.documents import Document
from collections import defaultdict
import os


class ChromaDocumentCreator:
    """Creates ChromaDB Document objects from program data."""

    def __init__(self, data_file: str):
        """Initialize with data file path."""
        # Get script directory and go up to data directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.dirname(script_dir)  # Go up from operations to data
        self.data_file = os.path.join(self.data_dir, data_file)
        self.programs = []

    def _calculate_price_range(self, program: Dict[str, Any]) -> str:
        """Calculate price range from year_details. Logic from data_enrichers.py"""
        prices = []
        year_details = program.get("year_details", {})

        for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
            if year_key in year_details:
                for year_data in year_details[year_key]:
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
                            continue

        if prices:
            min_price = min(prices)
            max_price = max(prices)
            if min_price == max_price:
                return f"€{int(min_price)}"
            else:
                return f"€{int(min_price)}-€{int(max_price)}"
        else:
            return "Price not available"

    def load_data(self) -> None:
        """Load program data from JSON file."""
        with open(self.data_file, "r", encoding="utf-8") as f:
            self.programs = json.load(f)
        print(f"Loaded {len(self.programs)} programs")

    def format_year_entries(self, year_name, entries):
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
            campus_raw = general_entry.get("campus") or general_entry.get(
                "campuses", "[]"
            )
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
                        intakes = (
                            ", ".join(intake_raw) if intake_raw else "Same as general"
                        )
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

    def generate_markdown_content(self, program: Dict[str, Any]) -> str:
        """Generate markdown content for a program using the new format."""
        # Format data to match expected structure
        data = {
            "program_name": program.get("program", "Unknown Program"),
            "school_name": program.get("school", "Unknown School"),
            "program_type": program.get("program_type", "Unknown Type"),
            "school_type": program.get("school_type", "Unknown"),
            "field": program.get("field", "Unknown Field"),
            "rank": program.get("rank", "0"),
            "price_range": self._calculate_price_range(program),
            "specializations": program.get("specializations", []),
        }

        # Add year data from year_details
        year_details = program.get("year_details", {})
        for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
            if year_key in year_details:
                data[year_key] = year_details[year_key]

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
**Rank:** {"Not Ranked" if data.get("rank") == "0" else data.get("rank")}  
**Price Range:** {price_range}  
**Available Specializations:** {', '.join(data.get("specializations", [])) if isinstance(data.get("specializations"), list) else data.get("specializations", "N/A")}
            """

        # Add the detailed program information section heading (for child-parent split)
        detailed_section = "\n## 📅 Detailed Program Information\n"

        years = []
        # Handle year data
        for year_key in sorted([k for k in data.keys() if k.startswith("year_")]):
            if year_key in data:
                years.append(self.format_year_entries(year_key, data[year_key]))

        return (
            header
            + detailed_section
            + "\n".join(years)
            + f"--------End of program--------"
        )

    def create_document(
        self, program: Dict[str, Any], doc_id: str, json_transformation: bool = False
    ) -> Dict[str, Any]:
        """Create a Document dictionary for ChromaDB."""
        school = program.get("school", "Unknown School")
        school_type = program.get("school_type", "Unknown")

        # Get program type from data (fallback to extraction if not available)
        program_type = program.get("program_type")

        if json_transformation:
            page_content = program

        else:
            page_content = self.generate_markdown_content(program)

        # Create document structure as dictionary
        document = {
            "page_content": page_content,
            "metadata": {
                "id": doc_id,
                "program_type": program_type,
                "school_type": school_type,
                "school_name": school,
            },
        }
        return document

    def create_all_documents(self) -> List[Dict[str, Any]]:
        """Create Document objects for all programs."""
        if not self.programs:
            self.load_data()

        documents = []
        json_documents = []
        parent_documents = defaultdict()

        for i, program in enumerate(self.programs):
            doc_id = f"program_{i+1:04d}"  # e.g., program_0001, program_0002
            parent_documents[doc_id] = str(program)
            json_document = self.create_document(
                json_transformation=True, doc_id=doc_id, program=program
            )
            document = self.create_document(program, doc_id)
            documents.append(document)
            json_documents.append(json_document)

        # Use absolute paths relative to data directory
        json_output = os.path.join(
            self.data_dir, "chroma_documents", "chroma_json_documents.json"
        )
        parent_output = os.path.join(self.data_dir, "parents", "parent_documents.json")

        # Create directories if they don't exist
        os.makedirs(os.path.dirname(json_output), exist_ok=True)
        os.makedirs(os.path.dirname(parent_output), exist_ok=True)

        with open(json_output, "w", encoding="utf-8") as f:
            json.dump(json_documents, f, indent=2, ensure_ascii=False)

        print(f"Created {len(documents)} document objects")
        with open(parent_output, "w", encoding="utf-8") as f:
            json.dump(parent_documents, f, indent=2, ensure_ascii=False)
        return documents

    def save_documents_json(self, output_file: str) -> None:
        """Save documents as JSON for inspection."""
        documents = self.create_all_documents()

        # Use absolute path relative to data directory
        output_path = os.path.join(self.data_dir, output_file)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)

        print(f"Saved documents to {output_path}")


def main():
    """Main function to create ChromaDB documents."""
    data_file = "programs/programs.json"
    output_file = "chroma_documents/chroma_documents.json"

    print("🚀 Creating ChromaDB Document objects...")

    creator = ChromaDocumentCreator(data_file)

    # Create and save documents
    creator.save_documents_json(output_file)

    # Show sample documents
    print("\n📄 Sample documents:")

    print(f"\n✅ All documents saved to: {output_file}")


if __name__ == "__main__":
    main()
