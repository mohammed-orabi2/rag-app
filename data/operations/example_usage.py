"""
Example script demonstrating how to use the DataSummaryGenerator class.
"""

from summary_generator import DataSummaryGenerator
import json
import os


def main():
    """Demonstrate various ways to use the DataSummaryGenerator class."""

    # Method 1: Using data file path
    data_path = "../processed/data_with_program_type.json"

    if os.path.exists(data_path):
        print("=== Method 1: Using data file path ===")
        generator = DataSummaryGenerator(data_path=data_path)

        # Generate complete summary with console output
        summary = generator.generate_complete_summary(print_summary=True)

        print("\n=== Method 2: Individual analysis methods ===")

        # Get specific analyses without printing
        basic_stats = generator.get_basic_statistics()
        print(f"Basic stats: {basic_stats}")

        price_analysis = generator.get_price_analysis()
        print(f"Programs with pricing: {price_analysis['programs_with_prices']}")

        top_schools = generator.get_top_schools(top_n=3)
        print(f"Top 3 schools: {list(top_schools.keys())}")

    else:
        print("Data file not found. Demonstrating with sample data...")

        # Method 3: Using preloaded data
        sample_data = [
            {
                "program": "Computer Science",
                "school": "Tech University",
                "school_type": "Public",
                "program_type": "Bachelor",
                "field": "Technology",
                "price_range": "€10000-€15000",
                "specializations": ["AI", "Web Development", "Data Science"],
            },
            {
                "program": "Business Administration",
                "school": "Business School",
                "school_type": "Private",
                "program_type": "Master",
                "field": "Business",
                "price_range": "€20000",
                "specializations": ["Marketing", "Finance"],
            },
            {
                "program": "Art History",
                "school": "Art Institute",
                "school_type": "Private",
                "program_type": "Bachelor",
                "field": "Arts",
                "price_range": "Price not available",
                "specializations": [],
            },
        ]

        print("=== Method 3: Using preloaded data ===")
        generator = DataSummaryGenerator(data=sample_data)

        # Generate summary without console output
        summary = generator.generate_complete_summary(print_summary=False)

        print("Summary generated successfully!")
        print(
            f"Total programs analyzed: {summary['basic_statistics']['total_programs']}"
        )

        # Access specific parts of the summary
        program_types = summary["program_type_distribution"]
        print(f"Program types found: {list(program_types.keys())}")

        # Save summary to JSON for further analysis
        output_path = "../processed/sample_summary.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Summary saved to: {output_path}")


if __name__ == "__main__":
    main()
