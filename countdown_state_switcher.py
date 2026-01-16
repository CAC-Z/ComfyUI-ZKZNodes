try:
    from server import PromptServer
except ImportError:
    from a1111_comfyui.node_wrappers.base_node import PromptServer

try:
    from impact.utils import any_typ
except ImportError:
    any_typ = ("*",)


class ImpactCountdownNodeStateSwitcher:
    """
    一个手动控制的计数节点。每次执行时，计数器会加一。
    当计数达到预设总数时，它会改变目标节点的启用/禁用状态，并将计数器重置。
    这个节点不会自动重新触发队列。
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "count": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "total": ("INT", {"default": 10, "min": 1, "max": 0xffffffffffffffff}),
                "target_node_id": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "target_state_on_finish": ("BOOLEAN", {"default": True, "label_on": "active", "label_off": "mute"}),
            },
            "optional": {"signal": (any_typ,),},
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    FUNCTION = "doit"
    CATEGORY = "ZKZ"  # 分类
    RETURN_TYPES = (any_typ, "INT")
    RETURN_NAMES = ("signal_opt", "count")
    OUTPUT_NODE = True

    def doit(self, count, total, target_node_id, target_state_on_finish, unique_id, signal=None):
        new_count = count + 1

        if new_count < total:
            # --- 计数进行中 ---
            # 1. 更新UI上的计数值
            PromptServer.instance.send_sync("impact-node-feedback",
                                            {"node_id": unique_id, "widget_name": "count", "type": "int", "value": new_count})
        else:
            # --- 计数完成 ---
            # 1. 达到目标，改变目标节点的状态
            PromptServer.instance.send_sync("impact-node-mute-state", {"node_id": target_node_id, "is_active": target_state_on_finish})
            
            # 2. 将计数器重置为0
            new_count = 0
            PromptServer.instance.send_sync("impact-node-feedback",
                                            {"node_id": unique_id, "widget_name": "count", "type": "int", "value": new_count})

        # 返回信号和更新后的计数值
        # 你可以将这个 'count' 输出连接回它自己的 'count' 输入来形成一个手动循环
        return (signal, new_count)



# --- 节点注册信息 ---
# ComfyUI 会使用这两个字典来加载节点
NODE_CLASS_MAPPINGS = {
    "ImpactCountdownNodeStateSwitcher": ImpactCountdownNodeStateSwitcher
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImpactCountdownNodeStateSwitcher": "节点状态切换器"
}