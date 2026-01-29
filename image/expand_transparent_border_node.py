import torch
from PIL import Image
import numpy as np
from .image_processor import tensor_to_pil, pil_to_tensor

class ExpandTransparentBorderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "expand_top": ("INT", {"default": 0, "min": 0, "max": 1024, "step": 1}),
                "expand_bottom": ("INT", {"default": 0, "min": 0, "max": 1024, "step": 1}),
                "expand_left": ("INT", {"default": 0, "min": 0, "max": 1024, "step": 1}),
                "expand_right": ("INT", {"default": 0, "min": 0, "max": 1024, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("expanded_image", "expanded_mask")
    FUNCTION = "expand_border"
    CATEGORY = "ZKZ/Image Tools"

    def expand_border(self, image, expand_top, expand_bottom, expand_left, expand_right):
        pil_img = tensor_to_pil(image[0])  # 假设输入为单张图像
        w, h = pil_img.size
        new_w = w + expand_left + expand_right
        new_h = h + expand_top + expand_bottom
        # 创建新的全透明画布
        new_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
        # 粘贴原图到新画布
        new_img.paste(pil_img, (expand_left, expand_top))
        # 转回tensor
        expanded_tensor = pil_to_tensor(new_img, allow_rgba=True)
        # 生成mask
        alpha_np = np.array(new_img.split()[-1]).astype(np.float32) / 255.0  # [H, W]
        mask_tensor = torch.from_numpy(alpha_np).unsqueeze(0).unsqueeze(0)  # [1, 1, H, W]
        return (expanded_tensor, mask_tensor)

NODE_CLASS_MAPPINGS = {
    "ExpandTransparentBorderNode": ExpandTransparentBorderNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExpandTransparentBorderNode": "扩展透明边"
} 
