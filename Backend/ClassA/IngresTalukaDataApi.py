import requests
import json

class IngresTalukaDataApi:
# Global input (for now)
    # location_data = {
    #         "locationUUID": "07edc941-79d8-41cc-9624-4b4a1f7b3885",
    #         "locationName": "DHANPATGANJ",
    #         "locationType": "BLOCK",
    #         "DistrictName": "SULTANPUR",
    #         "districtUUID": "0a32cfaf-984f-4991-b8af-1b1b19ba0910",
    #         "StateName": "UTTAR PRADESH",
    #         "stateUUID": "edce8ca7-bf15-4b5e-b4c5-b10c543acd83",
    #         "categoryTotal": "safe"
    #     }


    def fetch_business_data(self, location_data):
        """
        Fetch business data from the API for a given location_data dict.
        Returns: dict (API response) or raises Exception if invalid.
        """
        url = "https://ingres.iith.ac.in/api/gec/getBusinessDataForUserOpen"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, /",
            "Origin": "https://ingres.iith.ac.in",
            "Referer": "https://ingres.iith.ac.in/gecdataonline/gis/"
        }

        payload = {
            "parentLocName": "INDIA",
            "locname": location_data["locationName"],
            "loctype": location_data["locationType"],
            "view": "admin",
            "locuuid": location_data["locationUUID"],
            "year": "2024-2025",
            "computationType": "normal",
            "component": "recharge",
            "period": "annual",
            "category": location_data["categoryTotal"],
            "mapOnClickParams": "true",
            "stateuuid": location_data.get("stateUUID"),
            "verificationStatus": 1,
            "approvalLevel": 1,
            "parentuuid": location_data.get("stateUUID")  
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        try:
            data = response.json()
        except ValueError:
            raise Exception("API returned invalid JSON")

        if not data:
            raise Exception("API returned empty response")

        return data


    # # Example usage
    # if _name_ == "_main_":
    #     business_data_result = fetch_business_data(location_data)
    #     print("Business data fetched:")
    #     print(json.dumps(business_data_result, indent=2))