import torch
import torch.nn.functional as F
import math

class SmartResizeAndPad:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "margin": ("INT", {"default": 10, "min": 0, "max": 2048}),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "process"
    CATEGORY = "ZKZ/Image Tools"

    def process(self, image, margin, mask=None):
        # 固定的内部参数，避免在 UI 中暴露复杂度
        target_pixel_count = 1048576
        multiple_of = 64
        B, H, W, C = image.shape

        # 单张处理，避免裁剪后尺寸不一致
        final_images = []
        final_masks = []

        for idx in range(B):
            img_single = image[idx]  # HWC
            if mask is None:
                mask_single = torch.ones((H, W), dtype=torch.float32, device=image.device)
            else:
                mask_single = mask[idx]
                if mask_single.shape[0] != H or mask_single.shape[1] != W:
                    mask_single = F.interpolate(mask_single.unsqueeze(0).unsqueeze(0), size=(H, W), mode="nearest").squeeze(0).squeeze(0)

            # -----------------------------
            # 去除透明边缘（使用 mask 或 alpha 通道）
            # -----------------------------
            if C >= 4:
                alpha_mask = img_single[:, :, 3]
            else:
                alpha_mask = torch.ones((H, W), device=image.device)

            crop_source = torch.maximum(mask_single, alpha_mask)
            nonzero = torch.nonzero(crop_source > 1e-6, as_tuple=False)

            if nonzero.numel() > 0:
                y_min = int(nonzero[:, 0].min())
                y_max = int(nonzero[:, 0].max()) + 1
                x_min = int(nonzero[:, 1].min())
                x_max = int(nonzero[:, 1].max()) + 1

                img_single = img_single[y_min:y_max, x_min:x_max, :]
                mask_single = mask_single[y_min:y_max, x_min:x_max]

            # 更新尺寸
            cur_h, cur_w, _ = img_single.shape

            # -------------------------------------------------------------------
            # 第一步：初步缩放 (根据目标像素量)
            # -------------------------------------------------------------------
            scale_factor = math.sqrt(target_pixel_count / (cur_w * cur_h))
            temp_w = max(1, int(cur_w * scale_factor))
            temp_h = max(1, int(cur_h * scale_factor))

            # 调整格式为 BCHW 进行缩放
            img_permuted = img_single.permute(2, 0, 1).unsqueeze(0)  # 1,C,H,W
            mask_expanded = mask_single.unsqueeze(0).unsqueeze(0)    # 1,1,H,W

            img_temp = F.interpolate(img_permuted, size=(temp_h, temp_w), mode="bicubic", align_corners=False)
            mask_temp = F.interpolate(mask_expanded, size=(temp_h, temp_w), mode="bilinear", align_corners=False)

            # -------------------------------------------------------------------
            # 第二步：添加用户指定的边距 (此时还不一定是64倍数)
            # -------------------------------------------------------------------
            img_margined = F.pad(img_temp, (margin, margin, margin, margin), value=0)
            mask_margined = F.pad(mask_temp, (margin, margin, margin, margin), value=0)

            # 获取添加边距后的新尺寸
            _, _, margined_h, margined_w = img_margined.shape

            # -------------------------------------------------------------------
            # 第三步：整体缩放，确保长边是 64 的倍数
            # -------------------------------------------------------------------
            if margined_w >= margined_h:
                final_w = round(margined_w / multiple_of) * multiple_of
                final_h = int(final_w * (margined_h / margined_w))
            else:
                final_h = round(margined_h / multiple_of) * multiple_of
                final_w = int(final_h * (margined_w / margined_h))

            # 将包含边距的整体再次缩放到符合倍数的尺寸
            img_resized = F.interpolate(img_margined, size=(final_h, final_w), mode="bicubic", align_corners=False)
            mask_resized = F.interpolate(mask_margined, size=(final_h, final_w), mode="bilinear", align_corners=False)

            # -------------------------------------------------------------------
            # 第四步：短边补齐 (Padding) 到 64 倍数
            # -------------------------------------------------------------------
            pad_w_needed = (multiple_of - (final_w % multiple_of)) % multiple_of
            pad_h_needed = (multiple_of - (final_h % multiple_of)) % multiple_of

            pl = pad_w_needed // 2
            pr = pad_w_needed - pl
            pt = pad_h_needed // 2
            pb = pad_h_needed - pt

            final_img = F.pad(img_resized, (pl, pr, pt, pb), value=0)
            final_mask = F.pad(mask_resized, (pl, pr, pt, pb), value=0)

            # 转回 HWC 和 HW
            final_img = final_img.squeeze(0).permute(1, 2, 0)  # HWC
            final_mask = final_mask.squeeze(0).squeeze(0)      # HW

            final_images.append(final_img)
            final_masks.append(final_mask)

        # 对齐批次输出
        final_images_tensor = torch.stack(final_images, dim=0)
        final_masks_tensor = torch.stack(final_masks, dim=0)

        return (final_images_tensor, final_masks_tensor)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "SmartResizeAndPad": SmartResizeAndPad
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SmartResizeAndPad": "按系数智能缩放"
}
