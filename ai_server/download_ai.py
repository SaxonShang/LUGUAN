# download.py
"""
Download Stable Diffusion models via Hugging Face Diffusers.
Choose between:
  - StableDiffusionPipeline (text2img)
  - StableDiffusionImg2ImgPipeline (img2img)

Usage:
  1) pip install diffusers transformers accelerate safetensors torch --upgrade
  2) Uncomment one pipeline block in main() (text2img or img2img).
  3) Run: python download.py

Model repos:
  - runwayml/stable-diffusion-v1-5
  - stabilityai/stable-diffusion-2-1
  - andite/anything-v4.0
  - dreamlike-art/dreamlike-photoreal-2.0
  - prompthero/openjourney
  - XpucT/Deliberate
  - stabilityai/stable-diffusion-xl-base-0.9  (beta, needs recent diffusers + lots of VRAM)
"""

import torch

# Import BOTH pipelines
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionImg2ImgPipeline
)

def download_model_text2img(model_id: str, save_path: str):
    """
    Download a model for text-to-image tasks.
    """
    print(f"🚀 Downloading (text2img) '{model_id}' ...")
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16
    ).to("cuda")
    pipe.save_pretrained(save_path)
    print(f"✅ (text2img) Model '{model_id}' saved to '{save_path}'")

def download_model_img2img(model_id: str, save_path: str):
    """
    Download a model for image-to-image tasks.
    (Same checkpoint, but loaded with Img2ImgPipeline.)
    """
    print(f"🚀 Downloading (img2img) '{model_id}' ...")
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16
    ).to("cuda")
    pipe.save_pretrained(save_path)
    print(f"✅ (img2img) Model '{model_id}' saved to '{save_path}'")


def main():
    """
    Uncomment the model + pipeline block you want to download.
    Comment out the rest.
    """

    # -----------------------------------------------------------------
    # Example #1: Stable Diffusion 1.5, text2img
    # -----------------------------------------------------------------
    #model_id = "runwayml/stable-diffusion-v1-5"
    #save_path = "./ai_server/models/sd_v1_5"
    #download_model_img2img(model_id, save_path)

    # -----------------------------------------------------------------
    # Example #2: Stable Diffusion 2.1, text2img
    # -----------------------------------------------------------------
    #model_id = "stabilityai/stable-diffusion-2-1"
    #save_path = "./ai_server/models/sd_2_1"
    #download_model_img2img(model_id, save_path)

    # -----------------------------------------------------------------
    # Example #3: Dreamlike Photoreal 2.0, text2img
    # -----------------------------------------------------------------
    #model_id = "dreamlike-art/dreamlike-photoreal-2.0"
    #save_path = "./ai_server/models/dreamlike_photoreal_2"
    #download_model_img2img(model_id, save_path)

    # -----------------------------------------------------------------
    # Example #4: OpenJourney, text2img
    # -----------------------------------------------------------------
    #model_id = "prompthero/openjourney"
    #save_path = "./ai_server/models/openjourney_local"
    #download_model_text2img(model_id, save_path)

if __name__ == "__main__":
    main()
