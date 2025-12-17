"""
Classifies French educational programs based on school type, field, duration, and name patterns.
Optimized version with reduced redundancy and improved efficiency.
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from collections import Counter


# Regex patterns for program identification
PATTERNS = {
    'pge_business': re.compile(r'\bprogramme\s+grande\s+[eé]cole\b', re.IGNORECASE), #this Matches things like: “Programme Grande École” “programme grande ecole” “Programme Grande école
    'pge_engineering': [
        re.compile(r'\bprogramme\s+grande\s+[eé]cole\b', re.IGNORECASE), #this Matches things like: “Programme Grande École”  
        re.compile(r'\bprogramme\s+ing[eé]nieur\b', re.IGNORECASE), # “Programme Ingénieur”
        re.compile(r'\bengineering\s+program\b', re.IGNORECASE), # “Engineering program”
    ],
    'cycle_ingenieur': re.compile(r'\bcycle\s+(d\'?)?ing[eé]nieur', re.IGNORECASE), # Matches "Cycle d'Ingénieur" or "Cycle Ingenieur"
    'cycle_prepa': re.compile(r'\b(preparatory\s+cycle|cycle\s+pr[eé]pa|cycle\s+pr[eé]-ing[eé]nieur|international\s+preparatory\s+cycle|pr[eé]pa\s+\w+)', re.IGNORECASE), # Matches "Cycle prépa", "Preparatory Cycle", "Prépa" followed by any word (e.g., "Prépa Art", "Prépa Animation", "Prépa Ingénieur", "Prépa Internationale")
    'master_ge': re.compile(r'\bmaster\s+.*grande\s+[eé]cole\b', re.IGNORECASE), #Matches "Master ... Grande École" — any text in between.
    'master_in_management': re.compile(r'\bmaster\s+in\s+management\b', re.IGNORECASE), #Matches "Master in Management, case insensitive" 
    'bts': re.compile(r'\bbts\b', re.IGNORECASE), #BTS
    'bba': re.compile(r'\bbba\b', re.IGNORECASE), #BBA
    'mba': re.compile(r'\bmba\b', re.IGNORECASE), #MBA
}

# Schools to exclude from classification
EXCLUDED_SCHOOLS = {"Universidad Europeaa", "GBSB Global Business School"}


def extract_duration(year_details: Dict) -> Optional[int]:
    """Extract maximum duration from year_details structure."""
    if not isinstance(year_details, dict):
        return None
    
    max_duration = None
    for year_data in year_details.values():
        if isinstance(year_data, list) and year_data:
            duration = year_data[0].get("duration") if isinstance(year_data[0], dict) else None
            if duration is not None:
                try:
                    duration = int(duration)
                    max_duration = max(max_duration or 0, duration)
                except (ValueError, TypeError):
                    continue
    
    return max_duration


def has_pattern(name: str, *keywords: str) -> bool:
    """Check if name contains any of the keywords (case-insensitive)."""
    name_lower = name.lower().strip()
    return any(kw in name_lower for kw in keywords)


def classify_bachelor_or_bba(name: str, duration: Optional[int]) -> str:
    """Classify Bachelor vs BBA based on duration (>= 4 years → BBA)."""
    if duration is not None and duration >= 4:
        return "BBA"
    return "Bachelor"


def classify_business_program(name: str, duration: Optional[int], school_type: str) -> str:
    """Classification logic for Business Schools (Grande Ecole)."""
    if PATTERNS['bts'].search(name):
        return "BTS"
    
    if has_pattern(name, "bachelor") or PATTERNS['bba'].search(name):
        return classify_bachelor_or_bba(name, duration)
    
    # MIM: Master in Management or Master ... Grande École
    if PATTERNS['master_in_management'].search(name) or PATTERNS['master_ge'].search(name):
        return "MIM"
    
    if PATTERNS['pge_business'].search(name):
        return "PGE"
    
    if has_pattern(name, "msc", "master of science", "master"):
        return "MSc"
    
    if has_pattern(name, "mastère spécialisé", "mastere specialise", "(ms)"):
        return "Mastère Spécialisé®"
    
    if has_pattern(name, "mba") or PATTERNS['mba'].search(name):
        return "MBA" if "grande ecole" in school_type.lower() else "Mastère"
    
    if has_pattern(name, "mastère", "mastere"):
        return "Other"
    
    return "Other"


def classify_engineering_program(name: str, duration: Optional[int]) -> str:
    """Classification logic for Engineering Schools (Grande Ecole)."""
    if has_pattern(name, "bachelor"):
        return "Bachelor"
    
    if PATTERNS['bts'].search(name):
        return "BTS"
    
    if PATTERNS['cycle_ingenieur'].search(name):
        return "Cycle d'Ingénieur"
    
    if any(pattern.search(name) for pattern in PATTERNS['pge_engineering']):
        return "Programme d'Ingénieur"
    
    if has_pattern(name, "master"):
        return "Master"
    
    # if has_pattern(name, "msc", "master of science", "master"):
    #     return "MSc"
    
    if has_pattern(name, "msc", "master of science"):
        return "MSc"
    
    if has_pattern(name, "mastère spécialisé", "mastere specialise", "(ms)"):
        return "Mastère Spécialisé®"
    
    if has_pattern(name, "mastère", "mastere"):
        return "Mastère"
    
    return "Other"


def classify_specialized_program(name: str, duration: Optional[int]) -> str:
    """Classification logic for Specialized Schools (École Spécialisée)."""
    if PATTERNS['bts'].search(name):
        return "BTS"
    
    if has_pattern(name, "bachelor") or PATTERNS['bba'].search(name):
        return classify_bachelor_or_bba(name, duration)
    
    if has_pattern(name, "mastère spécialisé", "mastere specialise", "(ms)"):
        return "Mastère Spécialisé®"
    
    # All other master-level programs → Mastère
    if has_pattern(name, "mba", "msc", "master of science", "mastère", "mastere", "master"):
        return "Mastère"
    
    return "Other"


def classify_no_metadata(name: str, field: str) -> Optional[str]:
    """Fallback classification for programs with missing metadata."""
    
    if has_pattern(name, "msc", "master of science"):
        return "MSc"
    
    if PATTERNS['mba'].search(name):
        return "MBA"
    
    if PATTERNS['bba'].search(name):
        return "BBA"
    
    if has_pattern(name, "bachelor"):
        return "Bachelor"
    
    if has_pattern(name, "master") and not has_pattern(name, "mastère spécialisé", "mastere specialise"):
        return "MSc"
    
    if "do not send" in field.lower():
        return "Other"
    
    return None


def classify_program(program_data: Dict[str, Any]) -> Optional[str]:
    """
    Main classification router.
    
    Priority:
    1. Special cases (specific program names)
    2. Special patterns (PGE, Cycle prépa, Cycle d'Ingénieur)
    3. Grande Ecole special cases (MBA, MS, Master with problematic fields)
    4. Route by school type → field
    5. Fallback for missing metadata
    """
    name = program_data.get("program", "")
    school = program_data.get("school", "")
    field = (program_data.get("field") or "").lower()
    school_type = (program_data.get("school_type") or "").lower().strip()
    duration = extract_duration(program_data.get("year_details", {}))
    
    # Excluded schools
    if school in EXCLUDED_SCHOOLS:
        return None
    
    # Special cases - exact program name matches
    if "TEMA Innovation et Digital Management" in name:
        return "PGE"
    if "Cycle Expert" in name:
        return "Mastère"
    if "ECAM Engineering (Master's level)" in name or "ECAM Engineering Master" in name:
        return "Master"
    if "ECAM Engineering" in name and "Master" not in name:
        return "PGE"
    if "Programme Intelligence Artificielle et Science des données Grande École" in name:
        return "PGE"
    if "CAM Arts et Métiers" in name:
        return "PGE"
    if "Programme Ingénieur d'affaires" in name:
        return "MSc"
    
    # Special patterns (override school type/field)
    if PATTERNS['pge_business'].search(name):
        return "PGE"
    if PATTERNS['cycle_prepa'].search(name):
        return "Cycle prépa"
    if PATTERNS['cycle_ingenieur'].search(name):
        return "Cycle d'Ingénieur"
    
    # Route by school type
    if school_type == "ecole spécialisée":
        return classify_specialized_program(name, duration)
    
    if school_type == "grande ecole":
        # Route by field if available
        if "business" in field:
            return classify_business_program(name, duration, school_type)
        if "engineering" in field:
            return classify_engineering_program(name, duration)
        
        # Handle Grande Ecole with problematic/missing fields
        # Check common program types that should be classified regardless of field
        if PATTERNS['bts'].search(name):
            return "BTS"
        if has_pattern(name, "bachelor") or PATTERNS['bba'].search(name):
            return classify_bachelor_or_bba(name, duration)
        if PATTERNS['mba'].search(name):
            return "MBA"
        if has_pattern(name, "mastère spécialisé", "mastere specialise", "(ms)"):
            return "Mastère Spécialisé®"
        if has_pattern(name, "master") and not PATTERNS['master_ge'].search(name) and \
           not has_pattern(name, "mastère spécialisé", "mastere specialise"):
            return "MSc"
        
        return "Other"
    
    # Fallback for missing metadata
    return classify_no_metadata(name, field)


#agents magic with stats
def generate_new_classification(
    programs_path: str = "data/programs/programs.json",
    output_path: str = "data/mappings/programs_classification_new.json",
    log_no_duration: bool = True
) -> Dict[str, str]:
    """
    Main pipeline: Load → Classify → Log → Save
    
    Returns:
        Dictionary mapping {program_name: program_type}
    """
    print(f"📂 Loading programs from {programs_path}...")
    
    programs_path_obj = Path(programs_path)
    if not programs_path_obj.exists():
        raise FileNotFoundError(f"Programs file not found: {programs_path}")
    
    with open(programs_path, 'r', encoding='utf-8') as f:
        programs = json.load(f)
    
    print(f"✅ Loaded {len(programs)} programs\n🔄 Classifying programs...")
    
    # Classification and logging
    classification = {}
    no_duration_programs = []
    ambiguous_programs = []
    
    for idx, program_data in enumerate(programs, 1):
        program_name = program_data.get("program", "UNKNOWN")
        school_type = (program_data.get("school_type") or "").lower().strip()
        field = (program_data.get("field") or "").lower()
        
        # Log programs with no duration
        if log_no_duration:
            duration = extract_duration(program_data.get("year_details", {}))
            if duration is None:
                no_duration_programs.append({
                    "program": program_name,
                    "school": program_data.get("school", "Unknown"),
                    "field": program_data.get("field", "Unknown"),
                    "school_type": program_data.get("school_type", "Unknown")
                })
        
        # Classify
        program_type = classify_program(program_data)
        classification[program_name] = program_type
        
        # Log ambiguous cases
        name_lower = program_name.lower()
        if "mba" in name_lower and "grande ecole" not in school_type:
            ambiguous_programs.append({
                "program": program_name,
                "school": program_data.get("school", "Unknown"),
                "field": field,
                "school_type": program_data.get("school_type", "Unknown"),
                "classified_as": program_type,
                "reason": "MBA in name but school_type != Grande Ecole"
            })
        
        if "cycle" in name_lower and "ingénieur" in name_lower.replace("ingenieur", "ingénieur"):
            dur = extract_duration(program_data.get("year_details", {}))
            if dur is not None and dur != 3:
                ambiguous_programs.append({
                    "program": program_name,
                    "school": program_data.get("school", "Unknown"),
                    "field": field,
                    "school_type": program_data.get("school_type", "Unknown"),
                    "duration": dur,
                    "classified_as": program_type,
                    "reason": f"Cycle Ingénieur but duration={dur} (expected 3)"
                })
        
        if idx % 100 == 0:
            print(f"   Processed {idx}/{len(programs)} programs...")
    
    print(f"✅ Classification complete!")
    
    # Save classification
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(classification, f, ensure_ascii=False, indent=4)
    print(f"\n💾 Saved classification to {output_path}")
    
    # Save logs
    if no_duration_programs:
        log_path = output_path_obj.parent / "programs_no_duration.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(no_duration_programs, f, ensure_ascii=False, indent=2)
        print(f"📝 Logged {len(no_duration_programs)} programs with no duration → {log_path}")
    
    if ambiguous_programs:
        ambiguous_path = output_path_obj.parent / "programs_ambiguous.json"
        with open(ambiguous_path, 'w', encoding='utf-8') as f:
            json.dump(ambiguous_programs, f, ensure_ascii=False, indent=2)
        print(f"📝 Logged {len(ambiguous_programs)} ambiguous programs → {ambiguous_path}")
    
    # Print statistics
    final_counts = Counter(classification.values())
    sorted_categories = sorted(final_counts.keys(), key=lambda x: (x is None, x if x is not None else ""))
    
    print(f"\n{'='*60}")
    print(f"📊 CLASSIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total unique programs: {len(classification)}")
    print(f"Total programs processed: {len(programs)}")
    print(f"Duplicate program names: {len(programs) - len(classification)}\n")
    
    for category in sorted_categories:
        count = final_counts[category]
        percentage = (count / len(classification)) * 100
        category_display = "None (missing metadata)" if category is None else category
        print(f"  {category_display:35s}: {count:4d} ({percentage:5.1f}%)")
    
    print(f"{'='*60}\n")
    
    return classification


if __name__ == "__main__":
    import sys
    
    programs_path = sys.argv[1] if len(sys.argv) > 1 else "data/programs/programs.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "data/mappings/programs_classification.json"
    
    try:
        generate_new_classification(programs_path, output_path)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
