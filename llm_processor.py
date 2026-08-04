import os
from openai import OpenAI
import logging

class LLMProcessor:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            logging.warning("DASHSCOPE_API_KEY is not set. LLM processing will fail.")
        
        # 阿里云百炼大模型的兼容 OpenAI 接口
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model_name = os.environ.get("LLM_MODEL_NAME", "qwen-plus")

    def process_post(self, post_content):
        """
        Translates, interprets, and provides suggestions for a given post using Qwen.
        """
        prompt = f"""
请你扮演一位专业的美国政治分析师，针对唐纳德·特朗普(Donald Trump)刚刚发布的一条推文(Truth)，完成以下三个任务。
特别注意：【深度解读】和【投资建议】必须精简核心观点，各自控制在 200 字以内！

请严格以 JSON 格式返回，必须包含以下三个字段，不要输出除 JSON 以外的任何分析解释内容：
{{
  "translation": "中文翻译...",
  "analysis": "深度解读（限200字以内）...",
  "advice": "投资建议（限200字以内）..."
}}

推文内容如下：
{post_content}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位专业的美国政治分析师，只能输出 JSON。"},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content.strip()
            
            # 清理可能被大模型包围的 markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            import json
            result = json.loads(content.strip())
            return result
        except Exception as e:
            logging.error(f"Error calling Qwen API: {e}")
            return None
