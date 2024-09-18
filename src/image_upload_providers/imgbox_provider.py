import asyncio
import pyimgbox
import nest_asyncio
import os
from src.image_upload_providers.base_provider import ImageHostProvider

class ImgBoxProvider(ImageHostProvider):
    def __init__(self):
        pass

    def upload(self, image_path):
        nest_asyncio.apply()
        list = [image_path]
        return asyncio.run(self._upload_async(list))

    async def _upload_async(self, image_path):
        gallery = pyimgbox.Gallery(thumb_width=350, square_thumbs=False)
        try:
            async for submission in gallery.add(image_path):
                if not submission['success']:
                    raise Exception(f"[red]There was an error uploading to ImgBox: [yellow]{submission['error']}[/yellow][/red]")

                image_dict = {
                    'web_url': submission['thumbnail_url'],
                    'img_url': submission['web_url'],
                    'raw_url': submission['image_url']
                }
                return image_dict
        finally:
            await gallery.close()
