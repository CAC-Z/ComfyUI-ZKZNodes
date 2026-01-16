import time
import hashlib
from server import PromptServer
import torch

DEBUG = True
_input_types_registered = False
_node_states = {}

class VrchCountdownQueueControlNode:
    QUEUE_OPTIONS = ["once", "instant"]
    MODE_CHANGE_DELAY = 2.0
    SPECIAL_HASH_VALUE = "UNINITIALIZED"

    @classmethod
    def INPUT_TYPES(cls):
        global _input_types_registered
        if DEBUG and not _input_types_registered:
            print("[CountdownQueueControlNode] Registering input types")
            _input_types_registered = True
        return {
            "required": {
                "input": ("IMAGE",),
                "queue_option": (cls.QUEUE_OPTIONS, {"default": "instant"}),
                "countdown_total": ("INT", {"default": 5, "min": 1, "max": 60}),
                "count": ("INT", {"default": 0, "min": 0, "max": 60}),
                "enabled": ("BOOLEAN", {"default": True}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("IMAGE", "INT",)
    RETURN_NAMES = ("output", "count",)
    FUNCTION = "change_queue_mode"
    CATEGORY = "ZKZ/Basic"
    OUTPUT_NODE = True

    def change_queue_mode(self, input, queue_option, countdown_total, count, enabled, unique_id=None):
        global _node_states

        if not unique_id:
            if DEBUG:
                print("[CountdownQueueControlNode] Warning: No unique_id provided")
            return (input, count,)

        if unique_id not in _node_states:
            _node_states[unique_id] = {
                "last_queue_option": queue_option,
                "last_input_hash": self.SPECIAL_HASH_VALUE,
                "waiting_mode_change": False,
                "last_mode_change_time": 0,
                "mode_change_triggered": False,
                "last_count": 0  # 添加上一次的计数记录
            }

        node_state = _node_states[unique_id]
        current_time = time.time()

        if DEBUG:
            print(f"\n[CountdownQueueControlNode] ====== Begin Execution ======")
            print(f"[CountdownQueueControlNode] Processing node {unique_id}")
            print(f"[CountdownQueueControlNode] Current values:")
            print(f"- queue_option: {queue_option}")
            print(f"- countdown_total: {countdown_total}")
            print(f"- count: {count}")
            print(f"- enabled: {enabled}")
            print(f"- mode_change_triggered: {node_state['mode_change_triggered']}")
            print(f"- waiting_mode_change: {node_state['waiting_mode_change']}")
            print(f"- last_count: {node_state['last_count']}")

        try:
            # 检查队列选项是否发生变化
            if queue_option != node_state["last_queue_option"]:
                if DEBUG:
                    print(f"[CountdownQueueControlNode] Queue option changed from {node_state['last_queue_option']} to {queue_option}")
                # 完全重置节点状态
                _node_states[unique_id] = {
                    "last_queue_option": queue_option,
                    "last_input_hash": self.SPECIAL_HASH_VALUE,
                    "waiting_mode_change": False,
                    "last_mode_change_time": 0,
                    "mode_change_triggered": False,
                    "last_count": 0
                }
                node_state = _node_states[unique_id]
                new_count = 1  # 直接从1开始计数
                node_state["last_count"] = new_count
                
                # 更新计数显示
                PromptServer.instance.send_sync("impact-node-feedback",
                                              {"node_id": unique_id, 
                                               "widget_name": "count", 
                                               "type": "int",
                                               "value": new_count})
                
                # 更新倒计时显示
                remaining = countdown_total - new_count
                PromptServer.instance.send_sync("impact-node-feedback",
                                              {"node_id": unique_id, 
                                               "widget_name": "countdown_display", 
                                               "type": "text",
                                               "value": f"Change in {remaining} {'second' if remaining == 1 else 'seconds'} ..."})
                
                return (input, new_count,)

            # 如果正在等待模式切换完成
            if node_state["waiting_mode_change"]:
                if current_time - node_state["last_mode_change_time"] > self.MODE_CHANGE_DELAY:
                    if DEBUG:
                        print(f"[CountdownQueueControlNode] Mode change wait completed")
                    node_state["waiting_mode_change"] = False
                    node_state["mode_change_triggered"] = False
                    node_state["last_input_hash"] = self.SPECIAL_HASH_VALUE
                    node_state["last_count"] = 0
                else:
                    if DEBUG:
                        print(f"[CountdownQueueControlNode] Waiting for mode change to complete")
                    # 在返回None之前重置节点状态，但保留countdown_total
                    _node_states[unique_id] = {
                        "last_queue_option": queue_option,
                        "last_input_hash": self.SPECIAL_HASH_VALUE,
                        "waiting_mode_change": False,
                        "last_mode_change_time": 0,
                        "mode_change_triggered": False,
                        "last_count": 0
                    }
                    # 重置计数显示
                    PromptServer.instance.send_sync("impact-node-feedback",
                                                  {"node_id": unique_id, 
                                                   "widget_name": "count", 
                                                   "type": "int",
                                                   "value": 0})
                    return None

            # 如果节点未启用，直接传递输入
            if not enabled:
                if DEBUG:
                    print(f"[CountdownQueueControlNode] Node disabled, passing through input")
                return (input, count,)

            # 计算当前输入的哈希值
            current_input_hash = None
            if isinstance(input, torch.Tensor):
                current_input_hash = hash((
                    input.shape,
                    float(input.mean()),
                    float(input.std()),
                    float(input.min()),
                    float(input.max())
                ))

            # 检查输入是否发生变化
            input_changed = current_input_hash != node_state["last_input_hash"]
            node_state["last_input_hash"] = current_input_hash

            if DEBUG:
                print(f"[CountdownQueueControlNode] State check:")
                print(f"- Input changed: {input_changed}")
                print(f"- Current count: {count}")

            if input_changed and not node_state["mode_change_triggered"]:
                # 确保计数从上次的值继续
                new_count = node_state["last_count"] + 1
                node_state["last_count"] = new_count

                if DEBUG:
                    print(f"[CountdownQueueControlNode] Updating count to {new_count}")

                # 更新计数显示
                PromptServer.instance.send_sync("impact-node-feedback",
                                              {"node_id": unique_id, 
                                               "widget_name": "count", 
                                               "type": "int",
                                               "value": new_count})

                # 如果达到目标计数，切换模式并重置
                if new_count >= countdown_total:
                    if DEBUG:
                        print(f"[CountdownQueueControlNode] Target count reached, changing queue mode to {queue_option}")

                    # 发送队列模式更改事件
                    PromptServer.instance.send_sync("vrch-queue-mode-change", {"queue_option": queue_option})

                    # 设置等待状态
                    node_state["waiting_mode_change"] = True
                    node_state["mode_change_triggered"] = True
                    node_state["last_mode_change_time"] = current_time

                    # 重置计数
                    new_count = 0
                    node_state["last_count"] = new_count
                    PromptServer.instance.send_sync("impact-node-feedback",
                                                  {"node_id": unique_id, 
                                                   "widget_name": "count", 
                                                   "type": "int",
                                                   "value": new_count})

                    # 更新显示
                    PromptServer.instance.send_sync("impact-node-feedback",
                                                  {"node_id": unique_id, 
                                                   "widget_name": "countdown_display", 
                                                   "type": "text",
                                                   "value": "Queue Mode Changed"})

                    return (input, new_count,)
                else:
                    # 更新倒计时显示
                    remaining = countdown_total - new_count
                    PromptServer.instance.send_sync("impact-node-feedback",
                                                  {"node_id": unique_id, 
                                                   "widget_name": "countdown_display", 
                                                   "type": "text",
                                                   "value": f"Change in {remaining} {'second' if remaining == 1 else 'seconds'} ..."})

                return (input, new_count,)

            # 如果输入没有变化或模式切换已触发，直接返回当前状态
            if DEBUG:
                print(f"[CountdownQueueControlNode] Input unchanged or mode change triggered, passing through")
            return (input, count,)

        except Exception as e:
            if DEBUG:
                print(f"[CountdownQueueControlNode] Error occurred: {str(e)}")
            return (input, count,)

    @classmethod
    def IS_CHANGED(cls, queue_option, countdown_total, count, enabled, unique_id=None):
        m = hashlib.sha256()
        m.update(queue_option.encode())
        m.update(str(countdown_total).encode())
        m.update(str(count).encode())
        m.update(str(enabled).encode())
        if unique_id:
            m.update(str(unique_id).encode())
        return m.hexdigest()
