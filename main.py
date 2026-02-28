import httpx
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api.messge_components import Image

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚 Wiki 助手", "1.0.0")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://terraria.wiki.gg/zh/api.php"

    @filter.command("tr")
    async def search_wiki(self, event: AstrMessageEvent, keyword: str):
        '''查询泰拉瑞亚 Wiki 并返回图片和简介。用法: /tr [关键词]'''
        
        # 先给用户一个反馈，避免加载太久没反应
        yield event.plain_result(f"🔍 正在从 Wiki 搬运【{keyword}】的信息...")

        async with httpx.AsyncClient() as client:
            try:
                # 第一步：搜索词条，获取最匹配的标题
                search_params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": keyword,
                    "format": "json",
                    "srlimit": 1
                }
                search_res = await client.get(self.api_url, params=search_params)
                search_data = search_res.json()

                if not search_data['query']['search']:
                    yield event.plain_result(f"❌ 哎呀，没找到关于“{keyword}”的词条。")
                    return

                # 获取正式的标题（比如搜“土块”得到“土块”）
                real_title = search_data['query']['search'][0]['title']
                
                # 第二步：获取详情（图片地址 + 文本简介）
                detail_params = {
                    "action": "query",
                    "prop": "extracts|pageimages",
                    "exintro": True,      # 只要开头的简介
                    "explaintext": True,  # 只要纯文本，不要HTML标签
                    "titles": real_title,
                    "pithumbsize": 500,   # 设置图片宽度最大为500像素
                    "format": "json"
                }
                detail_res = await client.get(self.api_url, params=detail_params)
                pages = detail_res.json()['query']['pages']
                
                # 提取页面数据
                page_id = list(pages.keys())[0]
                page_data = pages[page_id]

                # 提取简介（截取前150字防止刷屏）
                summary = page_data.get('extract', '暂无详细介绍').strip()
                if len(summary) > 150:
                    summary = summary[:150] + "..."
                
                # 提取图片 URL
                image_url = page_data.get('thumbnail', {}).get('source')
                
                # 拼接完整的 Wiki 链接
                wiki_link = f"https://terraria.wiki.gg/zh/{real_title.replace(' ', '_')}"

                # 第三步：构建包含图片和文字的消息
                chain = MessageChain()
                chain.plain(f"✨ 【{real_title}】\n\n")
                
                # 如果有图片就加上图片
                if image_url:
                    chain.message_components.append(Image.fromURL(image_url))
                
                chain.plain(f"\n📖 简介：{summary}\n")
                chain.plain(f"\n🔗 详情：{wiki_link}")

                # 发送最终结果
                yield event.chain_result(chain)

            except Exception as e:
                yield event.plain_result(f"⚠️ 查询时发生错误: {str(e)}")
