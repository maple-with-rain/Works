import requests
import json
import time
import random
import schedule
from datetime import datetime
import logging
import pyautogui
import re

class WeChatController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def send_message(self, contact_name, message):
        """发送微信消息"""
        try:
            self.logger.info(f"准备发送消息给: {contact_name}")
            
            # 激活微信
            pyautogui.hotkey('ctrl', 'alt', 'w')
            time.sleep(3)
            
            # 搜索联系人
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            pyautogui.write(contact_name)
            time.sleep(2)
            pyautogui.press('enter')
            time.sleep(2)
            
            # 发送消息
            messages = self.split_message(message)
            for msg in messages:
                pyautogui.write(msg, interval=0.05)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(1)
            
            # 返回
            pyautogui.hotkey('ctrl', 'alt', 'w')
            
            self.logger.info("消息发送成功")
            return True
            
        except Exception as e:
            self.logger.error(f"发送失败: {e}")
            try:
                pyautogui.hotkey('ctrl', 'alt', 'w')
            except:
                pass
            return False

    def split_message(self, message, max_length=100):
        """分割长消息"""
        if len(message) <= max_length:
            return [message]
        
        lines = message.split('\n')
        result = []
        current_message = ""
        
        for line in lines:
            if len(current_message) + len(line) + 1 > max_length:
                if current_message:
                    result.append(current_message.strip())
                current_message = line
            else:
                if current_message:
                    current_message += "\n" + line
                else:
                    current_message = line
        
        if current_message:
            result.append(current_message.strip())
        
        return result

class SimpleBilibiliMonitor:
    def __init__(self, config_file='config.json'):
        """初始化简单B站监控器"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bilibili_monitor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config = self.load_config(config_file)
        
        # 创建会话
        self.session = requests.Session()
        
        # 设置真实的浏览器头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.bilibili.com/',
        })
        
        # 存储已处理的视频ID
        self.processed_videos = set()
        self.load_history()
        
        # 初始化微信控制
        self.wechat = WeChatController()
        
        self.logger.info("简单B站监控器初始化完成")

    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info("配置文件加载成功")
            return config
        except:
            # 默认配置
            default_config = {
                "search_keywords": ["Python教程", "编程学习"],
                "wechat_contact": "文件传输助手",
                "check_interval": 1800,  # 30分钟检查一次
                "send_count": 3,        # 每次发送3个视频
                "max_retries": 3        # 最大重试次数
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config

    def load_history(self):
        """加载历史记录"""
        try:
            with open('processed_videos.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.processed_videos = set(data.get('processed_videos', []))
            self.logger.info(f"加载了 {len(self.processed_videos)} 个已处理视频")
        except:
            self.processed_videos = set()

    def save_history(self):
        """保存历史记录"""
        data = {'processed_videos': list(self.processed_videos)}
        with open('processed_videos.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def search_bilibili_direct(self, keyword, retry_count=0):
        """
        直接搜索B站并返回前几个视频
        使用移动端API，成功率更高
        """
        try:
            self.logger.info(f"搜索: {keyword}")
            
            # 使用移动端API
            url = "https://api.bilibili.com/x/web-interface/search/type"
            params = {
                'search_type': 'video',
                'keyword': keyword,
                'page': 1,
                'page_size': 10  # 获取10个，选择前几个发送
            }
            
            # 使用移动端User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36',
                'Referer': 'https://m.bilibili.com/',
            }
            
            # 随机延迟
            time.sleep(random.uniform(2, 5))
            
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 412:
                self.logger.warning("触发风控，等待后重试...")
                if retry_count < self.config.get('max_retries', 3):
                    time.sleep(30)
                    return self.search_bilibili_direct(keyword, retry_count + 1)
                else:
                    return []
            
            if response.status_code != 200:
                self.logger.warning(f"搜索失败，状态码: {response.status_code}")
                return []
            
            data = response.json()
            
            if data['code'] == 0 and data['data']['result']:
                videos = []
                for video in data['data']['result'][:self.config.get('send_count', 3)]:
                    video_info = {
                        'bvid': video.get('bvid', ''),
                        'title': video.get('title', ''),
                        'author': video.get('author', ''),
                        'url': f"https://www.bilibili.com/video/{video.get('bvid', '')}",
                        'view': video.get('play', 0),
                        'like': video.get('like', 0),
                        'duration': video.get('duration', ''),
                        'pubdate': video.get('pubdate', int(time.time()))
                    }
                    videos.append(video_info)
                
                self.logger.info(f"成功获取 {len(videos)} 个视频")
                return videos
            else:
                self.logger.warning("API返回数据异常")
                return []
                
        except Exception as e:
            self.logger.error(f"搜索异常: {e}")
            if retry_count < self.config.get('max_retries', 3):
                time.sleep(10)
                return self.search_bilibili_direct(keyword, retry_count + 1)
            return []

    def send_video_to_wechat(self, video_info, keyword):
        """发送单个视频到微信"""
        contact = self.config.get('wechat_contact', '文件传输助手')
        
        # 格式化发布时间
        pub_date = datetime.fromtimestamp(video_info['pubdate']).strftime('%Y-%m-%d %H:%M')
        
        # 格式化时长
        duration = self.format_duration(video_info['duration'])
        
        message = f"""🎬 推荐视频 - {keyword}

