import requests
import logging

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
            logging.error("PushPlus Token is not configured.")
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
            if 'response' in locals() and hasattr(response, 'text'):
                logging.error(f"Response text: {response.text}")
            return False
