import time
import feedparser
import logging
import requests
import concurrent.futures

class TruthSocialMonitor:
    def __init__(self):
        self.rss_url = "https://trumpstruth.org/feed"
        self.api_url = "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses?limit=5"
        self.state_file = "last_post_id.txt"
        self.last_post_id = self._load_state()
        
    def _load_state(self):
        try:
            with open(self.state_file, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
            
    def _save_state(self, post_id):
        with open(self.state_file, "w") as f:
            f.write(post_id)

    def _fetch_rss(self):
        try:
            feed = feedparser.parse(self.rss_url)
            if feed.entries:
                latest_entry = feed.entries[0]
                # 使用 truth:originalId 统一 ID 体系
                post_id = getattr(latest_entry, 'truth_originalid', latest_entry.guid)
                return {
                    "id": post_id,
                    "title": latest_entry.title,
                    "link": getattr(latest_entry, 'truth_originalurl', latest_entry.link),
                    "published": latest_entry.published,
                    "content": latest_entry.description,
                    "source": "RSS"
                }
        except Exception as e:
            logging.debug(f"RSS Fetch Error: {e}")
        return None

    def _fetch_api(self):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
            # 请求 Mastodon 兼容 API
            response = requests.get(self.api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    latest_post = data[0]
                    # Mastodon API 直接返回 original ID
                    post_id = str(latest_post.get("id"))
                    # Mastodon 返回的内容包含 HTML，也可以使用 text 提取纯文本（这里保留原始逻辑）
                    import re
                    content_html = latest_post.get("content", "")
                    # 简单去除 HTML 标签作为 title 备用（如果没有提供）
                    raw_text = re.sub(r'<[^>]+>', '', content_html)
                    return {
                        "id": post_id,
                        "title": raw_text,
                        "link": latest_post.get("url"),
                        "published": latest_post.get("created_at"),
                        "content": content_html,
                        "source": "API"
                    }
        except Exception as e:
            logging.debug(f"API Fetch Error: {e}")
        return None

    def get_latest_post(self):
        """
        Fetches the latest post from both RSS and API concurrently.
        Returns the first successfully fetched new post.
        """
        post = None
        
        # 并发请求两个源，以最快返回且有效的为准
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_api = executor.submit(self._fetch_api)
            future_rss = executor.submit(self._fetch_rss)
            
            for future in concurrent.futures.as_completed([future_api, future_rss]):
                result = future.result()
                if result:
                    post_id = result["id"]
                    # 忽略已经处理过的帖子
                    if self.last_post_id == post_id:
                        continue
                        
                    # 找到了新帖子
                    post = result
                    break # 取消等待另一个源，直接使用最快的这个
                    
        if not post:
            return None

        post_id = post["id"]
        
        if self.last_post_id is None:
            logging.info(f"第一次运行，获取到当前最新帖子 {post_id} (来源: {post['source']})。将推送此帖以供测试。")
        else:
            logging.info(f"发现新帖子！(来源: {post['source']}) 更新本地记录为: {post_id}")
            
        self.last_post_id = post_id
        self._save_state(post_id)
        
        return post
