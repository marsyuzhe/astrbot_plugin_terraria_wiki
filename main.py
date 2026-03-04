import requests
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚助手", "1.2.0")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def get_wiki_content(self, keyword: str):
        """这是一个简单的函数，用来去 Wiki 抓取文字内容"""
        url = "https://terraria.wiki.gg/api.php"
        # 先搜标题
        search_params = {"action": "query", "list": "search", "srsearch": keyword, "format": "json"}
        try:
            r = requests.get(url, params=search_params).json()
            results = r.get("query", {}).get("search", [])
            if not results: return None
            
            title = results[0]['title']
            # 再拿正文
            content_params = {
                "action": "query", "prop": "extracts", "exintro": True, 
                "explaintext": True, "titles": title, "format": "json"
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
        
        # 2. 准备发给 AI 的内容
        if wiki_text:
            user_prompt = f"我从 Wiki 找到了以下关于‘{query}’的信息：\n\n{wiki_text[:1000]}\n\n请根据这些信息回答用户的问题：{query}"
            system_msg = "你是一个泰拉瑞亚专家，请结合我提供的 Wiki 信息，用亲切专业的语气回答用户。如果 Wiki 里没提到具体数值，就按你的知识库回答。"
        else:
            user_prompt = f"用户问了：{query}。我没在 Wiki 上搜到结果，请直接根据你的知识库回答他。"
            system_msg = "你是一个泰拉瑞亚专家。"

        # 3. 调用 AI 
        # 获取当前模型
        provider_id = await self.context.get_current_chat_provider_id(event.unified_msg_origin)
        provider = await self.context.main_config.get_llm_provider(provider_id)
        
        try:
            # 使用最基础的 text_chat，不带任何 Tool 逻辑，兼容性最高
            resp = await provider.text_chat(
                prompt=user_prompt,
                system_prompt=system_msg
            )
            yield event.plain_result(resp.completion_text)
        except Exception as e:
            yield event.plain_result(f"糟糕，AI 罢工了：{str(e)}")
