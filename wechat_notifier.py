import requests
import logging
import time
import hmac
import hashlib
import base64
import urllib.parse

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

class FeishuNotifier:
    def __init__(self, webhook_url, secret=None):
        self.webhook_url = webhook_url
        self.secret = secret

    def send_markdown(self, title, content):
        if not self.webhook_url:
            return False

        payload = {
            "msg_type": "interactive",
            "card": {
                "elements": [{
                    "tag": "markdown",
                    "content": content
                }],
                "header": {
                    "template": "blue",
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    }
                }
            }
        }

        if self.secret:
            timestamp = str(int(time.time()))
            string_to_sign = '{}\\n{}'.format(timestamp, self.secret)
            hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
            sign = base64.b64encode(hmac_code).decode('utf-8')
            payload["timestamp"] = timestamp
            payload["sign"] = sign

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=5)
            if resp.json().get("code") != 0:
                logging.error(f"Feishu API error: {resp.json()}")
                return False
            logging.info("Message successfully sent via Feishu.")
            return True
        except Exception as e:
            logging.error(f"Failed to send message via Feishu: {e}")
            return False

class DingTalkNotifier:
    def __init__(self, webhook_url, secret=None):
        self.webhook_url = webhook_url
        self.secret = secret

    def send_markdown(self, title, content):
        if not self.webhook_url:
            return False

        url = self.webhook_url
        if self.secret:
            timestamp = str(round(time.time() * 1000))
            secret_enc = self.secret.encode('utf-8')
            string_to_sign = '{}\\n{}'.format(timestamp, self.secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            }
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=5)
            if resp.json().get("errcode") != 0:
                logging.error(f"DingTalk API error: {resp.json()}")
                return False
            logging.info("Message successfully sent via DingTalk.")
            return True
        except Exception as e:
            logging.error(f"Failed to send message via DingTalk: {e}")
            return False
