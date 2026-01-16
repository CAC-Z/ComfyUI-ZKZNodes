import torch
from PIL import Image
import numpy as np
import comfy.utils

class CropBlackAndWhiteBordersNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "black_threshold": ("INT", {"default": 10, "min": 0, "max": 255, "step": 1}),  # 黑色阈值
                "white_threshold": ("INT", {"default": 245, "min": 0, "max": 255, "step": 1}),  # 白色阈值
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "crop_borders"
    CATEGORY = "ZKZ"

    def crop_borders(self, image, black_threshold=10, white_threshold=245):
        # 将输入的张量转换为PIL图像
        image = image.squeeze(0).numpy()  # 去掉批次维度并转换为numpy数组
        image = (image * 255).astype(np.uint8)  # 将值从[0, 1]转换为[0, 255]
        pil_image = Image.fromarray(image, mode="RGB")  # 转换为PIL图像

        # 将图像转换为灰度图以便检测黑色和白色区域
        grayscale_image = pil_image.convert("L")
        grayscale_array = np.array(grayscale_image)

        # 初始化裁剪区域
        left, top, right, bottom = 0, 0, grayscale_array.shape[1], grayscale_array.shape[0]

        # 检查上边缘（黑色或白色）
        while top < bottom and (np.all(grayscale_array[top, :] <= black_threshold) or np.all(grayscale_array[top, :] >= white_threshold)):
            top += 1

        # 检查下边缘（黑色或白色）
        while bottom > top and (np.all(grayscale_array[bottom - 1, :] <= black_threshold) or np.all(grayscale_array[bottom - 1, :] >= white_threshold)):
            bottom -= 1

        # 检查左边缘（黑色或白色）
        while left < right and (np.all(grayscale_array[:, left] <= black_threshold) or np.all(grayscale_array[:, left] >= white_threshold)):
            left += 1

        # 检查右边缘（黑色或白色）
        while right > left and (np.all(grayscale_array[:, right - 1] <= black_threshold) or np.all(grayscale_array[:, right - 1] >= white_threshold)):
            right -= 1

        # 如果检测到黑色或白色边框，裁剪图像
        if top > 0 or bottom < grayscale_array.shape[0] or left > 0 or right < grayscale_array.shape[1]:
            cropped_image = pil_image.crop((left, top, right, bottom))
        else:
            cropped_image = pil_image  # 没有黑色或白色边框，不裁剪

        # 将裁剪后的图像转换回张量
        cropped_image_np = np.array(cropped_image).astype(np.float32) / 255.0  # 转换为[0, 1]范围
        cropped_image_tensor = torch.from_numpy(cropped_image_np).unsqueeze(0)  # 添加批次维度

        return (cropped_image_tensor,)

NODE_CLASS_MAPPINGS = {
    "CropBlackAndWhiteBordersNode": CropBlackAndWhiteBordersNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CropBlackAndWhiteBordersNode": "裁剪黑白边框"
}