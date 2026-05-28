"""
LLM API 服务模块

标准OpenAI Chat Completions API，手动维护对话上下文

配置来源: 项目根目录 .env 文件

使用方法:
    from services.llm_api import LLMService, get_patient_llm
    
    # 创建实例（自动从.env加载配置）
    llm = LLMService(role="patient")
    
    # 单轮对话
    response = llm.chat("你好")
    
    # 多轮对话（自动维护上下文）
    response = llm.chat("我叫小明")  # 包含上一轮上下文
    response = llm.chat("我叫什么名字？")  # 模型知道是小明
    
    # 查看完整对话历史
    print(llm.get_history())
    
    # 新实例 = 新对话
    llm2 = LLMService(role="patient")  # 全新上下文
"""

import os
import base64
import time
import logging
from typing import List, Dict, Union, Optional
from dataclasses import dataclass
from pathlib import Path

import httpx
from openai import OpenAI
from dotenv import load_dotenv

# 加载.env文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

logging.getLogger("httpx").setLevel(logging.ERROR)


@dataclass
class APIConfig:
    """API配置类"""
    api_base: str
    api_key: str
    model: str
    max_tokens: int = 4096
    temperature: float = 1.0
    timeout: float = 30.0


class LLMConfigManager:
    """LLM配置管理器 - 从.env加载配置"""
    
    _configs: Dict[str, APIConfig] = {}
    
    @classmethod
    def get_config(cls, role: str) -> APIConfig:
        """获取指定角色的配置"""
        if role not in cls._configs:
            role_upper = role.upper()

            # evaluator1-5 特殊处理：映射为 EVALUATOR_1, EVALUATOR_2 等 env 前缀
            if role_upper.startswith("EVALUATOR") and len(role_upper) > 9:
                # "EVALUATOR1" -> "EVALUATOR_1"
                role_upper = f"EVALUATOR_{role_upper[9]}"

            # 优先使用角色特定的配置，否则使用通用配置
            temperature_key = f"{role_upper}_TEMPERATURE"
            timeout_key = f"{role_upper}_TIMEOUT"

            max_tokens_key = f"{role_upper}_MAX_TOKENS"
            cls._configs[role] = APIConfig(
                api_base=os.getenv(f"{role_upper}_API_BASE", ""),
                api_key=os.getenv(f"{role_upper}_API_KEY", ""),
                model=os.getenv(f"{role_upper}_MODEL", "gpt-4o"),
                max_tokens=int(os.getenv(max_tokens_key, os.getenv("MAX_TOKENS", "4096"))),
                temperature=float(os.getenv(temperature_key, os.getenv("TEMPERATURE", "1.0"))),
                timeout=float(os.getenv(timeout_key, os.getenv("TIMEOUT", "30.0")))
            )
        return cls._configs[role]


