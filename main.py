import requests
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚助手", "1.2.1")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def get_wiki_content(self, keyword: str):
        """去 Wiki.gg 抓取文字内容"""
        url = "https://terraria.wiki.gg/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": keyword,
            "format": "json"
        }
        try:
            r = requests.get(url, params=search_params).json()
            results = r.get("query", {}).get("search", [])
            if not results: return None
            
            title = results[0]['title']
            content_params = {
                "action": "query",
                "prop": "extracts",
                "exintro": True, 
                "explaintext": True,
                "titles": title,
                "format": "json"
            }
            c_r = requests.get(url, params=content_params).json()
            pages = c_r.get("query", {}).get("pages", {})
            return next(iter(pages.values())).get("extract", "")
        except:
            return None

    @filter.command("tr")
    async def tr_command(self, event: AstrMessageEvent):
        '''提问关于泰拉瑞亚的问题。用法：/tr 永夜刃怎么合成？'''
        query = event.message_str.replace("/tr", "").strip()
        if not query:
            yield event.plain_result("你想问什么？例如：/tr 怎么打克苏鲁之眼？")
            return

        # 1. 尝试从 Wiki 获取信息
        wiki_text = await self.get_wiki_content(query)
        
        # 2. 准备 Prompt
        if wiki_text:
            user_prompt = f"泰拉瑞亚 Wiki 关于‘{query}’的资料如下：\n\n{wiki_text[:1000]}\n\n请根据以上资料回答用户的问题：{query}"
            system_msg = "你是一个泰拉瑞亚专家。请结合提供的 Wiki 资料回答用户，语气要友好。"
        else:
            user_prompt = query
            system_msg = "你是一个泰拉瑞亚专家。我没在 Wiki 搜到相关内容，请直接根据你的知识库回答用户。"

        # 3. 获取 AI 提供商并聊天 (修复点在此)
        try:
            provider_id = await self.context.get_current_chat_provider_id(event.unified_msg_origin)
            # 修复：直接从 context 获取 provider
            provider = await self.context.get_llm_provider(provider_id)
            
            resp = await provider.text_chat(
                prompt=user_prompt,
                system_prompt=system_msg
            )
            yield event.plain_result(resp.completion_text)
        except Exception as e:
            yield event.plain_result(f"查询失败，原因：{str(e)}")
