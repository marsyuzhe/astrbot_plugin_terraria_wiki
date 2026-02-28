from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import httpx

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚百科查询插件", "1.0.0")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 这里的指令触发词是 /tr 物品名
    @filter.command("tr")
    async def search_wiki(self, event: AstrMessageEvent, item_name: str):
        '''查询泰拉瑞亚 Wiki 物品信息'''
        
        # 提示用户正在查询，增强互动感
        yield event.plain_result(f"🔍 正在为你去 Wiki.gg 翻找关于 '{item_name}' 的资料...")

        base_url = "https://terraria.wiki.gg/zh/api.php" # 中文 Wiki
        
        try:
            async with httpx.AsyncClient() as client:
                # 第一步：搜索最匹配的页面标题
                search_params = {
                    "action": "opensearch",
                    "search": item_name,
                    "limit": 1,
                    "format": "json"
                }
                search_resp = await client.get(base_url, params=search_params)
                search_data = search_resp.json()

                if not search_data[1]:
                    yield event.plain_result(f"❌ 哎呀，没找到 '{item_name}'。是不是名字打错了？")
                    return

                real_title = search_data[1][0]
                page_url = search_data[3][0]

                # 第二步：获取页面简介
                query_params = {
                    "action": "query",
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "titles": real_title,
                    "format": "json"
                }
                query_resp = await client.get(base_url, params=query_params)
                pages = query_resp.json()["query"]["pages"]
                page_id = list(pages.keys())[0]
                extract = pages[page_id].get("extract", "暂无简介")

                # 只截取前 150 个字，避免刷屏
                summary = extract[:150] + "..." if len(extract) > 150 else extract
                
                # 最后返回结果
                result_msg = (
                    f"📖 【{real_title}】\n"
                    f"------------------\n"
                    f"{summary}\n\n"
                    f"🔗 详情传送门: {page_url}"
                )
                yield event.plain_result(result_msg)

        except Exception as e:
            yield event.plain_result(f"⚠️ 访问 Wiki 时出错了: {str(e)}")
