from diffusers import StableDiffusionImg2ImgPipeline
import torch

# 下载并加载 Stable Diffusion 2.1 模型
pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
    "stabilityai/stable-diffusion-2-1",  # 新模型名称
    torch_dtype=torch.float16
).to("cuda")  # 使用 GPU
pipeline.save_pretrained("./stable_diffusion_2_1_img2img_model")  # 保存模型
print("✅ 新模型下载并保存成功！")