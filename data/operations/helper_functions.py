from difflib import SequenceMatcher
import unicodedata
from classification_rules import CLASSIFICATION_RULES
import json
import re
import os


def read_json_file(file_name):
    with open(file_name, "rb") as file:
        return json.load(file)


def save_json_file(file_name, data):
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def classify_program(name):
    name_lower = name.lower()
    for category, keywords in CLASSIFICATION_RULES.items():
        if any(keyword.strip().lower() in name_lower for keyword in keywords):
            return category
    return "Other"


def add_specializations_and_prices(data):
    """
    Extract all specializations from year data and add them to a top-level 'specializations' key
    """
    for entry in data:

        # Extract all specializations
        specializations = []
        prices = []

        for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
            if year_key in entry:
                for year_data in entry[year_key]:

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

    return data


def strip_accents(text):
    """Normalize unicode to NFKD form and filter out combining diacritical marks."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def normalize_name(name):
    """
    Normalize name by removing accents, special characters and extra spaces.
    """    
    # Remove accents using strip_accents
    normalized = strip_accents(name)
    
    # Lowercase and remove hyphens, parentheses, brackets
    normalized = normalized.lower()
    normalized = normalized.replace('-', ' ').replace('(', ' ').replace(')', ' ')
    normalized = normalized.replace('[', ' ').replace(']', ' ')
    
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    
    return normalized


def simple_fuzzy_match(text1, text2):
    text1 = strip_accents(text1).lower().strip()
    text2 = strip_accents(text2).lower().strip()
    return SequenceMatcher(None, text1, text2).ratio()


def remove_emojis(text):
    return re.sub(r"[\U00010000-\U0010FFFF]", "", str(text))
