import random

class RandomNumberNode:
    """
    一个在指定范围内生成随机整数的ComfyUI节点。
    它提供整数、浮点数和字符串三种格式的输出。
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "min_value": ("INT", {"default": 1, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 1}),
                "max_value": ("INT", {"default": 20, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 1}),
            }
        }

    RETURN_TYPES = ("INT", "FLOAT", "STRING")
    RETURN_NAMES = ("number_int", "number_float", "number_text")
    FUNCTION = "generate_random_number"

    # 将其分类，方便在菜单中查找
    CATEGORY = "ZKZ/Basic" # 您可以根据需要修改分类名称

    def generate_random_number(self, seed, min_value, max_value):
        # 确保 min_value 不大于 max_value
        if min_value > max_value:
            min_value, max_value = max_value, min_value
            
        random.seed(seed)
        random_int = random.randint(min_value, max_value)
        random_float = float(random_int)
        random_string = str(random_int)
        
        return (random_int, random_float, random_string)

# 节点注册信息
NODE_CLASS_MAPPINGS = {
    "VrchRandomNumber": RandomNumberNode  # 建议加上前缀以避免潜在的命名冲突
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VrchRandomNumber": "随机数字"
}
