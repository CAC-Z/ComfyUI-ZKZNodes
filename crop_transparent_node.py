import torch
from PIL import Image
import numpy as np
import comfy.utils

class CropTransparentImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "margin": ("INT", {"default": 0, "min": 0, "max": 500, "step": 1}),  # 添加边距参数
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "crop_transparent_image"
    CATEGORY = "ZKZ"

    def crop_transparent_image(self, image, margin=0):
        # 将输入的张量转换为PIL图像
        image_tensor = image.clone()  # Keep a copy of the original tensor
        image = image.squeeze(0).numpy()  # 去掉批次维度并转换为numpy数组
        image = (image * 255).astype(np.uint8)  # 将值从[0, 1]转换为[0, 255]
        pil_image = Image.fromarray(image, mode="RGBA")  # 转换为PIL图像

        # 检查图像是否有透明度
        if pil_image.mode != 'RGBA':
            raise ValueError("输入图像必须包含透明度通道（RGBA模式）。")

        # 裁剪图像
        bbox = pil_image.getbbox()
        if bbox:
            # 扩展边距
            left, upper, right, lower = bbox
            left = max(0, left - margin)
            upper = max(0, upper - margin)
            right = min(pil_image.width, right + margin)
            lower = min(pil_image.height, lower + margin)

            # 裁剪图像
            cropped_image = pil_image.crop((left, upper, right, lower))

            # 将裁剪后的图像转换回张量
            cropped_image_np = np.array(cropped_image).astype(np.float32) / 255.0  # 转换为[0, 1]范围
            cropped_image_tensor = torch.from_numpy(cropped_image_np).unsqueeze(0)  # 添加批次维度

            # 提取透明度通道作为掩码
            mask_np = np.array(cropped_image.split()[-1]).astype(np.float32) / 255.0  # 转换为[0, 1]范围
            mask_tensor = torch.from_numpy(mask_np).unsqueeze(0)  # 添加批次维度

            return (cropped_image_tensor, mask_tensor)
        else:
            # 图像没有需要裁剪的非空白部分，直接输出原图
            alpha_channel = pil_image.split()[-1]
            mask_np = np.array(alpha_channel).astype(np.float32) / 255.0
            mask_tensor = torch.from_numpy(mask_np).unsqueeze(0)

            return (image_tensor, mask_tensor)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "CropTransparentImageNode": CropTransparentImageNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CropTransparentImageNode": "裁剪透明区域"
}