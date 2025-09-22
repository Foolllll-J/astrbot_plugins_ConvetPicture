import os
import aiohttp
from astrbot import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.core.platform import MessageType

# 定义下载目录，确保无论插件放在哪里，都能找到正确的路径
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloaded_files')

async def download_image(picture_url, save_path):
    """
    异步下载图片并保存到指定路径。
    在保存前会确保目录存在。
    """
    try:
        dir_name = os.path.dirname(save_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(picture_url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(save_path, 'wb') as f:
                        f.write(content)
                    return True
                else:
                    logger.error(f"图片下载失败，HTTP状态码：{response.status}")
                    return False
    except Exception as e:
        logger.error(f"下载图片时出错: {e}")
        return False

@register("Convert", "orchidsziyou", "qq表情转化成可以保存的图片", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    @filter.command("转换")
    async def convert_command(self, event: AstrMessageEvent):
        """这是一个转换图片格式指令"""
        event.should_call_llm(False)
        message_chain = event.get_messages()

        for msg in message_chain:
            # 处理直接发送的图片
            if msg.type == 'Image':
                picture_id = msg.file
                client = event.bot
                
                # 获取图片本地路径
                response = await client.api.call_action('get_image', file_id=picture_id)
                local_disk_path = response['file']
                abs_path = os.path.abspath(local_disk_path)
                
                # 根据文件后缀确定文件名
                filename = ""
                if abs_path.endswith(".jpg"):
                    filename = "图片.jpg"
                elif abs_path.endswith(".png"):
                    filename = "图片.png"
                elif abs_path.endswith(".gif"):
                    filename = "图片.gif"

                file_url = f'file://{abs_path}'

                # 发送文件给用户或群组
                if event.get_message_type() == MessageType.FRIEND_MESSAGE:
                    user_id = event.get_sender_id()
                    payloads = {"user_id": user_id, "message": [{"type": "file", "data": {"file": file_url, "name": filename}}]}
                    await client.api.call_action('send_private_msg', **payloads)
                elif event.get_message_type() == MessageType.GROUP_MESSAGE:
                    group_id = event.get_group_id()
                    payloads = {"group_id": group_id, "message": [{"type": "file", "data": {"file": file_url, "name": filename}}]}
                    await client.api.call_action('send_group_msg', **payloads)
                
                event.stop_event()
                return

            # 处理引用的图片
            elif msg.type == 'Reply':
                client = event.bot
                payload = {"message_id": msg.id}
                response = await client.api.call_action('get_msg', **payload)
                reply_msg = response['message']
                
                for m in reply_msg:
                    if m['type'] == 'image':
                        picture_url = m['data']['url']
                        
                        # 官方表情无法直接通过文件ID获取，需要下载
                        if "/club/item/" in picture_url:
                            save_path = os.path.join(DOWNLOAD_DIR, 'downloaded_image.jpg')
                            result = await download_image(picture_url, save_path)
                            if result:
                                file_url = f'file://{save_path}'
                                if event.get_message_type() == MessageType.FRIEND_MESSAGE:
                                    user_id = event.get_sender_id()
                                    payloads = {"user_id": user_id, "message": [{"type": "file", "data": {"file": file_url, "name": "图片.jpg"}}]}
                                    await client.api.call_action('send_private_msg', **payloads)
                                elif event.get_message_type() == MessageType.GROUP_MESSAGE:
                                    group_id = event.get_group_id()
                                    payloads = {"group_id": group_id, "message": [{"type": "file", "data": {"file": file_url, "name": "图片.jpg"}}]}
                                    await client.api.call_action('send_group_msg', **payloads)
                            else:
                                yield event.plain_result("图片下载失败")
                        else:
                            # 非官方表情，直接通过文件ID获取
                            picture_id = m['data']['file']
                            response = await client.api.call_action('get_image', file_id=picture_id)
                            local_disk_path = response['file']
                            abs_path = os.path.abspath(local_disk_path)
                            
                            filename = ""
                            if abs_path.endswith(".jpg"):
                                filename = "图片.jpg"
                            elif abs_path.endswith(".png"):
                                filename = "图片.png"
                            elif abs_path.endswith(".gif"):
                                filename = "图片.gif"

                            file_url = f'file://{abs_path}'

                            if event.get_message_type() == MessageType.FRIEND_MESSAGE:
                                user_id = event.get_sender_id()
                                payloads = {"user_id": user_id, "message": [{"type": "file", "data": {"file": file_url, "name": filename}}]}
                                await client.api.call_action('send_private_msg', **payloads)
                            elif event.get_message_type() == MessageType.GROUP_MESSAGE:
                                group_id = event.get_group_id()
                                payloads = {"group_id": group_id, "message": [{"type": "file", "data": {"file": file_url, "name": filename}}]}
                                await client.api.call_action('send_group_msg', **payloads)

                        event.stop_event()
                        return
