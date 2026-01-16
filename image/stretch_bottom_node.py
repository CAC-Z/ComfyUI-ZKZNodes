import torch
from PIL import Image
import numpy as np

# 复用image_processor.py中的辅助函数
from .image_processor import tensor_to_pil, pil_to_tensor

class StretchBottomNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "stretch_pct": ("FLOAT", {"default": 20.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "allow_RGBA_output": (["false", "true"], {"default": "true"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "stretch_images"
    CATEGORY = "ZKZ/Image"

    def stretch_images(self, images, stretch_pct, allow_RGBA_output):
        output_images = []
        for i in range(images.shape[0]):
            pil_img = tensor_to_pil(images[i])
            stretched = self.stretch_bottom(pil_img, stretch_pct)
            tensor_img = pil_to_tensor(stretched, allow_RGBA_output == "true")
            output_images.append(tensor_img)
        output_images_tensor = torch.cat(output_images, dim=0)
        return (output_images_tensor,)

    @staticmethod
    def stretch_bottom(img: Image.Image, pct: float) -> Image.Image:
        if pct <= 0:
            return img.copy()
        width, height = img.size
        extra_pixels = int(round(height * pct / 100.0))
        if extra_pixels == 0:
            return img.copy()
        bottom_row = img.crop((0, height - 1, width, height))
        stretched = bottom_row.resize((width, extra_pixels), Image.NEAREST)
        new_img = Image.new("RGBA", (width, height + extra_pixels), (0, 0, 0, 0))
        new_img.paste(img, (0, 0))
        new_img.paste(stretched, (0, height))
        return new_img

NODE_CLASS_MAPPINGS = {
    "StretchBottomNode": StretchBottomNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StretchBottomNode": "图像底部拉伸"
} 
