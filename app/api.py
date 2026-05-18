import base64
from app.config import settings
import requests
from app.models import FrequencyEnum


class PlantApiImpl():
    def identify_plant(self, image_url: str) -> tuple[str, str, FrequencyEnum]:
        '''Идентифицирует растение по изображению и возвращает его название, описание, рекомендации по поливу'''
        with open(image_url, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        headers = {
            'Api-Key': settings.PLANT_ID_API_KEY,
        }
        
        data = {
            'images': [encoded_image],
            'classification_level': 'species',
        }

        res = requests.post("https://plant.id/api/v3/identification", json=data, headers=headers)
        
        response_data = res.json()
        access_token = response_data.get("access_token")
        
        try:
            # suggestions = response_data.get("result", {}).get("classification", {}).get("suggestions", [])
            suggestions = response_data["result"]["classification"]["suggestions"]

            species = suggestions[0].get("name", "Unknown Plant")
        except Exception as e:
            species = "Unknown Plant"

        params = {
            'details': 'description,watering'
        }

        res = requests.get(f"https://plant.id/api/v3/identification/{access_token}", params=params, headers=headers)

        try:
            detail_data = res.json()

            watering_info = detail_data["result"]["classification"]["suggestions"][0]["details"]["watering"]
            print(watering_info)
            if watering_info:
                watering_info = watering_info["min"]
            else:
                watering_info = 0

            description = detail_data["result"]["classification"]["suggestions"][0]["details"]["description"]["value"]
        except Exception as e:
            description = "No description"
            watering_info = 0

        if watering_info == 1:
            watering_info = FrequencyEnum.BIWEEKLY
        elif watering_info == 2:
            watering_info = FrequencyEnum.WEEKLY
        elif watering_info == 3:
            watering_info = FrequencyEnum.EVERY_3_DAYS
        else:
            watering_info = FrequencyEnum.NO_INFO

        return (species, description, watering_info)
