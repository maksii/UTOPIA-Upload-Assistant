import os
import glob
import base64
import requests

from src.image_upload_providers.base_provider import ImageHostProvider

class LensDumpProvider(ImageHostProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    def upload(self, image_path):
        url = "https://lensdump.com/api/1/upload"
        data = {
            'image': base64.b64encode(open(image_path, "rb").read()).decode('utf8')
        }
        headers = {
            'X-API-Key': self.api_key
        }
        
        response = requests.post(url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        response = response.json()
        return {
            'web_url': response['data'].get('medium', response['data']['image'])['url'],
            'img_url': response['data']['url_viewer'],
            'raw_url': response['data']['image']['url']
        }