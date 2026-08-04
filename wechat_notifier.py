import requests
import logging

class WeChatNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_markdown(self, content):
        """
        Sends a Markdown message to the Enterprise WeChat Group Bot.
        """
        if not self.webhook_url:
            logging.error("Webhook URL is not configured.")
            return False

        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        try:
            # 微信企业端 markdown 限制最大 4096 字节
            content_bytes = content.encode('utf-8')
            if len(content_bytes) > 4000:
                logging.warning(f"Message too long ({len(content_bytes)} bytes), truncating to fit WeChat limits...")
                # 截断，保留前3900字节，并在末尾加上截断提示
                truncated_bytes = content_bytes[:3900]
                content = truncated_bytes.decode('utf-8', errors='ignore') + "\n\n...(内容过长已截断)"
                
                data["markdown"]["content"] = content

            response = requests.post(self.webhook_url, json=data, timeout=5)
            result = response.json()
            if result.get("errcode") != 0:
                logging.error(f"WeChat API returned error: {result}")
                return False
                
            logging.info("Message successfully sent to WeChat.")
            return True
        except Exception as e:
            logging.error(f"Failed to send message to WeChat: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                logging.error(f"Response text: {response.text}")
            return False
