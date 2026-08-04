import os
import time
import logging
from dotenv import load_dotenv

from monitor import TruthSocialMonitor
from llm_processor import LLMProcessor
from wechat_notifier import PushPlusNotifier

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    load_dotenv()
    
    pushplus_token = os.environ.get("PUSHPLUS_TOKEN")
    pushplus_topic = os.environ.get("PUSHPLUS_TOPIC")
    
    if not pushplus_token:
        logging.error("Please set PUSHPLUS_TOKEN in .env file")
        return

    monitor = TruthSocialMonitor()
    llm_processor = LLMProcessor()
    notifier = PushPlusNotifier(pushplus_token, pushplus_topic)

    logging.info("Starting Truth Social Monitor (PushPlus Edition)...")
    
    while True:
        try:
            post = monitor.get_latest_post()
            
            if post:
                logging.info(f"New post detected! ID: {post['id']}")
                
                # Use LLM to translate and analyze
                logging.info("Calling LLM for translation and analysis...")
                llm_result = llm_processor.process_post(post['content'])
                
                title = "🚨 特朗普 Truth Social 新动态"
                
                if not llm_result:
                    logging.error("LLM processing failed, sending original text only.")
                    content = f"""**发布时间**: {post['published']}
**原帖链接**: [点击查看原帖]({post['link']})

---

### 🇺🇸 英文原文
{post['title']}
"""
                    notifier.send_markdown(title, content)
                    continue
                
                # Merge into one beautifully formatted message for PushPlus
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
                notifier.send_markdown(title, merged_message)
                
            time.sleep(10)
            
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
