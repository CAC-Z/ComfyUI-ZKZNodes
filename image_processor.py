import os
from PIL import Image
import torch
import numpy as np

class ImageProcessor:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),  # Input: Batch of images
                "final_width": ("INT", {"default": 1024, "min": 1, "max": 4096}),  # Control: Final width
                "final_height": ("INT", {"default": 1024, "min": 1, "max": 4096}),  # Control: Final height
                "max_top_space": ("INT", {"default": 0, "min": 0, "max": 4096}),  # Control: Max top space
                "max_side_space": ("INT", {"default": 0, "min": 0, "max": 2048}), # Control: Max side space
                "allow_RGBA_output": (["false", "true"], {"default": "true"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "process_images"
    CATEGORY = "ZKZ"

    def process_images(self, images, final_width, final_height, max_top_space, max_side_space, allow_RGBA_output):
        """
        Processes a batch of images.
        """
        output_images = []
        output_masks = []

        for i in range(images.shape[0]):  # Iterate through the batch
            print(f"Processing image index: {i}")

            # 1. Convert tensor to PIL image
            print(f"  [tensor_to_pil] Input Tensor Shape: {images[i].shape}, Type: {images[i].dtype}") # DEBUG - Tensor Info
            pil_image_before_conversion = tensor_to_pil(images[i])
            print(f"  [tensor_to_pil] PIL Image Mode (after tensor_to_pil): {pil_image_before_conversion.mode}")  # DEBUG - Check mode
            pil_image_before_conversion.save(f"debug_1_initial_pil_{i}.png")  # Save for inspection

            image = pil_image_before_conversion # Use the saved image as input

            # 2. Process the image
            print(f"  [crop_and_resize_image] Input PIL Image Mode: {image.mode}") # Debug Mode In
            image.save(f"debug_2_crop_resize_input_{i}.png") # Save input to crop_and_resize
            image = self.crop_and_resize_image(image, final_width, final_height, max_top_space, max_side_space)
            print(f"  [crop_and_resize_image] Output PIL Image Mode: {image.mode}") # Debug Mode Out
            image.save(f"debug_3_crop_resize_output_{i}.png") # Save output of crop_and_resize


            # 3. Convert back to tensor
            print(f"  [pil_to_tensor] Input PIL Image Mode: {image.mode}") # Debug Mode In
            image.save(f"debug_6_pil_to_tensor_input_{i}.png") # Save input to pil_to_tensor
            # 生成遮罩（基于 alpha 通道）
            mask_np = np.array(image.split()[-1]).astype(np.float32) / 255.0
            mask_tensor = torch.from_numpy(mask_np).unsqueeze(0)  # (1, H, W)

            output_tensor = pil_to_tensor(image, allow_RGBA_output == "true")
            print(f"  [pil_to_tensor] Output Tensor Shape: {output_tensor.shape}, Type: {output_tensor.dtype}") # DEBUG - Tensor Info
            output_images.append(output_tensor)
            output_masks.append(mask_tensor)


        # Concatenate the list of processed images into a single tensor.
        output_images_tensor = torch.cat(output_images, dim=0)
        output_masks_tensor = torch.cat(output_masks, dim=0)
        print(f"Final Output Tensor Shape: {output_images_tensor.shape}, Type: {output_images_tensor.dtype}") # DEBUG - Final Tensor Shape

        return (output_images_tensor, output_masks_tensor)

    def crop_and_resize_image(self, img, final_width=850, final_height=1049, max_top_space=150, max_side_space=50):
        """
        裁剪透明部分，调整大小，并通过添加透明区域来达到目标像素尺寸，避免拉伸. 按照原比例最大化缩放到新建的画布内, 考虑max_top_space和max_side_space
        """
        print(f"    [crop_and_resize_image] Starting - Input Mode: {img.mode}")
        img = img.convert("RGBA")  # 确保图像具有 Alpha 通道
        print(f"    [crop_and_resize_image] Converted to RGBA - Mode: {img.mode}")

        # 裁剪透明部分
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
            print(f"    [crop_and_resize_image] Cropped - Mode: {img.mode}")
        else:
            print(f"    [crop_and_resize_image] No Bounding Box found (fully transparent?), skipping crop.")

        width, height = img.size

        # 创建新的透明画布
        new_img = Image.new("RGBA", (final_width, final_height), (0, 0, 0, 0))
        print(f"    [crop_and_resize_image] Created new RGBA image - Mode: {new_img.mode}, Size: {new_img.size}")

        # 计算初始缩放比例，仅考虑画布尺寸
        width_ratio = final_width / width
        height_ratio = final_height / height
        initial_scale = min(width_ratio, height_ratio)

        new_width = int(width * initial_scale)
        new_height = int(height * initial_scale)
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        print(f"    [crop_and_resize_image] Initial Resized - Mode: {resized_img.mode}, Size: {resized_img.size}")


        # 计算初始粘贴位置 (初始居中)
        x_offset = (final_width - new_width) // 2
        y_offset = (final_height - new_height) // 2

        # 粘贴图像
        new_img.paste(resized_img, (x_offset, y_offset))
        print(f"    [crop_and_resize_image] Pasted Initially - Mode: {resized_img.mode}, Offset: ({x_offset}, {y_offset})")

        # 获取当前的顶部空间
        top_space = y_offset

        # 调整顶部空间，只在顶部空间大于max_top_space时生效
        if top_space > max_top_space and max_top_space > 0:  # 只有当 max_top_space 大于 0 时才调整
            y_offset = max_top_space
            new_img = Image.new("RGBA", (final_width, final_height), (0, 0, 0, 0)) #创建新的画布
            new_img.paste(resized_img, (x_offset, y_offset)) # 粘贴在新的位置
            print(f"    [crop_and_resize_image] Adjusted Top Space - Mode: {resized_img.mode}, Offset: ({x_offset}, {y_offset})")

        # 调整侧边空间
        side_space = x_offset
        if side_space < max_side_space: # 如果侧边空间小于目标值，则缩放以满足侧边空间
            scale_factor = (final_width - 2 * max_side_space) / (final_width - 2 * side_space)
            new_width = int(new_width * scale_factor)
            new_height = int(new_height * scale_factor)
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            x_offset = max_side_space # 固定左右侧边为 max_side_space
            y_offset = (final_height - new_height) // 2 #重新居中
            new_img = Image.new("RGBA", (final_width, final_height), (0, 0, 0, 0))
            new_img.paste(resized_img, (x_offset, y_offset))
            print(f"   [crop_and_resize_image] Adjusted Side Space - Mode: {resized_img.mode}, Size: {resized_img.size}, Offset: ({x_offset}, {y_offset})")

        print(f"    [crop_and_resize_image] Ending - Output Mode: {new_img.mode}, Size: {new_img.size}")
        return new_img



# Helper functions to convert between PIL images and torch tensors
def tensor_to_pil(img):
    print(f"  [tensor_to_pil] Input Tensor Shape: {img.shape}, Type: {img.dtype}") # DEBUG - Tensor Info in helper
    image = img.cpu().numpy()
    image = np.clip(image * 255, 0, 255).astype(np.uint8)
    # Permute to HWC format if necessary
    if image.ndim == 3 and image.shape[0] in [3, 4]:
        image = np.transpose(image, (1, 2, 0))

    # 显式指定 mode 参数，根据通道数判断
    if image.ndim == 3 and image.shape[-1] == 4: # HWC 格式，4通道
        mode = "RGBA"
    elif image.ndim == 3 and image.shape[-1] == 3: # HWC 格式，3通道
        mode = "RGB"
    elif image.ndim == 2: # 灰度图
        mode = "L"
    else:
        mode = None # 让 PIL 自动判断, or could raise error

    pil_image = Image.fromarray(image, mode=mode) # 添加 mode 参数
    print(f"  [tensor_to_pil] Output PIL Image Mode: {pil_image.mode}, Size: {pil_image.size}") # DEBUG - PIL Image Info in helper
    return pil_image

def pil_to_tensor(img, allow_rgba=True):
    print(f"  [pil_to_tensor] Input PIL Image Mode: {img.mode}, Size: {img.size}") # DEBUG - PIL Image Info in helper
    if allow_rgba:
        img = img.convert("RGBA")
        print(f"  [pil_to_tensor] Converted to RGBA - Mode: {img.mode}") # Debug Mode after convert
    else:
        img = img.convert("RGB")
        print(f"  [pil_to_tensor] Converted to RGB - Mode: {img.mode}") # Debug Mode after convert

    numpy_image = np.array(img).astype(np.float32) / 255.0  # Normalize
    numpy_image = np.clip(numpy_image, 0.0, 1.0)  # Ensure values in [0, 1]

    tensor = torch.from_numpy(numpy_image).unsqueeze(0)  # Add batch dimension
    print(f"  [pil_to_tensor] Output Tensor Shape: {tensor.shape}, Type: {tensor.dtype}") # DEBUG - Tensor Info in helper
    return tensor

NODE_CLASS_MAPPINGS = {
    "ImageProcessor": ImageProcessor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageProcessor": "图像裁剪高级版"
}