class LLMService:
    """LLM服务类 - 标准OpenAI Chat Completions API
    
    特性:
    - 实例生命周期内自动维护对话上下文
    - 每次调用附带完整历史
    - 新实例 = 新对话（上下文清空）
    """
    
    def __init__(self, role: str = "patient", system_message: str = ""):
        """初始化LLM服务
        
        Args:
            role: 角色名称 (patient/doctor/evaluator)
            system_message: 可选的系统提示词
        """
        self.role = role
        self.config = LLMConfigManager.get_config(role)
        self.logger = logging.getLogger(__name__)
        
        # 创建OpenAI客户端
        self.client = OpenAI(
            base_url=self.config.api_base,
            api_key=self.config.api_key,
            http_client=httpx.Client(verify=False, timeout=self.config.timeout)
        )
        
        # 对话历史: [{"role": "user"/"assistant"/"system", "content": str}]
        self._history: List[Dict[str, str]] = []
        
        # 设置系统提示词
        if system_message:
            self._history.append({"role": "system", "content": system_message})
    
    def chat(self, message: str) -> str:
        """发送消息并获取回复（自动维护上下文）
        
        Args:
            message: 用户消息
            
        Returns:
            助手回复内容
        """
        # 添加用户消息到历史
        self._history.append({"role": "user", "content": message})
        
        # 限制对话历史长度，避免 token 超限
        # 保留 system 消息 + 最近 20 轮对话（40 条消息）
        MAX_HISTORY_MESSAGES = 42  # 1 system + 40 conversation
        if len(self._history) > MAX_HISTORY_MESSAGES:
            # 保留 system 消息和最近的消息
            system_msgs = [m for m in self._history if m["role"] == "system"]
            recent_msgs = self._history[-MAX_HISTORY_MESSAGES + len(system_msgs):]
            self._history = system_msgs + recent_msgs
        
        # 调用API
        response = self._call_api(self._history)
        
        # 添加助手回复到历史
        self._history.append({"role": "assistant", "content": response})
        
        return response
    
    def chat_with_history(self, messages: List[Dict[str, str]]) -> str:
        """使用指定历史进行对话（不修改当前实例历史）
        
        Args:
            messages: 完整对话历史
            
        Returns:
            助手回复内容
        """
        return self._call_api(messages)
    
    def _call_api(self, messages: List[Dict[str, str]]) -> str:
        """底层API调用（带重试）"""
        def _call():
            msgs = messages
            # 百川医学 API 不支持 system role，将其合并到第一条 user 消息
            if "baichuan" in self.config.model.lower():
                msgs = self._convert_system_to_user(messages)

            kwargs = {
                "model": self.config.model,
                "messages": msgs,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "timeout": self.config.timeout,
            }
            # 仅 Qwen 系列模型需要关闭 enable_thinking
            if self.config.model.lower().startswith("qwen"):
                kwargs["extra_body"] = {"enable_thinking": False}

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        return self._retry_with_backoff(_call)

    @staticmethod
    def _convert_system_to_user(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """将 system 消息合并到第一条 user 消息（百川医学兼容）"""
        system_msgs = []
        other_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msgs.append(m["content"])
            else:
                other_msgs.append(m)
        if not system_msgs:
            return other_msgs
        # 将 system 内容拼到第一条 user 消息前面
        combined = "\n\n".join(system_msgs)
        if other_msgs and other_msgs[0]["role"] == "user":
            first = other_msgs[0]
            new_content = combined + "\n\n" + first["content"]
            return [{"role": "user", "content": new_content}] + other_msgs[1:]
        # 如果没有 user 消息，创建一条
        return [{"role": "user", "content": combined}] + other_msgs
    
    def _retry_with_backoff(self, func, max_retries: int = 3, delay: float = 1.0):
        """带退避的重试机制"""
        last_error = None
        for i in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_error = e
                self.logger.warning(f"[{self.role}] API调用失败({i+1}/{max_retries}): {e}")
                if i < max_retries - 1:
                    time.sleep(delay * (2 ** i))  # 指数退避
        raise last_error
    
    def get_history(self) -> List[Dict[str, str]]:
        """获取当前对话历史（副本）"""
        return self._history.copy()
    
    def clear_history(self):
        """清空对话历史（保留system消息）"""
        # 保留system消息
        system_msgs = [m for m in self._history if m["role"] == "system"]
        self._history = system_msgs.copy()
    
    def reset(self):
        """完全重置（清空所有历史）"""
        self._history = []
    
    def set_system_message(self, message: str):
        """设置/更新系统提示词"""
        # 移除旧的system消息
        self._history = [m for m in self._history if m["role"] != "system"]
        # 插入新的system消息到开头
        self._history.insert(0, {"role": "system", "content": message})
    
    def chat_with_images(
        self,
        message: str,
        image_paths: Union[str, List[str]]
    ) -> str:
        """多模态对话（图文）
        
        Args:
            message: 关于图片的提示
            image_paths: 图片路径或路径列表
            
        Returns:
            助手回复内容
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]
        
        # 构建content列表
        content = [{"type": "text", "text": message}]
        for path in image_paths:
            base64_image = self._encode_image(path)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        
        # 添加用户消息
        self._history.append({"role": "user", "content": content})

        # 限制对话历史长度（与 chat 方法保持一致）
        MAX_HISTORY_MESSAGES = 42
        if len(self._history) > MAX_HISTORY_MESSAGES:
            system_msgs = [m for m in self._history if m["role"] == "system"]
            recent_msgs = self._history[-MAX_HISTORY_MESSAGES + len(system_msgs):]
            self._history = system_msgs + recent_msgs

        # 调用API
        response = self._call_api(self._history)
        
        # 添加助手回复
        self._history.append({"role": "assistant", "content": response})
        
        return response
    
    def _encode_image(self, image_path: str) -> str:
        """图片转base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')


# ========== 便捷函数 ==========

def get_patient_llm(system_message: str = "", backup: bool = False) -> LLMService:
    """获取患者Agent的LLM服务

    Args:
        system_message: 可选的系统提示词
        backup: 使用备用API（PATIENT_BACKUP_* 配置）
    """
    role = "patient_backup" if backup else "patient"
    return LLMService(role=role, system_message=system_message)


def get_doctor_llm(system_message: str = "") -> LLMService:
    """获取医生Agent的LLM服务"""
    return LLMService(role="doctor", system_message=system_message)


def get_evaluator_llm(system_message: str = "", evaluator_id: int = 1) -> LLMService:
    """获取评估器的LLM服务

    Args:
        system_message: 可选的系统提示词
        evaluator_id: 评估器编号 (1-5)，对应 .env 中的 EVALUATOR_N_* 配置
    """
    return LLMService(role=f"evaluator{evaluator_id}", system_message=system_message)


def get_instrument_llm(system_message: str = "", backup: bool = False) -> LLMService:
    """获取仪器Agent的LLM服务

    Args:
        system_message: 可选的系统提示词
        backup: 使用备用API（INSTRUMENT_BACKUP_* 配置）
    """
    role = "instrument_backup" if backup else "instrument"
    return LLMService(role=role, system_message=system_message)
