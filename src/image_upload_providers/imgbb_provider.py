import os
import glob
import base64
import requests

from src.image_upload_providers.base_provider import ImageHostProvider

class ImgBBProvider(ImageHostProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    def upload(self, image_path):
        url = "https://api.imgbb.com/1/upload"
        data = {
            'key': self.api_key,
            'image': base64.b64encode(open(image_path, "rb").read()).decode('utf8')
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        response_data = response.json()
        return {
            'web_url': response_data['data']['url_viewer'],
            'img_url': response_data['data']['image']['url'],
            'raw_url': response_data['data']['image']['url']
        }