import requests
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚助手", "1.2.4")
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
        
        # 2. 构造消息
        if wiki_text:
            wiki_context = f"【泰拉瑞亚 Wiki 资料】\n{wiki_text[:800]}..."
        else:
            wiki_context = "（未在 Wiki 中搜到相关资料）"

        # 3. 绕过 provider_manager，直接使用框架最稳妥的调用链
        # 我们直接构造一个 System Prompt 和 User Prompt 发回给 LLM
        try:
            # 这里的改进：使用 AstrBot 的统一回复接口，不直接操作底层 provider
            # 这种方式会直接把消息推回给当前会话配置的 AI
            prompt = f"{wiki_context}\n\n用户问题：{query}\n请作为泰拉瑞亚专家回答。"
            
            # 使用 self.context.get_llm_provider_id 的变体或直接让 Agent 处理
            # 如果之前的方式都失败了，这里改用最保守的：直接返回文字，并告诉用户 Wiki 查到了什么
            # 这是一个“保底策略”，即使 AI 调用失败，用户也能看到 Wiki 信息
            
            yield event.plain_result(f"🔍 Wiki 搜索结果：\n{wiki_context}\n\n(正在请求 AI 总结...)")

            # 尝试调用统一的智能体接口
            provider_id = await self.context.get_current_chat_provider_id(event.unified_msg_origin)
            
            # 使用 try-except 包裹 AI 总结部分
            try:
                # 注意：有些版本可能叫 provider_manager.providers.get()
                # 我们直接尝试最常用的调用方式
                resp = await self.context.tool_loop_agent(
                    event=event,
                    chat_provider_id=provider_id,
                    prompt=prompt,
                    system_prompt="你是一个泰拉瑞亚助手。",
                    tools=None # 不传工具，只让它总结文字
                )
                yield event.plain_result(resp.completion_text)
            except Exception as e:
                yield event.plain_result(f"AI 总结失败，请直接参考上面的 Wiki 原文。原因: {str(e)}")

        except Exception as e:
            yield event.plain_result(f"发生未知错误: {str(e)}")
