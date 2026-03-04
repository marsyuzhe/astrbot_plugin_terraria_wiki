import requests
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚助手", "1.2.3")
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def get_wiki_content(self, keyword: str):
        url = "https://terraria.wiki.gg/api.php"
        search_params = {"action": "query", "list": "search", "srsearch": keyword, "format": "json"}
        try:
            r = requests.get(url, params=search_params).json()
            results = r.get("query", {}).get("search", [])
            if not results: return None
            title = results[0]['title']
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

        # 1. 获取 Wiki 信息
        wiki_text = await self.get_wiki_content(query)
        
        # 2. 准备内容
        if wiki_text:
            user_prompt = f"Wiki 资料：\n{wiki_text[:1000]}\n\n问题：{query}"
            system_msg = "你是一个泰拉瑞亚专家，请参考 Wiki 资料回答。"
        else:
            user_prompt = query
            system_msg = "你是一个泰拉瑞亚专家。"

        # 3. 终极调用方式：通过 provider_manager 获取
        try:
            # 先拿到当前会话使用的 Provider ID
            curr_provider_id = await self.context.get_current_chat_provider_id(event.unified_msg_origin)
            
            # 从 provider_manager 中获取实例
            # 这是目前最底层的获取方式，绕过了 event 和 context 的直接属性
            provider = self.context.provider_manager.get_provider(curr_provider_id)
            
            if not provider:
                yield event.plain_result("错误：找不到 AI 提供商，请检查模型配置。")
                return

            resp = await provider.text_chat(
                prompt=user_prompt,
                system_prompt=system_msg
            )
            yield event.plain_result(resp.completion_text)
            
        except Exception as e:
            yield event.plain_result(f"抱歉，还是报错了: {str(e)}\n请联系开发者检查 provider_manager 调用。")
