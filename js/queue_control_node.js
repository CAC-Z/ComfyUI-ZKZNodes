import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// 添加调试标志
const DEBUG = true;

app.registerExtension({
    name: "vrch.CountdownQueueControlNode",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "VrchCountdownQueueControlNode") {
            if (DEBUG) console.log("[CountdownQueueControlNode] Registering node definition");
        }
    },

    getCustomWidgets() {
        return {};
    },

    async nodeCreated(node) {
        if (node.comfyClass === "VrchCountdownQueueControlNode") {
            if (DEBUG) console.log("[CountdownQueueControlNode] Node created");

            let countdownTotalWidget = node.widgets.find(w => w.name === "countdown_total");
            let countdownTotal = countdownTotalWidget ? countdownTotalWidget.value : 5;
            let countWidget = node.widgets.find(w => w.name === "count");
            
            if (DEBUG) {
                console.log("[CountdownQueueControlNode] Initial values:");
                console.log("- countdownTotal:", countdownTotal);
                console.log("- countWidget value:", countWidget ? countWidget.value : "not found");
            }

            const countdownDisplay = document.createElement('div');
            countdownDisplay.classList.add("comfy-value-small-display");
            node.addDOMWidget("countdown_display", "countdown_display", countdownDisplay);

            function updateCountdownDisplay(value) {
                if (countdownDisplay) {
                    const remaining = countdownTotal - value;
                    countdownDisplay.textContent = `Change in ${remaining} ${remaining == 1 ? "second" : "seconds"} ...`;
                    if (DEBUG) console.log(`[CountdownQueueControlNode] Display updated: ${countdownDisplay.textContent}`);
                }
            }

            function selectQueueOption(queueOption) {
                if (DEBUG) {
                    console.log("\n[CountdownQueueControlNode] ====== Select Queue Option ======");
                    console.log(`[CountdownQueueControlNode] Attempting to select queue option: ${queueOption}`);
                }
                
                // 1. 定位队列按钮的容器
                const buttonContainer = document.querySelector('div[data-testid="queue-button"]');
                if (DEBUG) {
                    console.log("[CountdownQueueControlNode] Button container search result:");
                    console.log(buttonContainer);
                }
                
                if (buttonContainer) {
                    // 2. 尝试所有可能的下拉菜单按钮选择器
                    const dropdownButton = 
                        buttonContainer.querySelector('button[data-pc-name="pcdropdown"]') ||
                        buttonContainer.querySelector('button.p-splitbutton-menubutton') ||
                        buttonContainer.querySelector('button[aria-haspopup="true"]');
                        
                    if (DEBUG) {
                        console.log("[CountdownQueueControlNode] Dropdown button search result:");
                        console.log(dropdownButton);
                    }

                    if (dropdownButton) {
                        if (DEBUG) console.log("[CountdownQueueControlNode] Clicking dropdown button");
                        dropdownButton.click();
                        
                        // 延长等待时间
                        setTimeout(() => {
                            if (DEBUG) console.log("[CountdownQueueControlNode] Looking for menu after delay");
                            
                            // 尝试所有可能的菜单容器选择器
                            const menuContainer = 
                                document.querySelector('div[data-pc-name="pcmenu"]') ||
                                document.querySelector('div.p-tieredmenu.p-component.p-tieredmenu-overlay') ||
                                document.querySelector('ul.p-menu-list');
                                
                            if (DEBUG) {
                                console.log("[CountdownQueueControlNode] Menu container search result:");
                                console.log(menuContainer);
                            }

                            if (menuContainer) {
                                // 尝试所有可能的按钮选择器
                                const buttons = {
                                    once: menuContainer.querySelector('li[aria-label="Queue"] button, li#pv_id_10_overlay_0 button'),
                                    instant: menuContainer.querySelector('li[aria-label="Queue (Instant)"] button, li#pv_id_10_overlay_1 button'),
                                    change: menuContainer.querySelector('li[aria-label="Queue (Change)"] button, li#pv_id_10_overlay_2 button')
                                };

                                if (DEBUG) {
                                    console.log("[CountdownQueueControlNode] Found menu buttons:");
                                    console.log(buttons);
                                }

                                const targetButton = buttons[queueOption];
                                if (targetButton) {
                                    if (DEBUG) console.log(`[CountdownQueueControlNode] Clicking ${queueOption} button`);
                                    targetButton.click();
                                } else {
                                    console.warn(`[CountdownQueueControlNode] ${queueOption} button not found`);
                                }
                            } else {
                                console.warn("[CountdownQueueControlNode] Menu container not found");
                            }
                        }, 500); // 增加延迟时间到 500ms
                    } else {
                        console.warn("[CountdownQueueControlNode] No dropdown button found");
                    }
                } else {
                    console.warn("[CountdownQueueControlNode] Queue button container not found");
                }
            }

            api.addEventListener("vrch-queue-mode-change", (event) => {
                const queue_option = event.detail.queue_option;
                if (DEBUG) {
                    console.log("\n[CountdownQueueControlNode] ====== Queue Mode Change Event ======");
                    console.log(`[CountdownQueueControlNode] Received queue-mode-change event`);
                    console.log("Event details:", event.detail);
                    console.log("Queue option:", queue_option);
                }
                
                // 只切换队列模式，不点击队列按钮
                setTimeout(() => {
                    if (DEBUG) console.log("[CountdownQueueControlNode] Attempting to change queue mode");
                    selectQueueOption(queue_option);
                    
                    // 在队列模式改变后，重置计数器
                    setTimeout(() => {
                        if (DEBUG) console.log("[CountdownQueueControlNode] Queue mode changed, resetting counter");
                        PromptServer.instance.send_sync("impact-node-feedback",
                                          {"node_id": node.id, 
                                           "widget_name": "count", 
                                           "type": "int",
                                           "value": 0});
                    }, 1000); // 给足够的时间让队列模式改变
                }, 100);
                
                if (countdownDisplay) {
                    countdownDisplay.textContent = `Queue Mode Changed`;
                }
            });

            api.addEventListener("impact-node-feedback", (event) => {
                if (event.detail.node_id === node.id) {
                    const feedbackData = event.detail;
                    if (DEBUG) {
                        console.log("[CountdownQueueControlNode] Received feedback:", feedbackData);
                    }

                    const widgetName = feedbackData.widget_name;
                    const value = feedbackData.value;
                    
                    if (widgetName === "count" && countWidget) {
                        if (DEBUG) console.log(`[CountdownQueueControlNode] Updating count to: ${value}`);
                        countWidget.value = value;
                        node.widgets_values[node.widgets.indexOf(countWidget)] = value;
                        updateCountdownDisplay(value);
                        app.graph.setDirtyCanvas(true);
                    } else if (widgetName === "countdown_display") {
                        if (DEBUG) console.log(`[CountdownQueueControlNode] Updating display text: ${value}`);
                        countdownDisplay.textContent = value;
                    }
                }
            });

            // 监听小部件值变化
            if (countdownTotalWidget) {
                countdownTotalWidget.callback = (value) => {
                    if (DEBUG) console.log(`[CountdownQueueControlNode] countdown_total changed to: ${value}`);
                    countdownTotal = value;
                    updateCountdownDisplay(countWidget ? countWidget.value : 0);
                };
            }

            if (countWidget) {
                countWidget.callback = (value) => {
                    if (DEBUG) console.log(`[CountdownQueueControlNode] count widget changed to: ${value}`);
                    updateCountdownDisplay(value);
                };
            }

            node.onRemoved = function () {
                if (DEBUG) console.log("[CountdownQueueControlNode] Node removed, cleaning up");
                if (countdownDisplay.parentNode) {
                    countdownDisplay.parentNode.removeChild(countdownDisplay);
                }
            };

            function init() {
                if (DEBUG) console.log("[CountdownQueueControlNode] Initializing display");
                updateCountdownDisplay(countWidget ? countWidget.value : 0);
            }

            setTimeout(init, 1000);
        }
    }
});

const style = document.createElement("style");
style.textContent = `
    .comfy-value-small-display {
        margin-top: 0px;
        font-size: 14px;
        text-align: center;
    }
`;
document.head.appendChild(style);