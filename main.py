import httpx
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Image, Plain # 保持导入

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚 Wiki 助手", "1.0.0")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://terraria.wiki.gg/zh/api.php"

    @filter.command("tr")
    async def search_wiki(self, event: AstrMessageEvent, keyword: str):
        '''查询泰拉瑞亚 Wiki。用法: /tr [关键词]'''
        
        yield event.plain_result(f"🔍 正在从 Wiki 搬运【{keyword}】的信息...")

        async with httpx.AsyncClient() as client:
            try:
                # 1. 搜索
                search_params = {"action": "query", "list": "search", "srsearch": keyword, "format": "json", "srlimit": 1}
                search_res = await client.get(self.api_url, params=search_params)
                search_data = search_res.json()

                if not search_data['query']['search']:
                    yield event.plain_result(f"❌ 找不到词条。")
                    return

                real_title = search_data['query']['search'][0]['title']
                
                # 2. 详情
                detail_params = {
                    "action": "query", "prop": "extracts|pageimages", "exintro": True,
                    "explaintext": True, "titles": real_title, "pithumbsize": 500, "format": "json"
                }
                detail_res = await client.get(self.api_url, params=detail_params)
                pages = detail_res.json()['query']['pages']
                page_data = pages[list(pages.keys())[0]]

                summary = page_data.get('extract', '暂无介绍')[:150] + "..."
                image_url = page_data.get('thumbnail', {}).get('source')
                wiki_link = f"https://terraria.wiki.gg/zh/{real_title.replace(' ', '_')}"

                # 3. 构建消息链 (使用这种最保险的构造方式)
                # 直接在列表里放进所有组件
                components = [
                    Plain(f"✨ 【{real_title}】\n\n"),
                ]
                
                if image_url:
                    components.append(Image.fromURL(image_url))
                
                components.append(Plain(f"\n📖 简介：{summary}\n"))
                components.append(Plain(f"\n🔗 详情：{wiki_link}"))

                # 用 components 列表直接创建 MessageChain
                chain = MessageChain(components)

                yield event.chain_result(chain)

            except Exception as e:
                yield event.plain_result(f"⚠️ 查询发生错误: {str(e)}")