标题: {video_info['title']}

UP主: {video_info['author']}
播放: {video_info['view']} | 点赞: {video_info['like']}
时长: {duration} | 发布时间: {pub_date}

链接: {video_info['url']}

推荐时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}"""
        
        success = self.wechat.send_message(contact, message)
        return success

    def format_duration(self, duration):
        """格式化视频时长"""
        try:
            if ':' in str(duration):
                return duration
            seconds = int(duration)
            if seconds < 60:
                return f"0:{seconds:02d}"
            elif seconds < 3600:
                minutes = seconds // 60
                seconds = seconds % 60
                return f"{minutes}:{seconds:02d}"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60
                return f"{hours}:{minutes:02d}:{seconds:02d}"
        except:
            return str(duration)

    def check_and_send_videos(self):
        """检查并发送视频"""
        self.logger.info("开始检查并发送视频...")
        
        total_sent = 0
        
        for keyword in self.config['search_keywords']:
            self.logger.info(f"处理关键词: {keyword}")
            
            # 搜索视频
            videos = self.search_bilibili_direct(keyword)
            
            if not videos:
                self.logger.warning(f"未找到关键词 '{keyword}' 的视频")
                continue
            
            # 发送视频
            sent_count = 0
            for video in videos:
                # 检查是否已发送过
                if video['bvid'] in self.processed_videos:
                    self.logger.info(f"跳过已发送视频: {video['title'][:30]}...")
                    continue
                
                self.logger.info(f"发送视频: {video['title'][:40]}...")
                
                # 发送到微信
                if self.send_video_to_wechat(video, keyword):
                    self.processed_videos.add(video['bvid'])
                    sent_count += 1
                    total_sent += 1
                    self.logger.info("✅ 视频发送成功")
                else:
                    self.logger.error("❌ 视频发送失败")
                
                # 发送间隔
                time.sleep(random.uniform(3, 6))
            
            self.logger.info(f"关键词 '{keyword}' 发送了 {sent_count} 个视频")
            
            # 关键词间间隔
            if len(self.config['search_keywords']) > 1:
                time.sleep(random.uniform(5, 10))
        
        if total_sent > 0:
            self.save_history()
            self.logger.info(f"🎉 本轮共发送 {total_sent} 个新视频")
        else:
            self.logger.info("ℹ️  本轮没有新视频需要发送")
        
        self.logger.info("本轮检查完成")

    def run(self):
        """运行监控器"""
        self.logger.info("🚀 B站视频推荐器启动")
        self.logger.info(f"📝 搜索关键词: {self.config['search_keywords']}")
        self.logger.info(f"💬 微信联系人: {self.config['wechat_contact']}")
        self.logger.info(f"📤 每次发送: {self.config.get('send_count', 3)} 个视频")
        self.logger.info(f"⏰ 检查间隔: {self.config['check_interval']} 秒")
        
        # 立即执行一次
        self.check_and_send_videos()
        
        # 设置定时任务
        interval = self.config.get('check_interval', 1800)
        schedule.every(interval).seconds.do(self.check_and_send_videos)
        
        self.logger.info(f"🔄 定时任务已设置: 每 {interval} 秒执行一次")
        self.logger.info("⏹️  按 Ctrl+C 停止程序")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("🛑 程序被用户停止")

def main():
    """主函数"""
    print("=" * 50)
    print("B站视频推荐器")
    print("特点: 直接搜索并转发前几个视频")
    print("=" * 50)
    print()
    
    try:
        monitor = SimpleBilibiliMonitor()
        monitor.run()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()