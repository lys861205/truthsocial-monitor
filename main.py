import os
import time
import logging
from dotenv import load_dotenv

from monitor import TruthSocialMonitor
from llm_processor import LLMProcessor
from wechat_notifier import WeChatNotifier, FeishuNotifier

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    load_dotenv()
    
    webhook_url = os.environ.get("WEBHOOK_URL")
    feishu_webhook = os.environ.get("FEISHU_WEBHOOK")
    feishu_secret = os.environ.get("FEISHU_SECRET")
    
    if not any([webhook_url, feishu_webhook]):
        logging.error("Please set at least one Webhook in .env file")
        return

    monitor = TruthSocialMonitor()
    llm_processor = LLMProcessor()
    
    wechat_notifier = WeChatNotifier(webhook_url) if webhook_url else None
    feishu_notifier = FeishuNotifier(feishu_webhook, feishu_secret) if feishu_webhook else None

    logging.info("Starting Truth Social Monitor (Multi-Push Edition)...")
    
    while True:
        try:
            post = monitor.get_latest_post()
            
            if post:
                logging.info(f"New post detected! ID: {post['id']}")
                
                # ------ 1. 企业微信：提前发送原文 ------
                if wechat_notifier:
                    msg1 = f"""<font color="warning">🚨 特朗普在 Truth Social 发布了新动态 (1/4：英文原文)</font>\n
> **发布时间**: {post['published']}
> **原帖链接**: [点击查看原帖]({post['link']})

{post['title']}
"""
                    wechat_notifier.send_markdown(msg1)
                
                # ------ 2. 调用大模型 ------
                logging.info("Calling LLM for translation and analysis...")
                llm_result = llm_processor.process_post(post['content'])
                
                title = "🚨 特朗普 Truth Social 新动态"
                
                # ------ 3. 推送结果 ------
                if not llm_result:
                    logging.error("LLM processing failed, sending original text only.")
                    content = f"**发布时间**: {post['published']}\n**原帖链接**: [点击查看原帖]({post['link']})\n\n### 🇺🇸 英文原文\n{post['title']}"
                    
                    if feishu_notifier: feishu_notifier.send_markdown(title, content)
                    continue
                
                # 3.1 统一发送 (合并消息版：适合 Feishu)
                merged_message = f"""**发布时间**: {post['published']}
**原帖链接**: [点击查看原帖]({post['link']})

---

### 🇺🇸 英文原文
{post['title']}

---

### 🇨🇳 中文翻译
{llm_result.get('translation', '无内容')}

---

### 🔍 深度解读
{llm_result.get('analysis', '无内容')}

---

### 💡 投资建议
{llm_result.get('advice', '无内容')}
"""
                if feishu_notifier: feishu_notifier.send_markdown(title, merged_message)

                # 3.2 企业微信 拆分发送
                if wechat_notifier:
                    msg2 = f"""<font color="info">📄 特朗普新动态 (2/4：中文翻译)</font>\n\n{llm_result.get('translation', '无内容')}"""
                    wechat_notifier.send_markdown(msg2)
                    time.sleep(1)
                    
                    msg3 = f"""<font color="info">🔍 特朗普新动态 (3/4：深度解读)</font>\n\n{llm_result.get('analysis', '无内容')}"""
                    wechat_notifier.send_markdown(msg3)
                    time.sleep(1)
                    
                    msg4 = f"""<font color="info">💡 特朗普新动态 (4/4：投资建议)</font>\n\n{llm_result.get('advice', '无内容')}"""
                    wechat_notifier.send_markdown(msg4)
                
            time.sleep(10)
            
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
