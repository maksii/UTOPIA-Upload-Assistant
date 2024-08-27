import glob
import os
from src.console import console
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn

from src.image_upload_providers.imgbb_provider import ImgBBProvider
from src.image_upload_providers.imgbox_provider import ImgBoxProvider
from src.image_upload_providers.lensdump_provider import LensDumpProvider
from src.image_upload_providers.oeimg_provider import OnlyImageProvider
from src.image_upload_providers.pixhost_provider import PiXhostProvider
from src.image_upload_providers.ptpimg_provider import PtpImgProvider
from src.image_upload_providers.ptscreens_provider import PTscreensProvider
from src.image_upload_providers.utppm_provider import UTPpmProvider


class ImageUploader:
    def __init__(self, config):
        self.config = config
        self.providers = {
            'imgbb': ImgBBProvider(config.config['DEFAULT']['imgbb_api']),
            'ptpimg':PtpImgProvider(config.config['DEFAULT']['ptpimg_api']),
            'lensdump': LensDumpProvider(config.config['DEFAULT']['lensdump_api']),
            'oeimg': OnlyImageProvider(config.config['DEFAULT']['oeimg_api']),
            'ptscreens': PTscreensProvider(config.config['DEFAULT']['ptscreens_api']),
            'utppm': UTPpmProvider(config.config['DEFAULT']['utppm_api']),
            'imgbox': ImgBoxProvider(),
            'pixhost': PiXhostProvider(),
            # Add more providers here
        }

    def get_provider(self, provider_name):
        # Retrieve provider instance by name, return None if not found
        return self.providers.get(provider_name)

    def upload_screens(self, meta):
        # Change directory to the temporary image storage location
        target_directory = os.path.join(meta['base_dir'], 'tmp', meta['uuid'])
        os.chdir(target_directory)

        # Prepare the list of images to upload
        images_to_upload = glob.glob("*.png")

        uploaded_images = []
        current_image_count = 0
        provider_index = 1
        
        with Progress(
            TextColumn("[bold green]Uploading Screens..."),
            BarColumn(),
            "[cyan]{task.completed}/{task.total}",
            TimeRemainingColumn()
        ) as progress:
            upload_task = progress.add_task(
                "[green]Uploading Screens...",
                total=len(images_to_upload)
            )
            # Attempt to upload images using available providers
            while current_image_count < len(images_to_upload) and f'img_host_{provider_index}' in self.config.config['DEFAULT']:
                provider_name = self.config.config['DEFAULT'][f'img_host_{provider_index}']
                provider = self.get_provider(provider_name)

                if not provider:
                    console.print(f"[red]Unsupported image host: {provider_name}")
                    provider_index += 1
                    continue
                for image_file in images_to_upload[current_image_count:]:
                    try:
                        # Attempt to upload the image
                        uploaded_image_data = provider.upload(image_file)
                        if uploaded_image_data:
                            uploaded_images.append(uploaded_image_data)
                            current_image_count += 1
                            progress.advance(upload_task)
                            if current_image_count >= len(images_to_upload):
                                break
                    except Exception as e:
                        console.print(f"[yellow]{provider_name} failed, trying next image host: {e}")
                        break  # Exit the loop and try the next provider

                provider_index += 1  # Move to the next provider

        if len(uploaded_images) < len(images_to_upload):
            console.print(f"[red]Not all images uploaded due to imghost errors")
        return uploaded_images 