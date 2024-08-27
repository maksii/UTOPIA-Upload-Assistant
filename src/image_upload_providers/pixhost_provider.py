import os
import glob
import base64
import requests

from src.image_upload_providers.base_provider import ImageHostProvider

class PiXhostProvider(ImageHostProvider):
    def __init__(self):
        pass
    
    def upload(self, image_path):
        url = "https://api.pixhost.to/images"
        data = {
            'content_type': '0',
            'max_th_size': 350,
        }
        files = {
            'img': ('file-upload[0]', open(image_path, 'rb')),
        }
        
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        response = response.json()
        return {
            'web_url': response['th_url'].replace('https://t', 'https://img').replace('/thumbs/', '/images/'),
            'img_url': response['th_url'],
            'raw_url': response['show_url']
        }