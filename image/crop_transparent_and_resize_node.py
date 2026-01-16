import torch
from PIL import Image
import numpy as np

class CropTransparentAndResizeNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "max_size": ("INT", {"default": 512, "min": 1, "max": 4096, "step": 1}),
                "margin": ("INT", {"default": 0, "min": 0, "max": 500, "step": 1}),
                "resize_mode": (["fit_longest", "fit_and_pad"], {"default": "fit_longest"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "crop_and_resize"
    CATEGORY = "ZKZ/Image"

    def crop_and_resize(self, image, max_size, margin=0, resize_mode="fit_longest"):
        # 将输入的张量转换为PIL图像
        image_tensor = image.clone()
        image = image.squeeze(0).numpy()
        image = (image * 255).astype(np.uint8)
        pil_image = Image.fromarray(image, mode="RGBA")

        if pil_image.mode != 'RGBA':
            raise ValueError("输入图像必须包含透明度通道（RGBA模式）。")

        # 裁剪透明边
        bbox = pil_image.getbbox()
        if bbox:
            left, upper, right, lower = bbox
            left = max(0, left - margin)
            upper = max(0, upper - margin)
            right = min(pil_image.width, right + margin)
            lower = min(pil_image.height, lower + margin)
            cropped_image = pil_image.crop((left, upper, right, lower))
        else:
            cropped_image = pil_image

        # 缩放最长边为max_size，保持比例
        width, height = cropped_image.size
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        resized_image = cropped_image.resize((new_width, new_height), Image.LANCZOS)

        if resize_mode == "fit_and_pad":
            # 自动保持原图像的对齐方式
            pad_w = max_size - new_width
            pad_h = max_size - new_height
            # 计算原图在裁剪前的相对位置
            # 以裁剪框与原图的边界关系判断对齐方式
            # 默认居中
            paste_x = pad_w // 2
            paste_y = pad_h // 2
            if bbox:
                # 如果原图像与裁剪框的某一边重合，则补边时也贴边
                if left == 0:
                    paste_x = 0
                if right == pil_image.width:
                    paste_x = pad_w
                if upper == 0:
                    paste_y = 0
                if lower == pil_image.height:
                    paste_y = pad_h
            padded = Image.new("RGBA", (max_size, max_size), (0, 0, 0, 0))
            padded.paste(resized_image, (paste_x, paste_y))
            final_image = padded
        else:
            final_image = resized_image

        # 提取mask
        alpha_np = np.array(final_image.split()[-1]).astype(np.float32) / 255.0  # [H, W]
        mask_tensor = torch.from_numpy(alpha_np).unsqueeze(0)  # [1, H, W]

        # 转回tensor
        image_np = np.array(final_image).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np).unsqueeze(0)
        return (image_tensor, mask_tensor)

NODE_CLASS_MAPPINGS = {
    "CropTransparentAndResizeNode": CropTransparentAndResizeNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CropTransparentAndResizeNode": "裁剪透明并缩放"
} 
