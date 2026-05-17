from os import access

from kindwise import PlantApi
import base64
from app.config import settings
import requests


class PlantApiImpl():
    def identify_plant(self, image_url: str) -> str:
        '''Идентифицирует растение по изображению и возвращает его название.'''
        with open(image_url, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # api = PlantApi(api_key=settings.PLANT_ID_API_KEY)
        # details = ['common_names', 'taxonomy']
        # result = api.identify(encoded_image, details=details)
        
        # print(result.taxonomy)
        # if result["classification"]['suggestions']:
        #     return result["classification"]['suggestions'][0]['plant_name']
        # else:
        #     return "Unknown Plant"

        headers = {
            'Api-Key': settings.PLANT_ID_API_KEY,
        }
        
        data = {
            'images': [encoded_image],
            'classification_level': 'species',
        }

        res = requests.post("https://plant.id/api/v3/identification", json=data, headers=headers)
        print(f"Response status: {res.status_code}")
        
        response_data = res.json()
        access_token = response_data.get("access_token")
        print(f"Access token: {access_token}")
        
        # try:
        suggestions = response_data.get("result", {}).get("classification", {}).get("suggestions", [])
        if suggestions:
            species = suggestions[0].get("name", "Unknown Plant")
        else:
            species = "Unknown Plant"
        # except (KeyError, IndexError, TypeError) as e:
        #     print(f"Error extracting species: {e}")
        #     species = "Unknown Plant"
        
        print(f"Species: {species}")

        return species


    def get_plant_care_info(self, plant_name: str):
        params = {
            'key': settings.PLANT_CARE_API_KEY,
            'q': plant_name,
            'limit': 1,
            'type': 'watering'
        }

        result = requests.get(settings.PLANT_CARE_URL, params=params)
        if result.status_code == 200:
            data = result.json()
            try:
                care_info = data['data'][0]['section']['description']
                return care_info
            except KeyError:
                print("check the api answer format") # для разработки
            
        return "Care info not found"
