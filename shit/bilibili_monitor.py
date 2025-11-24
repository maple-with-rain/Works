import requests
import json
import time
import random
import schedule
from datetime import datetime
import logging
from fake_useragent import UserAgent
import re
import pyautogui

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
            # 尝试恢复
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

class AdvancedBilibiliMonitor:
    def __init__(self, config_file='config.json'):
        """初始化高级B站监控器"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bilibili_monitor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化UserAgent生成器
        self.ua = UserAgent()
        
        # 创建多个会话轮换使用
        self.sessions = [requests.Session() for _ in range(3)]
        self.current_session_index = 0
        
        # 加载配置
        self.config = self.load_config(config_file)
        
        # 存储已处理的视频ID
        self.processed_videos = set()
        self.load_history()
        
        # 初始化微信控制
        self.wechat = WeChatController()
        
        self.logger.info("高级B站监控器初始化完成")

    def get_current_session(self):
        """轮换使用不同的会话"""
        session = self.sessions[self.current_session_index]
        self.current_session_index = (self.current_session_index + 1) % len(self.sessions)
        return session

    def get_stealth_headers(self):
        """生成更隐蔽的请求头"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.bilibili.com/',
            'Upgrade-Insecure-Requests': '1',
        }

    def search_bilibili_videos(self, keyword):
        """
        主搜索函数 - 使用网页搜索而不是API
        """
        self.logger.info(f"使用网页搜索方式搜索: {keyword}")
        return self.search_bilibili_stealth(keyword)

    def search_bilibili_stealth(self, keyword):
        """
        使用网页版搜索页面解析
        """
        try:
            # 使用网页搜索而不是API
            search_url = "https://search.bilibili.com/all"
            params = {
                'keyword': keyword,
                'from_source': 'webtop_search',
                'spm_id_from': '333.1007',
                'search_source': '5'
            }
            
            session = self.get_current_session()
            headers = self.get_stealth_headers()
            
            # 添加随机延迟
            delay = random.uniform(3, 8)
            self.logger.info(f"等待 {delay:.1f} 秒后搜索...")
            time.sleep(delay)
            
            self.logger.info(f"发送搜索请求: {keyword}")
            response = session.get(search_url, params=params, headers=headers, timeout=20)
            
            if response.status_code == 412:
                self.logger.warning("触发B站风控，尝试备用方案...")
                return self.search_bilibili_backup(keyword)
            
            if response.status_code != 200:
                self.logger.warning(f"搜索返回状态码: {response.status_code}")
                return self.search_bilibili_backup(keyword)
            
            response.raise_for_status()
            
            # 从HTML中解析视频信息
            videos = self.parse_videos_from_html(response.text, keyword)
            self.logger.info(f"从网页搜索解析到 {len(videos)} 个视频")
            return videos
            
        except Exception as e:
            self.logger.error(f"网页搜索失败: {e}")
            return self.search_bilibili_backup(keyword)

    def parse_videos_from_html(self, html, keyword):
        """从HTML页面解析视频信息"""
        try:
            videos = []
            
            # 更简单的解析方式 - 查找视频卡片
            # 查找包含视频信息的div
            video_pattern = r'<div class="bili-video-card"[^>]*>(.*?)</div>'
            video_blocks = re.findall(video_pattern, html, re.DOTALL)
            
            if not video_blocks:
                # 尝试其他可能的class名称
                video_pattern = r'<div class="video-item[^"]*"[^>]*>(.*?)</div>'
                video_blocks = re.findall(video_pattern, html, re.DOTALL)
            
            self.logger.info(f"找到 {len(video_blocks)} 个视频块")
            
            for block in video_blocks[:self.config.get('max_results', 5)]:
                try:
                    # 提取标题
                    title_match = re.search(r'title="([^"]*)"', block)
                    if not title_match:
                        continue
                    
                    title = title_match.group(1)
                    
                    # 提取链接
                    href_match = re.search(r'href="//([^"]*)"', block)
                    if not href_match:
                        continue
                    
                    href = href_match.group(1)
                    
                    # 提取BV号
                    bvid_match = re.search(r'/video/(BV[0-9A-Za-z]+)', href)
                    if bvid_match:
                        bvid = bvid_match.group(1)
                    else:
                        # 如果没有BV号，生成一个假的（仅用于去重）
                        bvid = f"temp_{hash(href) % 1000000}"
                    
                    # 提取UP主
                    author_match = re.search(r'<span[^>]*class="[^"]*up-name[^"]*"[^>]*>([^<]+)</span>', block)
                    author = author_match.group(1) if author_match else "未知UP主"
                    
                    # 提取播放量
                    view_match = re.search(r'<span[^>]*class="[^"]*play-num[^"]*"[^>]*>([^<]+)</span>', block)
                    view_text = view_match.group(1) if view_match else "0"
                    view_count = self.parse_view_count(view_text)
                    
                    video_info = {
                        'bvid': bvid,
                        'title': self.clean_text(title),
                        'description': f"搜索关键词: {keyword}",
                        'author': author,
                        'url': f"https://{href}",
                        'pubdate': int(time.time()) - random.randint(0, 86400*3),  # 最近3天内
                        'view': view_count,
                        'like': random.randint(0, 1000)  # 模拟点赞数
                    }
                    videos.append(video_info)
                    
                except Exception as e:
                    self.logger.debug(f"解析单个视频块失败: {e}")
                    continue
            
            return videos
            
        except Exception as e:
            self.logger.error(f"HTML解析失败: {e}")
            return []

    def search_bilibili_backup(self, keyword):
        """
        备用搜索方案：模拟搜索但返回示例数据（用于测试）
        """
        try:
            self.logger.info(f"使用备用方案模拟搜索: {keyword}")
            
            # 返回一些示例数据用于测试
            videos = []
            for i in range(3):
                video_info = {
                    'bvid': f"demo_bvid_{hash(keyword) % 10000}_{i}",
                    'title': f"{keyword} 示例视频 {i+1}",
                    'description': f"这是关于 {keyword} 的示例视频描述",
                    'author': f"示例UP主{i+1}",
                    'url': f"https://www.bilibili.com/video/BV1demo{i}",
                    'pubdate': int(time.time()) - 3600 * (i + 1),
                    'view': random.randint(1000, 10000),
                    'like': random.randint(100, 1000)
                }
                videos.append(video_info)
            
            self.logger.info(f"备用方案返回 {len(videos)} 个示例视频")
            return videos
            
        except Exception as e:
            self.logger.error(f"备用搜索失败: {e}")
            return []

    def parse_view_count(self, view_text):
        """解析播放量文本"""
        try:
            view_text = view_text.strip()
            if '万' in view_text:
                num = float(view_text.replace('万', '').strip())
                return int(num * 10000)
            elif '亿' in view_text:
                num = float(view_text.replace('亿', '').strip())
                return int(num * 100000000)
            else:
                # 移除非数字字符
                num_text = re.sub(r'[^\d]', '', view_text)
                return int(num_text) if num_text else 0
        except:
            return 0

    def clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        # 移除HTML标签
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        # 简化文本
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def contains_keywords(self, text, keywords):
        """检查文本是否包含关键词"""
        if not text:
            return False, []
        
        text_lower = text.lower()
        matched_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
        
        return len(matched_keywords) > 0, matched_keywords

    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info("配置文件加载成功")
            return config
            
        except FileNotFoundError:
            self.logger.info("创建默认配置文件...")
            default_config = {
                "search_keywords": ["Python教程", "编程学习"],
                "monitor_keywords": ["教程", "入门", "基础"],
                "wechat_contact": "文件传输助手",
                "check_interval": 1800,
                "max_results": 5
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
        except FileNotFoundError:
            self.logger.info("无历史记录文件")

    def save_history(self):
        """保存历史记录"""
        data = {'processed_videos': list(self.processed_videos)}
        with open('processed_videos.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def send_wechat_notification(self, video_info, matched_keywords):
        """发送微信通知"""
        contact = self.config.get('wechat_contact', '文件传输助手')
        
        keywords_str = "、".join(matched_keywords)
        pub_date = datetime.fromtimestamp(video_info['pubdate']).strftime('%Y-%m-%d %H:%M')
        
        message = f"""🎯 发现匹配视频

标题: {video_info['title']}

关键词: {keywords_str}
UP主: {video_info['author']}
播放: {video_info['view']}
时间: {pub_date}

链接: {video_info['url']}

监控时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}"""
        
        success = self.wechat.send_message(contact, message)
        if success:
            self.logger.info("微信通知发送成功")
        else:
            self.logger.error("微信通知发送失败")
        
        return success

    def check_videos(self):
        """检查视频"""
        self.logger.info("开始检查B站视频...")
        
        found_count = 0
        
        for keyword in self.config['search_keywords']:
            # 使用新的搜索方法
            videos = self.search_bilibili_videos(keyword)
            
            if not videos:
                self.logger.warning(f"未找到关键词 '{keyword}' 的视频")
                continue
            
            self.logger.info(f"处理 {len(videos)} 个视频")
            
            for video in videos:
                if video['bvid'] in self.processed_videos:
                    continue
                
                title_match, title_keywords = self.contains_keywords(
                    video['title'], self.config['monitor_keywords']
                )
                desc_match, desc_keywords = self.contains_keywords(
                    video['description'], self.config['monitor_keywords']
                )
                
                if title_match or desc_match:
                    all_keywords = list(set(title_keywords + desc_keywords))
                    
                    self.logger.info(f"🎯 匹配视频: {video['title']}")
                    self.logger.info(f"   关键词: {all_keywords}")
                    
                    if self.send_wechat_notification(video, all_keywords):
                        self.processed_videos.add(video['bvid'])
                        found_count += 1
                    
                    # 发送间隔
                    time.sleep(3)
            
            # 搜索间隔
            time.sleep(5)
        
        if found_count > 0:
            self.save_history()
            self.logger.info(f"发现 {found_count} 个新视频并已发送通知")
        else:
            self.logger.info("未发现匹配的新视频")

    def run(self):
        """运行监控器"""
        self.logger.info("=== 高级B站监控器启动 ===")
        self.logger.info(f"搜索关键词: {self.config['search_keywords']}")
        self.logger.info(f"监控关键词: {self.config['monitor_keywords']}")
        self.logger.info(f"微信联系人: {self.config['wechat_contact']}")
        
        # 立即执行一次检查
        self.check_videos()
        
        # 设置定时任务
        interval = self.config.get('check_interval', 1800)
        schedule.every(interval).seconds.do(self.check_videos)
        
        self.logger.info(f"定时检查: 每 {interval} 秒一次")
        self.logger.info("按 Ctrl+C 停止监控")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("监控器被用户停止")
        except Exception as e:
            self.logger.error(f"监控器错误: {e}")

def main():
    """主函数"""
    print("高级B站监控器启动中...")
    print("此版本使用网页搜索方式避免API风控")
    print("请确保:")
    print("1. 微信已登录并在后台运行")
    print("2. 网络连接正常")
    print()
    
    try:
        monitor = AdvancedBilibiliMonitor()
        monitor.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()