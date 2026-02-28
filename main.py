import httpx
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star, register

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚 Wiki 助手", "1.0.0")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 这里的 tr 就是你在机器人里输入的指令，比如 /tr 泰拉刃
    @filter.command("tr")
    async def search_wiki(self, event: AstrMessageEvent, keyword: str):
        '''查询泰拉瑞亚 Wiki。用法: /tr [关键词]'''
        
        yield event.plain_result(f"🔍 正在查询 Wiki 中的 {keyword}...")

        api_url = "https://terraria.wiki.gg/zh/api.php"
        
        async with httpx.AsyncClient() as client:
            try:
                # 访问 Wiki 的搜索接口
                params = {
                    "action": "opensearch",
                    "search": keyword,
                    "limit": 1,
                    "format": "json"
                }
                res = await client.get(api_url, params=params)
                data = res.json()

                # data[1] 是标题列表，data[3] 是链接列表
                if data[1]:
                    title = data[1][0]
                    link = data[3][0]
                    yield event.plain_result(f"✅ 找到啦！\n标题：{title}\n链接：{link}")
                else:
                    yield event.plain_result(f"❌ 没找到关于“{keyword}”的内容。")
            
            except Exception as e:
                yield event.plain_result(f"⚠️ 出错了: {str(e)}")
