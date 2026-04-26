import json

class ApiShortenScript:
    def convert_json(self, input_json):
        # Parse the input JSON
        data = json.loads(input_json) if isinstance(input_json, str) else input_json
        
        # Normalize: if root is a list, wrap it into {"result": data}
        if isinstance(data, list):
            data = {"result": data}
        
        # Initialize the output structure
        output = {"result": []}
        
        # Find the Shirol entry
        for entry in data.get("result", []):
            if isinstance(entry, dict) and entry.get("locationName") == "Shirol":
                filtered_entry = {
                    "locationName": entry.get("locationName"),
                    "totalGWAvailability": entry.get("totalGWAvailability"),
                    "stageOfExtraction": entry.get("stageOfExtraction"),
                    "category": entry.get("category"),
                    "rechargeData": entry.get("rechargeData"),
                    "draftData": entry.get("draftData"),
                    "availabilityForFutureUse": entry.get("availabilityForFutureUse"),
                    "gwlevelData": entry.get("gwlevelData")
                }
                output["result"].append(filtered_entry)
                break
        
        return output
