from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import httpx
from bs4 import BeautifulSoup # 导入洗数据工具

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚纯文本百科", "1.1.0")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("tr")
    async def search_wiki(self, event: AstrMessageEvent, item_name: str):
        '''直接输出泰拉瑞亚物品文本'''
        
        yield event.plain_result(f"📡 正在接入泰拉瑞亚资料库，请稍候...")

        # 使用中文 Wiki 接口
        base_url = "https://terraria.wiki.gg/zh/api.php"
        
        async with httpx.AsyncClient() as client:
            try:
                # 1. 搜索标题
                search_params = {"action": "opensearch", "search": item_name, "limit": 1, "format": "json"}
                search_resp = await client.get(base_url, params=search_params)
                search_data = search_resp.json()

                if not search_data[1]:
                    yield event.plain_result(f"❌ 找不到物品 '{item_name}'，请检查名称是否正确。")
                    return

                real_title = search_data[1][0]

                # 2. 获取页面的 HTML 内容（这样抓取的数据最全）
                query_params = {
                    "action": "parse",
                    "page": real_title,
                    "prop": "text",
                    "format": "json",
                    "redirects": True
                }
                query_resp = await client.get(base_url, params=query_params)
                html_content = query_resp.json()["parse"]["text"]["*"]

                # 3. 使用 BeautifulSoup 清理 HTML，提取纯文本
                soup = BeautifulSoup(html_content, "html.parser")
                
                # 提取所有的段落 <p>
                paragraphs = soup.find_all("p")
                
                # 过滤掉空的段落，取前 3 段最核心的内容
                clean_text = ""
                count = 0
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 10: # 过滤掉太短的无意义字符
                        clean_text += text + "\n\n"
                        count += 1
                    if count >= 3: # 只要前三段，防止太长刷屏
                        break

                if not clean_text:
                    clean_text = "该页面暂时没有可读的文本描述。"

                # 4. 最终组合输出
                final_report = (
                    f"⚔️ 【泰拉瑞亚百科：{real_title}】\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{clean_text.strip()}"
                )
                
                yield event.plain_result(final_report)

            except Exception as e:
                yield event.plain_result(f"⚠️ 查询出错：{str(e)}")
