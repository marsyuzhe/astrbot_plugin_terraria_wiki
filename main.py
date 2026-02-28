from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import httpx
from bs4 import BeautifulSoup

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚百科+合成表", "1.2.0")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("tr")
    async def search_wiki(self, event: AstrMessageEvent, item_name: str):
        yield event.plain_result(f"⚒️ 正在工匠作坊为你查询 '{item_name}'...")

        base_url = "https://terraria.wiki.gg/zh/api.php"
        
        async with httpx.AsyncClient() as client:
            try:
                # 1. 搜索标题并处理重定向
                search_params = {"action": "opensearch", "search": item_name, "limit": 1, "format": "json"}
                search_resp = await client.get(base_url, params=search_params)
                if not search_resp.json()[1]:
                    yield event.plain_result(f"❌ 未找到物品 '{item_name}'。")
                    return
                real_title = search_resp.json()[1][0]

                # 2. 获取 HTML
                query_params = {"action": "parse", "page": real_title, "prop": "text", "format": "json", "redirects": True}
                query_resp = await client.get(base_url, params=query_params)
                html_content = query_resp.json()["parse"]["text"]["*"]
                soup = BeautifulSoup(html_content, "html.parser")

                # --- 提取简介 ---
                paragraphs = soup.find_all("p")
                intro_text = ""
                for p in paragraphs:
                    txt = p.get_text().strip()
                    if len(txt) > 15: # 简单过滤杂讯
                        intro_text = txt[:150] + "..."
                        break

                # --- 核心：提取合成表 (Crafting) ---
                recipes = []
                # 查找 Wiki 中专门存放合成表的表格
                recipe_table = soup.find("table", class_="crafts") 
                
                if recipe_table:
                    # 遍历表格行（跳过表头）
                    rows = recipe_table.find_all("tr")[1:]
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            # 第一列通常是材料，第二列是制作站
                            ingredients = cols[0].get_text(separator=" + ").strip()
                            station = cols[1].get_text().strip() if len(cols) > 1 else "未知制作站"
                            recipes.append(f"📦 材料: {ingredients}\n🛠️ 制作站: {station}")
                
                # --- 组合最终消息 ---
                msg = f"⚔️ 【{real_title}】\n\n📖 简介：\n{intro_text}\n"
                msg += "\n━━━━━━━━━━━━━━━\n"
                
                if recipes:
                    msg += "🛠️ 合成方案：\n" + "\n---\n".join(recipes[:3]) # 最多显示3个方案防止刷屏
                else:
                    msg += "💡 此物品可能无法通过合成获得，或者是基础材料。"

                yield event.plain_result(msg)

            except Exception as e:
                yield event.plain_result(f"⚠️ 查询出错啦: {str(e)}")
