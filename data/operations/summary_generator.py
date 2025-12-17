"""
Comprehensive data summary generator for educational program data.
This module provides a class-based approach to analyze and generate
detailed summaries of educational program datasets.
"""

import json
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional


class DataSummaryGenerator:
    """
    A class to generate comprehensive summaries of educational program data.

    This class provides methods to analyze various aspects of educational
    program data including program types, school types, fields, pricing,
    and specializations.
    """

    def __init__(
        self, data_path: Optional[str] = None, data: Optional[List[Dict]] = None
    ):
        """
        Initialize the DataSummaryGenerator.

        Args:
            data_path (str, optional): Path to the JSON data file
            data (List[Dict], optional): Preloaded data as a list of dictionaries

        Note:
            Either data_path or data must be provided, not both.
        """
        if data_path and data:
            raise ValueError("Provide either data_path or data, not both")
        if not data_path and not data:
            raise ValueError("Either data_path or data must be provided")

        if data_path:
            self.data_path = data_path
            self.data = self._load_data()
        else:
            self.data = data
            self.data_path = None

        self.total_programs = len(self.data)

    def _load_data(self) -> List[Dict]:
        """Load data from JSON file."""
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_basic_statistics(self) -> Dict[str, Any]:
        """
        Get basic statistics about the dataset.

        Returns:
            Dict containing total programs and unique schools count
        """
        unique_schools = len(set([item["school"] for item in self.data]))
        return {"total_programs": self.total_programs, "unique_schools": unique_schools}

    def get_program_type_distribution(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze program type distribution.

        Returns:
            Dict with program types as keys and count/percentage as values
        """
        program_types = [
            item.get("program_type", "Not specified") for item in self.data
        ]
        program_type_counts = Counter(program_types)

        distribution = {}
        for prog_type, count in program_type_counts.items():
            if prog_type:  # Skip empty values
                percentage = (count / self.total_programs) * 100
                distribution[prog_type] = {"count": count, "percentage": percentage}

        return dict(
            sorted(distribution.items(), key=lambda x: x[1]["count"], reverse=True)
        )

    def get_school_type_distribution(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze school type distribution.

        Returns:
            Dict with school types as keys and count/percentage as values
        """
        school_types = [item.get("school_type", "Not specified") for item in self.data]
        school_type_counts = Counter(school_types)

        distribution = {}
        for school_type, count in school_type_counts.items():
            if school_type:  # Skip empty values
                percentage = (count / self.total_programs) * 100
                distribution[school_type] = {"count": count, "percentage": percentage}

        return dict(
            sorted(distribution.items(), key=lambda x: x[1]["count"], reverse=True)
        )

    def get_field_distribution(self, top_n: int = 10) -> Dict[str, Dict[str, float]]:
        """
        Analyze field distribution.

        Args:
            top_n (int): Number of top fields to return

        Returns:
            Dict with top N fields as keys and count/percentage as values
        """
        fields = [item.get("field", "Not specified") for item in self.data]
        field_counts = Counter(fields)

        distribution = {}
        for field, count in field_counts.most_common(top_n):
            if field:  # Skip empty values
                percentage = (count / self.total_programs) * 100
                distribution[field] = {"count": count, "percentage": percentage}

        return distribution

    def _parse_price_range(self, price_range: str) -> Optional[Tuple[int, int]]:
        """
        Parse price range string into min and max values.

        Args:
            price_range (str): Price range string like "€9000-€12000" or "€9000"

        Returns:
            Tuple of (min_price, max_price) or None if parsing fails
        """
        if not price_range or price_range == "Price not available":
            return None

        try:
            if "-" in price_range:
                # Range like "€9000-€12000"
                parts = price_range.replace("€", "").split("-")
                min_val = int(parts[0])
                max_val = int(parts[1].replace("€", ""))
                return (min_val, max_val)
            else:
                # Single price like "€9000"
                price_val = int(price_range.replace("€", ""))
                return (price_val, price_val)
        except:
            return None

    def get_price_analysis(self) -> Dict[str, Any]:
        """
        Analyze pricing information.

        Returns:
            Dict containing comprehensive price analysis
        """
        programs_with_prices = sum(
            1
            for item in self.data
            if item.get("price_range") and item["price_range"] != "Price not available"
        )
        programs_without_prices = self.total_programs - programs_with_prices

        result = {
            "programs_with_prices": programs_with_prices,
            "programs_without_prices": programs_without_prices,
            "percentage_with_prices": (programs_with_prices / self.total_programs)
            * 100,
            "percentage_without_prices": (programs_without_prices / self.total_programs)
            * 100,
        }

        if programs_with_prices > 0:
            # Extract numeric values from price_range
            price_data = []
            for item in self.data:
                parsed_price = self._parse_price_range(item.get("price_range", ""))
                if parsed_price:
                    price_data.append(parsed_price)

            if price_data:
                min_prices = [p[0] for p in price_data]
                max_prices = [p[1] for p in price_data]

                result.update(
                    {
                        "min_price": min(min_prices),
                        "max_price": max(max_prices),
                        "avg_min_price": sum(min_prices) / len(min_prices),
                        "avg_max_price": sum(max_prices) / len(max_prices),
                        "price_distribution": {
                            "budget": {
                                "count": sum(1 for p in min_prices if p < 10000),
                                "threshold": "< €10,000",
                            },
                            "mid_range": {
                                "count": sum(
                                    1 for p in min_prices if 10000 <= p <= 20000
                                ),
                                "threshold": "€10,000-€20,000",
                            },
                            "premium": {
                                "count": sum(1 for p in min_prices if p > 20000),
                                "threshold": "> €20,000",
                            },
                        },
                    }
                )

                # Add percentages to price distribution
                total_priced = len(min_prices)
                for category in result["price_distribution"].values():
                    category["percentage"] = (category["count"] / total_priced) * 100

        return result

    def get_specialization_analysis(self) -> Dict[str, Any]:
        """
        Analyze specialization information.

        Returns:
            Dict containing comprehensive specialization analysis
        """
        programs_with_specializations = sum(
            1
            for item in self.data
            if item.get("specializations")
            and isinstance(item["specializations"], list)
            and len(item["specializations"]) > 0
            and item["specializations"] != "no specializations"
        )

        result = {
            "programs_with_specializations": programs_with_specializations,
            "programs_without_specializations": self.total_programs
            - programs_with_specializations,
            "percentage_with_specializations": (
                programs_with_specializations / self.total_programs
            )
            * 100,
            "percentage_without_specializations": (
                (self.total_programs - programs_with_specializations)
                / self.total_programs
            )
            * 100,
        }

        if programs_with_specializations > 0:
            # Calculate specialization counts
            specialization_counts = [
                len(item["specializations"])
                for item in self.data
                if item.get("specializations")
                and isinstance(item["specializations"], list)
                and item["specializations"] != "no specializations"
            ]

            if specialization_counts:
                avg_spec_count = sum(specialization_counts) / len(specialization_counts)
                max_spec_count = max(specialization_counts)

                result.update(
                    {
                        "avg_specializations_per_program": avg_spec_count,
                        "max_specializations_per_program": max_spec_count,
                    }
                )

                # Find program with most specializations
                most_spec_program = next(
                    (
                        item
                        for item in self.data
                        if item.get("specializations")
                        and isinstance(item["specializations"], list)
                        and len(item["specializations"]) == max_spec_count
                    ),
                    None,
                )

                if most_spec_program:
                    result["program_with_most_specializations"] = {
                        "program": most_spec_program["program"],
                        "school": most_spec_program["school"],
                        "specialization_count": max_spec_count,
                    }

                # Collect all specializations
                all_specializations = []
                for item in self.data:
                    specs = item.get("specializations")
                    if (
                        specs
                        and isinstance(specs, list)
                        and specs != "no specializations"
                    ):
                        all_specializations.extend(specs)

                if all_specializations:
                    spec_counter = Counter(all_specializations)
                    result["top_specializations"] = dict(spec_counter.most_common(10))

        return result

    def get_top_schools(self, top_n: int = 5) -> Dict[str, int]:
        """
        Get top schools by number of programs.

        Args:
            top_n (int): Number of top schools to return

        Returns:
            Dict with school names as keys and program counts as values
        """
        schools = [item["school"] for item in self.data]
        school_counts = Counter(schools)
        return dict(school_counts.most_common(top_n))

    def generate_complete_summary(self, print_summary: bool = True) -> Dict[str, Any]:
        """
        Generate a complete summary of all analyses.

        Args:
            print_summary (bool): Whether to print the summary to console

        Returns:
            Dict containing all analysis results
        """
        summary = {
            "basic_statistics": self.get_basic_statistics(),
            "program_type_distribution": self.get_program_type_distribution(),
            "school_type_distribution": self.get_school_type_distribution(),
            "field_distribution": self.get_field_distribution(),
            "price_analysis": self.get_price_analysis(),
            "specialization_analysis": self.get_specialization_analysis(),
            "top_schools": self.get_top_schools(),
        }

        if print_summary:
            self._print_summary(summary)

        return summary

    def _print_summary(self, summary: Dict[str, Any]):
        """Print formatted summary to console."""
        print("� COMPREHENSIVE DATA SUMMARY AFTER TRANSFORMATIONS")
        print("=" * 70)

        # Basic statistics
        basic_stats = summary["basic_statistics"]
        print(f"📊 GENERAL STATISTICS:")
        print(f"Total number of programs: {basic_stats['total_programs']}")
        print(f"Number of unique schools: {basic_stats['unique_schools']}")

        # Program type distribution
        print(f"\n📚 PROGRAM TYPE DISTRIBUTION:")
        for prog_type, data in summary["program_type_distribution"].items():
            print(f"{prog_type}: {data['count']} programs ({data['percentage']:.1f}%)")

        # School type distribution
        print(f"\n🏫 SCHOOL TYPE DISTRIBUTION:")
        for school_type, data in summary["school_type_distribution"].items():
            print(
                f"{school_type}: {data['count']} programs ({data['percentage']:.1f}%)"
            )

        # Field distribution
        print(f"\n🔬 TOP 10 FIELDS:")
        for field, data in summary["field_distribution"].items():
            print(f"{field}: {data['count']} programs ({data['percentage']:.1f}%)")

        # Price analysis
        price_analysis = summary["price_analysis"]
        print(f"\n💰 PRICE INFORMATION:")
        print(
            f"Programs with price information: {price_analysis['programs_with_prices']} ({price_analysis['percentage_with_prices']:.1f}%)"
        )
        print(
            f"Programs without price information: {price_analysis['programs_without_prices']} ({price_analysis['percentage_without_prices']:.1f}%)"
        )

        if "min_price" in price_analysis:
            print(f"\n💸 PRICE RANGE ANALYSIS:")
            print(f"Minimum price: €{price_analysis['min_price']:,}")
            print(f"Maximum price: €{price_analysis['max_price']:,}")
            print(f"Average minimum price: €{price_analysis['avg_min_price']:,.0f}")
            print(f"Average maximum price: €{price_analysis['avg_max_price']:,.0f}")

            print(f"\n📊 PRICE DISTRIBUTION:")
            price_dist = price_analysis["price_distribution"]
            print(
                f"Budget ({price_dist['budget']['threshold']}): {price_dist['budget']['count']} programs ({price_dist['budget']['percentage']:.1f}%)"
            )
            print(
                f"Mid-range ({price_dist['mid_range']['threshold']}): {price_dist['mid_range']['count']} programs ({price_dist['mid_range']['percentage']:.1f}%)"
            )
            print(
                f"Premium ({price_dist['premium']['threshold']}): {price_dist['premium']['count']} programs ({price_dist['premium']['percentage']:.1f}%)"
            )

        # Specialization analysis
        spec_analysis = summary["specialization_analysis"]
        print(f"\n🎯 SPECIALIZATION INFORMATION:")
        print(
            f"Programs with specializations: {spec_analysis['programs_with_specializations']} ({spec_analysis['percentage_with_specializations']:.1f}%)"
        )
        print(
            f"Programs without specializations: {spec_analysis['programs_without_specializations']} ({spec_analysis['percentage_without_specializations']:.1f}%)"
        )

        if "avg_specializations_per_program" in spec_analysis:
            print(f"\n🔢 SPECIALIZATIONS PER PROGRAM:")
            print(
                f"Average number of specializations: {spec_analysis['avg_specializations_per_program']:.1f}"
            )
            print(
                f"Maximum specializations for a single program: {spec_analysis['max_specializations_per_program']}"
            )

            if "program_with_most_specializations" in spec_analysis:
                most_spec = spec_analysis["program_with_most_specializations"]
                print(f"\n🏆 PROGRAM WITH MOST SPECIALIZATIONS:")
                print(f"Program: {most_spec['program']}")
                print(f"School: {most_spec['school']}")
                print(f"Number of specializations: {most_spec['specialization_count']}")

            if "top_specializations" in spec_analysis:
                print(f"\n🔝 TOP 10 MOST COMMON SPECIALIZATIONS:")
                for spec, count in spec_analysis["top_specializations"].items():
                    print(f"{spec}: {count} programs")

        # Top schools
        print(f"\n🏫 TOP 5 SCHOOLS BY NUMBER OF PROGRAMS:")
        for school, count in summary["top_schools"].items():
            print(f"{school}: {count} programs")

        print("\n" + "=" * 70)
        print("✅ DATA TRANSFORMATION SUMMARY COMPLETE")


# Example usage and backward compatibility
if __name__ == "__main__":
    # Default behavior for backward compatibility
    default_data_path = "../processed/data_with_program_type.json"
    try:
        generator = DataSummaryGenerator(data_path=default_data_path)
        generator.generate_complete_summary()
    except FileNotFoundError:
        print(f"Data file not found at {default_data_path}")
        print("Please provide the correct path to your data file.")
