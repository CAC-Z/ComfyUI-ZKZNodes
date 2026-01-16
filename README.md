# ComfyUI-ZKZNodes

这是为 ComfyUI 编写的一组自定义节点，侧重批量图像处理、透明边裁剪、尺寸调整、保存与文本辅助流程。

## 安装

1. 将本仓库放到 `ComfyUI/custom_nodes/ComfyUI-ZKZNodes`。
2. 重启 ComfyUI。

## 依赖

本项目基于 ComfyUI 默认环境，额外依赖：

- `requests`（URL 图像加载）
- `opencv-python`（透明区域分割）

安装方式：

```bash
pip install -r requirements.txt
```

## 节点说明（按类型分组）

### 图像加载与切分

#### `ComfyUI-ZKZNodes.Simple_Load_Image_Batch`（批量加载图像）
- 输入：`path`, `pattern`, `loop`, `allow_RGBA_output`, `reset`
- 输出：`image`, `mask`, `filename_text`, `text`, `total_images`
- 说明：按路径与通配符加载图片，按自然排序；读取同名 `.txt` 作为文本；索引记录在 `batch_counter.json`。

#### `LoadRGBALocalOrURL`（加载透明 PNG 图像）
- 输入：`image_path_or_url`, `local_file`（可选）
- 输出：`image_rgba`, `mask_alpha`
- 说明：从本地或 URL 加载 RGBA，并输出 alpha mask。

#### `ImageSplitterByTransparency`（图像透明分割）
- 输入：`image`, `min_width`, `min_height`, `alpha_threshold`
- 输出：`image`
- 说明：按透明区域轮廓切分，返回图片批次（需要 `opencv-python`）。

### 图像裁剪与边缘处理

#### `CropBlackAndWhiteBordersNode`（裁剪黑白边框）
- 输入：`image`, `black_threshold`, `white_threshold`
- 输出：`image`
- 说明：检测并裁剪纯黑/纯白边框。

#### `CropTransparentImageNode`（裁剪透明区域）
- 输入：`image`, `margin`
- 输出：`image`, `mask`
- 说明：根据透明通道裁剪，并输出 alpha mask。

#### `CropTransparentAndResizeNode`（裁剪透明并缩放）
- 输入：`image`, `max_size`, `margin`, `resize_mode`
- 输出：`image`, `mask`
- 说明：先裁剪透明边，再按最长边缩放；可选择补边成方图。

#### `ExpandTransparentBorderNode`（扩展透明边）
- 输入：`image`, `expand_top`, `expand_bottom`, `expand_left`, `expand_right`
- 输出：`expanded_image`, `expanded_mask`
- 说明：向四周扩展透明画布。

### 图像缩放与版式处理

#### `ImageProcessor`（图像裁剪高级版）
- 输入：`images`, `final_width`, `final_height`, `max_top_space`, `max_side_space`, `allow_RGBA_output`
- 输出：`image`, `mask`
- 说明：裁剪透明区域后缩放并放入目标画布，适配顶部/侧边限制。

#### `SmartResizeAndPad`（按系数智能缩放）
- 输入：`image`, `margin`, `mask`（可选）
- 输出：`image`, `mask`
- 说明：裁剪透明边后按像素量缩放，并对齐到 64 的倍数。

#### `StretchBottomNode`（图像底部拉伸）
- 输入：`images`, `stretch_pct`, `allow_RGBA_output`
- 输出：`image`
- 说明：按比例拉伸底部像素，增加高度。

### 图像路由与颜色处理

#### `ImageSwitchNode`（图像切换）
- 输入：`image`, `condition`
- 输出：`image_1`, `image_2`
- 说明：当 `condition == "1"` 输出到 1，否则输出到 2。

#### `VrchIsolateColorNode`（隔离颜色（黑/白））
- 输入：`image`, `isolate_color`, `threshold`
- 输出：`image`
- 说明：根据阈值将黑/白区域设为透明。

### 保存与输出

#### `VrchSaveImageNode`（保存图像）
- 输入：`image`, `base_save_path`, `filename_prefix`, `filename_suffix`, `file_type`, `overwrite_if_exists`, `folder_suffix`, `use_date_folder`, `use_date_in_filename`, `use_time_in_filename`
- 输出：`image`
- 说明：支持批量命名、日期文件夹、覆盖规则。

#### `ConditionalSaveImageNode`（条件保存图像）
- 输入：`image`, `condition`, `base_save_path`, `filename_prefix`, `filename_suffix`, `file_type`, `overwrite_if_exists`, `folder_suffix`, `use_date_folder`, `use_date_in_filename`, `use_time_in_filename`
- 输出：`image`
- 说明：当 `condition == "1"` 时保存；支持日期文件夹和灵活命名规则。

#### `ZKZSaveTextNode`（保存文本）
- 输入：`text_content`, `base_save_path`, `filename_prefix`, `filename_separator`, `filename_zero_padding`
- 输出：`text`
- 说明：保存文本为 `.txt`，自动递增文件名。

### 计数、随机与队列控制

#### `CounterNode`（计数器）
- 输入：`rule`, `digits`, `start_value`, `step`, `seed`
- 输出：`text`
- 说明：在 ComfyUI 运行期间保留状态；支持增减/随机/固定。

#### `VrchRandomNumber`（随机数字）
- 输入：`seed`, `min_value`, `max_value`
- 输出：`number_int`, `number_float`, `number_text`
- 说明：按 seed 生成可复现随机数。

#### `VrchCountdownQueueControlNode`（队列管理）
- 输入：`input`, `queue_option`, `countdown_total`, `count`, `enabled`
- 输出：`output`, `count`
- 说明：当计数达到阈值时切换队列模式；在等待窗口内返回 `None` 以中断当前执行。

#### `ImpactCountdownNodeStateSwitcher`（节点状态切换器）
- 输入：`count`, `total`, `target_node_id`, `target_state_on_finish`, `signal`（可选）
- 输出：`signal_opt`, `count`
- 说明：计数达到阈值时切换目标节点的启用状态。

### 文本处理

#### `SequentialReaderNode_ZKZ`（顺序文本读取）
- 输入：`file_path`, `reset`
- 输出：`text`
- 说明：逐行读取非空文本，跨运行记忆当前位置。

#### `UniversalTextReplacer`（通用文本替换）
- 输入：`text_input`, `replacement_rules`（可选）, `use_regex`（可选）
- 输出：`处理后的文本`
- 说明：按 `旧词->新词` 规则替换，支持正则。

## 运行时数据

`batch_counter.json` 会在运行时生成，保存路径：

```
<ComfyUI>/custom_nodes/ComfyUI-ZKZNodes/batch_counter.json
```

不应提交到仓库。

## 开源协议

本项目采用 GNU General Public License v3.0 发布，详见 `LICENSE`。
