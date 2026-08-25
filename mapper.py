"""映射引擎：加载 config.json，管理配置档与按键绑定查找。零第三方依赖。"""

import json
from dataclasses import dataclass, field

# 修饰键前缀，同时按多个时按此顺序匹配
MODIFIER_ORDER = ("LT", "LB", "RT", "RB", "L3")


@dataclass
class Binding:
    """一条按键绑定：action 为 "key"（keys 组合键）、"sequence"（steps 步骤序列）或 "mouse"（button 鼠标键）。"""
    action: str
    keys: list = field(default_factory=list)     # action="key" 时的组合键名列表
    steps: list = field(default_factory=list)    # action="sequence" 时的步骤列表
    trigger: str = "press"                       # press / release / both
    repeat: bool = False                         # 按住连发（方向键和按钮都支持）
    button: str = "left"                         # action="mouse" 时的鼠标键：left/right/middle


def _parse_binding(raw: dict) -> Binding:
    return Binding(
        action=raw.get("action", "key"),
        keys=list(raw.get("keys", [])),
        steps=list(raw.get("steps", [])),
        trigger=raw.get("trigger", "press"),
        repeat=bool(raw.get("repeat", False)),
        button=raw.get("button", "left"),
    )


class Mapper:
    """配置档管理 + 双层绑定查找（修饰层优先，回落默认层）。"""

    def __init__(self, config_path: str):
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)

        # 全局参数
        self.deadzone = float(cfg.get("deadzone", 0.35))
        self.hysteresis = float(cfg.get("hysteresis", 0.1))
        self.trigger_threshold = float(cfg.get("trigger_threshold", 0.5))
        self.repeat_delay_ms = int(cfg.get("repeat_delay_ms", 400))
        self.repeat_rate_ms = int(cfg.get("repeat_rate_ms", 80))
        self.mouse_deadzone = float(cfg.get("mouse_deadzone", 0.15))
        self.mouse_speed = int(cfg.get("mouse_speed", 8))

        # 预解析所有配置档的绑定
        self.current_index = 0
        self.profiles = [
            {
                "name": p.get("name", f"profile{i}"),
                "bindings": {name: _parse_binding(b) for name, b in p.get("bindings", {}).items()},
            }
            for i, p in enumerate(cfg.get("profiles", []))
        ]
        if not self.profiles:
            raise ValueError("config.json 中没有配置任何配置档")

    @property
    def profile(self) -> dict:
        return self.profiles[self.current_index]

    @property
    def profile_name(self) -> str:
        return self.profile["name"]

    def find_binding(self, event_name: str, active_modifiers):
        """双层查找：先精确匹配带修饰前缀的绑定（如 LT+A），找不到回落默认层同名绑定。"""
        bindings = self.profile["bindings"]
        for mod in MODIFIER_ORDER:
            if mod in active_modifiers:
                b = bindings.get(f"{mod}+{event_name}")
                if b is not None:
                    return b
        return bindings.get(event_name)

    def switch_profile(self):
        """循环切换到下一个配置档，返回新名字；只有一个配置档时返回 None。"""
        if len(self.profiles) <= 1:
            return None
        self.current_index = (self.current_index + 1) % len(self.profiles)
        return self.profile_name
