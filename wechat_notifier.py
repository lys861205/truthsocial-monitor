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
            return False

        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        try:
            content_bytes = content.encode('utf-8')
            if len(content_bytes) > 4000:
                truncated_bytes = content_bytes[:3900]
                content = truncated_bytes.decode('utf-8', errors='ignore') + "\n\n...(内容过长已截断)"
                data["markdown"]["content"] = content

            response = requests.post(self.webhook_url, json=data, timeout=5)
            result = response.json()
            if result.get("errcode") != 0:
                logging.error(f"WeChat API returned error: {result}")
                return False
                
            logging.info("Message successfully sent to WeChat Webhook.")
            return True
        except Exception as e:
            logging.error(f"Failed to send message to WeChat: {e}")
            return False

class PushPlusNotifier:
    def __init__(self, token, topic=None):
        self.token = token
        self.topic = topic
        self.api_url = "http://www.pushplus.plus/send"

    def send_markdown(self, title, content):
        """
        Sends a Markdown message via PushPlus.
        """
        if not self.token:
            return False

        data = {
            "token": self.token,
            "title": title,
            "content": content,
            "template": "markdown"
        }
        
        if self.topic:
            data["topic"] = self.topic
            
        try:
            response = requests.post(self.api_url, json=data, timeout=5)
            result = response.json()
            if result.get("code") != 200:
                logging.error(f"PushPlus API returned error: {result}")
                return False
                
            logging.info("Message successfully sent via PushPlus.")
            return True
        except Exception as e:
            logging.error(f"Failed to send message via PushPlus: {e}")
            return False
