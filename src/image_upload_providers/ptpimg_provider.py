import os
import glob
import base64
import requests

from src.image_upload_providers.base_provider import ImageHostProvider

class PtpImgProvider(ImageHostProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    def upload(self, image_path):
        payload = {
            'format' : 'json',
            'api_key' : self.api_key # API key is obtained from inspecting element on the upload page. 
        }
        files = [('file-upload[0]', open(image_path, 'rb'))] 
        headers = { 'referer': 'https://ptpimg.me/index.php'} 
        url = "https://ptpimg.me/upload.php"
        
        response = requests.post(url, headers=headers, data=payload, files=files, timeout=30)
        response.raise_for_status()
        response = response.json()
        ptpimg_code = response[0]['code'] 
        ptpimg_ext = response[0]['ext'] 
        return {
            'web_url': f"https://ptpimg.me/{ptpimg_code}.{ptpimg_ext}" ,
            'img_url': f"https://ptpimg.me/{ptpimg_code}.{ptpimg_ext}" ,
            'raw_url': f"https://ptpimg.me/{ptpimg_code}.{ptpimg_ext}" 
        }