import os
import time
import logging
from dotenv import load_dotenv

from monitor import TruthSocialMonitor
from llm_processor import LLMProcessor
from wechat_notifier import WeChatNotifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Load configuration from .env file
    load_dotenv()
    
    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        logging.error("WEBHOOK_URL environment variable is missing. Please check your .env file.")
        return

    # Initialize modules
    monitor = TruthSocialMonitor()
    llm_processor = LLMProcessor()
    notifier = WeChatNotifier(webhook_url=webhook_url)

    logging.info("Starting Truth Social Monitor...")
    logging.info("Polling every 10 seconds. Press Ctrl+C to stop.")

    try:
        while True:
            post = monitor.get_latest_post()
            
            if post:
                logging.info(f"New post detected! ID: {post['id']}")
                
                # Message 1/4: Original English (Send immediately before LLM to reduce delay)
                msg1 = f"""<font color="warning">🚨 特朗普在 Truth Social 发布了新动态 (1/4：英文原文)</font>\n
> **发布时间**: {post['published']}
> **原帖链接**: [点击查看原帖]({post['link']})

{post['title']}
"""
                notifier.send_markdown(msg1)
                
                # Use LLM to translate and analyze
                logging.info("Calling LLM for translation and analysis...")
                llm_result = llm_processor.process_post(post['content'])
                
                if not llm_result:
                    logging.error("LLM processing failed, skipping send for remaining parts.")
                    continue
                
                # Message 2/4: Translation
                msg2 = f"""<font color="info">📄 特朗普新动态 (2/4：中文翻译)</font>\n\n{llm_result.get('translation', '无内容')}"""
                notifier.send_markdown(msg2)
                time.sleep(1)
                
                # Message 3/4: Analysis
                msg3 = f"""<font color="info">🔍 特朗普新动态 (3/4：深度解读)</font>\n\n{llm_result.get('analysis', '无内容')}"""
                notifier.send_markdown(msg3)
                time.sleep(1)
                
                # Message 4/4: Advice
                msg4 = f"""<font color="info">💡 特朗普新动态 (4/4：投资建议)</font>\n\n{llm_result.get('advice', '无内容')}"""
                notifier.send_markdown(msg4)
                
            time.sleep(10)
            
    except KeyboardInterrupt:
        logging.info("Monitor stopped by user.")

if __name__ == "__main__":
    main()
