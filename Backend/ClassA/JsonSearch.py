# import json
# from rapidfuzz import process, fuzz

# class JsonSearchClass:
#     def fuzzy_search(locations, query, limit=10, score_cutoff=70):
#         # Extract just the names for searching
#         names = [loc["locationName"] for loc in locations]

#         # Find best matches
#         matches = process.extract(
#             query,
#             names,
#             scorer=fuzz.WRatio,
#             limit=limit,
#             score_cutoff=score_cutoff  # only matches >= score_cutoff
#         )

#         # Collect the full JSON objects for matched names
#         results = []
#         for name, score, idx in matches:
#             if score >= score_cutoff:  # filter again just to be sure
#                 results.append({
#                     "match_score": score,
#                     "data": locations[idx]
#                 })

#         return results


#     # if __name__ == "__main__":
#     #     # Load JSON directly from file
#     #     json_path = "india_ingris_data.json"
#     #     with open(json_path, "r", encoding="utf-8") as f:
#     #         locations = json.load(f)

#     #     # Ask user input
#     #     query = input("Enter location name to search: ")

#     #     results = fuzzy_search(locations, query, limit=10, score_cutoff=70)

#     #     if results:
#     #         print("\nBest Matches (score >= 70):\n")
#     #         for r in results:
#     #             print(json.dumps(r, indent=2, ensure_ascii=False))
#     #     else:
#     #         print("No close matches found with score >= 70.")




import json
from rapidfuzz import process, fuzz

class JsonSearchClass:
    @staticmethod
    def search_by_location_name(locations, query, score_cutoff=70):
        # Try exact match first
        for loc in locations:
            if loc["locationName"].lower() == query.lower():
                return loc   # return full JSON of exact match

        # If no exact match, fallback to fuzzy search
        names = [loc["locationName"] for loc in locations]
        match = process.extractOne(
            query,
            names,
            scorer=fuzz.WRatio,
            score_cutoff=score_cutoff
        )

        if match:  # if fuzzy match found
            name, score, idx = match
            return locations[idx]

        return None   # if no match at all
