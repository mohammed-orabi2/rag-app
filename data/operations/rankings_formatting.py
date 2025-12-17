from helper_functions import save_json_file


def get_unique_rankings(data):
    unique_rankings = set()
    for program in data:
        rank = program.get("school_rankings", [])
        try:
            if rank:
                unique_rankings.add(rank)
        except TypeError:
            continue
    return unique_rankings


def map_rankings_to_numbers(unique_rankings):
    sorted_rankings = sorted(list(unique_rankings))
    rankings_mapping = {str(rank): idx + 1 for idx, rank in enumerate(sorted_rankings)}
    save_json_file("data/mappings/rankings_mapping.json", rankings_mapping)
    return rankings_mapping


def add_rankings_numbers(data, output_path):
    unique_rankings = get_unique_rankings(data)
    rankings_mapping = map_rankings_to_numbers(unique_rankings)
    for program in data:
        try:
            program["school_rank"] = rankings_mapping[str(program["school_rankings"])]
        except:
            program["school_rank"] = "un ranked"
    save_json_file(output_path, data)
    return data
