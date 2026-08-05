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
                
                # ------ 0. 过滤无文字内容的帖子 ------
                if not post.get('content') or not post['content'].strip():
                    logging.info("Post has no text content (e.g. only images/videos). Skipping push.")
                    continue
                
                # ------ 1. 先调用大模型进行分析和过滤 ------
                logging.info("Calling LLM for translation, analysis, and filtering...")
                llm_result = llm_processor.process_post(post['content'])
                
                if not llm_result:
                    logging.error("LLM processing failed, skipping this post to maintain quality.")
                    continue
                    
                # 检查 AI 过滤标签
                if llm_result.get('is_valuable') is False:
                    logging.info("AI determined this post is NOT valuable (noise/propaganda). Skipping push.")
                    continue
                    
                # ------ 2. 推送原文 (1/4) ------
                title1 = "🚨 特朗普发布了新动态 (1/4：英文原文)"
                
                if wechat_notifier:
                    msg1_wechat = f"""<font color="warning">{title1}</font>\n
> **发布时间**: {post['published']}
> **原帖链接**: [点击查看原帖]({post['link']})

{post['title']}"""
                    wechat_notifier.send_markdown(msg1_wechat)
                    
                if feishu_notifier:
                    msg1_feishu = f"**发布时间**: {post['published']}\n**原帖链接**: [点击查看原帖]({post['link']})\n\n{post['title']}"
                    feishu_notifier.send_markdown(title1, msg1_feishu)
                
                time.sleep(1) # 小幅停顿，确保消息顺序
                
                # ------ 3.1 翻译 (2/4) ------
                title2 = "📄 特朗普新动态 (2/4：中文翻译)"
                content2 = llm_result.get('translation', '无内容')
                
                if wechat_notifier:
                    wechat_notifier.send_markdown(f"""<font color="info">{title2}</font>\n\n{content2}""")
                if feishu_notifier:
                    feishu_notifier.send_markdown(title2, content2)
                    
                time.sleep(1)
                
                # ------ 3.2 深度解读 (3/4) ------
                title3 = "🔍 特朗普新动态 (3/4：深度解读)"
                content3 = llm_result.get('analysis', '无内容')
                
                if wechat_notifier:
                    wechat_notifier.send_markdown(f"""<font color="info">{title3}</font>\n\n{content3}""")
                if feishu_notifier:
                    feishu_notifier.send_markdown(title3, content3)
                    
                time.sleep(1)
                
                # ------ 3.3 投资建议 (4/4) ------
                title4 = "💡 特朗普新动态 (4/4：投资建议)"
                content4 = llm_result.get('advice', '无内容')
                
                if wechat_notifier:
                    wechat_notifier.send_markdown(f"""<font color="info">{title4}</font>\n\n{content4}""")
                if feishu_notifier:
                    feishu_notifier.send_markdown(title4, content4)
                
            time.sleep(10)
            
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
