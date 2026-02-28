import httpx
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Image

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚 Wiki 助手", "1.0.0")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://terraria.wiki.gg/zh/api.php"

    @filter.command("tr")
    async def search_wiki(self, event: AstrMessageEvent, keyword: str):
        '''查询泰拉瑞亚 Wiki 并返回图片和简介。用法: /tr [关键词]'''
        
        yield event.plain_result(f"🔍 正在从 Wiki 搬运【{keyword}】的信息...")

        async with httpx.AsyncClient() as client:
            try:
                # 1. 搜索词条
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
                    yield event.plain_result(f"❌ 找不到关于“{keyword}”的词条。")
                    return

                real_title = search_data['query']['search'][0]['title']
                
                # 2. 获取详情
                detail_params = {
                    "action": "query",
                    "prop": "extracts|pageimages",
                    "exintro": True,
                    "explaintext": True,
                    "titles": real_title,
                    "pithumbsize": 500,
                    "format": "json"
                }
                detail_res = await client.get(self.api_url, params=detail_params)
                pages = detail_res.json()['query']['pages']
                page_id = list(pages.keys())[0]
                page_data = pages[page_id]

                summary = page_data.get('extract', '暂无详细介绍').strip()
                if len(summary) > 150:
                    summary = summary[:150] + "..."
                
                image_url = page_data.get('thumbnail', {}).get('source')
                wiki_link = f"https://terraria.wiki.gg/zh/{real_title.replace(' ', '_')}"

                # 3. 构建消息链 (注意这里使用了 .text 而不是 .plain)
                chain = MessageChain()
                chain.text(f"✨ 【{real_title}】\n\n")
                
                if image_url:
                    chain.message_components.append(Image.fromURL(image_url))
                
                chain.text(f"\n📖 简介：{summary}\n")
                chain.text(f"\n🔗 详情：{wiki_link}")

                yield event.chain_result(chain)

            except Exception as e:
                yield event.plain_result(f"⚠️ 查询发生错误: {str(e)}")
