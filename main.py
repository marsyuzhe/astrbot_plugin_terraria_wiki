import requests
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.core.agent.tool import FunctionTool, ToolExecResult, Tools  # 1. 这里增加了 Tools 的导入
from pydantic import Field
from pydantic.dataclasses import dataclass

# 定义搜索 Wiki 的“工具”
@dataclass
class TerrariaSearchTool(FunctionTool):
    name: str = "search_terraria_wiki"
    description: str = "当用户询问有关泰拉瑞亚物品、合成、BOSS、攻略时调用此工具。"
    parameters: dict = Field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "要查询的关键词"}
        },
        "required": ["keyword"]
    })

    async def call(self, context, keyword: str) -> ToolExecResult:
        url = "https://terraria.wiki.gg/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": keyword,
            "format": "json"
        }
        try:
            r = requests.get(url, params=params).json()
            search_results = r.get("query", {}).get("search", [])
            if not search_results:
                return "未找到相关 Wiki 内容。"
            
            title = search_results[0]['title']
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
            text = next(iter(pages.values())).get("extract", "无正文内容")
            
            return f"Wiki 条目【{title}】的内容：{text[:800]}..." 
        except Exception as e:
            return f"搜索出错：{str(e)}"

# 注册插件
@register("terraria_wiki", "marsyuzhe", "泰拉瑞亚助手", "1.0.1") # 版本号顺便升一下
class TerrariaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("tr")
    async def tr_command(self, event: AstrMessageEvent):
        '''提问关于泰拉瑞亚的问题。用法：/tr 永夜刃怎么合成？'''
        query = event.message_str.replace("/tr", "").strip()
        if not query:
            yield event.plain_result("你想问什么？例如：/tr 怎么打克苏鲁之眼？")
            return

        provider_id = await self.context.get_current_chat_provider_id(event.unified_msg_origin)

        # 2. 这里是关键：将列表用 Tools() 包起来
        resp = await self.context.tool_loop_agent(
            event=event,
            chat_provider_id=provider_id,
            prompt=query,
            system_prompt="你是一个泰拉瑞亚专家。请利用搜索工具获取 Wiki 信息，然后用亲切的语气回答用户。",
            tools=Tools([TerrariaSearchTool()]) # 修改了这里
        )
        
        yield event.plain_result(resp.completion_text)
