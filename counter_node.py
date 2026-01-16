import random

# 计数器的核心状态保存在类的变量中，以便在多次执行之间保持其值。
class CounterNode:
    # 初始化类级别的变量来存储计数器的状态
    # 这样可以确保只要ComfyUI服务在运行，状态就是持久的
    _count = 0
    _is_first_run = True
    _last_start_value = 0  # 记录上次的start_value，用于检测变化

    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点的输入参数。
        这些参数会显示在ComfyUI界面的节点上，允许用户进行配置。
        """
        return {
            "required": {
                "rule": (["increment", "decrement", "random", "fixed"],),
                "digits": ("INT", {"default": 2, "min": 1, "max": 10, "step": 1, "display": "number"}),
                "start_value": ("INT", {"default": 0, "min": -9999999, "max": 9999999, "step": 1, "display": "number"}),
                "step": ("INT", {"default": 1, "min": 1, "max": 9999999, "step": 1, "display": "number"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    # 定义节点的返回类型和名称
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)

    # 定义节点的主执行函数
    FUNCTION = "execute"

    # 定义节点在菜单中的分类
    CATEGORY = "ZKZ"

    def execute(self, rule, digits, start_value, step, seed):
        """
        当工作流运行时，此方法被调用。
        """
        # 如果是第一次运行或start_value发生变化，则将计数器设置为新的start_value
        if self._is_first_run or start_value != self.__class__._last_start_value:
            self.__class__._count = start_value
            self.__class__._last_start_value = start_value
            self.__class__._is_first_run = False

        # 根据用户选择的规则更新计数值
        if rule == "increment":
            self.__class__._count += step
        elif rule == "decrement":
            self.__class__._count -= step
        elif rule == "random":
            # 使用种子确保随机数的可复现性
            random.seed(seed)
            # 生成一个在合理范围内的随机数
            max_random_val = 10 ** digits
            self.__class__._count = random.randint(0, max_random_val -1)
        elif rule == "fixed":
            self.__class__._count = start_value
            
        # 将计数值格式化为带有前导零的字符串
        # 例如，如果 digits=3, count=5，则输出 "005"
        formatted_text = str(self.__class__._count).zfill(digits)

        # 返回结果
        # "ui"部分用于在节点上直接显示文本
        # "result"部分是节点的实际输出，可以连接到其他节点
        return {"ui": {"string": [formatted_text]}, "result": (formatted_text,)}

# ComfyUI 加载节点所需的映射
NODE_CLASS_MAPPINGS = {
    "CounterNode": CounterNode
}

# 节点在UI中显示的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "CounterNode": "计数器"
}