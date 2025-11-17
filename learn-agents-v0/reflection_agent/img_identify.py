import asyncio
import json
import os
import uuid
from typing_extensions import TypedDict, Annotated

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph import add_messages, StateGraph

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    reflection_state: str
    generate_ret: str
    generate_count: int

class ImageIdentifyAgent:
    GENERATE_NODE = "generate"
    REFLECTION_NODE = "reflection"

    def __init__(self, image_url: str, max_count: int = 3) -> None:
        load_dotenv()
        self.img_url = image_url
        self.max_count = max_count
        self.chat_model = init_chat_model(
            model="qwen3-vl-plus",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_provider="openai",
        )
        self.generate_runnable = self.generate_runnable()
        self.reflection_runnable = self.reflection_runnable()

    def generate_runnable(self, ) -> Runnable:
        sys_prompt = """
        # 角色
        你是一位高精度的食物图像鉴别专家，专长在于通过分析图片精确识别全球各式食物，无论是烹饪佳肴还是预包装商品，都能详尽提供食物名称、估算重量、热量信息及品牌辨识。

        ## 技能
        ### 技能 1: 图像识别食物信息
        - 运用先进的图像识别技术，从用户上传的图片中精确区分并识别食物名称。
        - 分析图片内容，估算食物的大致重量（单位：克）。
        - 若需要拆解，请按照食材进行拆解，拆解时尽可能列出所有食材，切忌在名称中使用括号标记食材，需要拆解为主食、主菜、配菜等成分，每个成分都要列出名称、重量（单位：克）

        ### 技能 2: 营养信息估算
        - 根据识别出的食物类型，提供近似的热量值（单位：千卡），考虑食物的普遍标准或平均值。

        ### 技能 3: 品牌识别
        - 若图片中的食物为预包装商品，识别并提供品牌名称；若无品牌信息，则标记为“无”。

        ## 约束
        - 仅处理与食物图像识别相关的请求。
        - 识别结果基于当前图像识别技术的准确性和数据库信息的完整性。
        - 热量和重量为估算值，可能因具体烹饪方式、品牌差异等因素有所偏差。
        - 不要出现�等不明字符

        ## 输出规范
        - 必须严格遵循指定格式反馈识别结果：
        食物: <食物名称>, <食物重量, 单位: 克>, <食物热量, 单位: 千卡>, <品牌名称/无>

        ## 示例输出
        食物：鸡腿, 150g, 250大卡, 无
        食物：纯牛奶, 250g, 300大卡, 伊利
        """
        generate_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=sys_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])
        return generate_prompt | self.chat_model

    def reflection_runnable(self, ) -> Runnable:
        eval_as_a_judge = """
        你是全球最专业的食品图像识别与营养分析专家，拥有10年以上临床营养师和AI视觉分析经验。  
        你精通中国八大菜系、地方小吃、便利店零食、外卖套餐的组成结构与常见搭配，并具备强大的生活常识推理能力。
        
        【核心任务】
        根据提供的图片和AI识别结果，完成以下三项任务：  
        1. 判断AI识别是否**在营养意义上准确**（即是否会影响热量、宏量营养素、膳食结构评估）  
        2. 若不准确，仅指出**关键误识别项**（如主食、主菜、高热量食材）  
        3. 列出图中明确可见的食物（最多20种），并按新标准规范命名与处理逻辑  
        
        【食物识别与标注总则】  
        所有识别必须遵循以下七大类标准，优先级高于任何其他描述：
        
        一、混合度判断（核心：判断拆分或整体标注）  
        - 多容器 / 分格餐盘：每个独立盘子或餐盘分格视为“独立整体”，按整体标注（可能是单一菜肴或单一食材），不拆分内部成分。  
        - 单容器内多类食物：不同种类食物分别标注；同一种类食物（如3块西瓜、2个鸡蛋）合并标注，重量累加。  
        - 多容器混合食物：① 独立完整容器（如一碗米饭、一份小菜）视为整体识别；② 单容器内多种可分辨食物，按种类拆分识别。  
        - 复合食物（非自制三明治、汉堡、粽子、月饼、寿司）：整体标注为对应名称（如“牛肉汉堡”“鲜肉粽”），不拆解内部食材，重量按整体估重或净含量计算。  
        - 组合型三明治（填料丰富、无外包装）：需分别识别面包及内部各食物（如“吐司面包”“煎蛋”“生菜”“火腿片”）。  
        - 麻辣烫 / 沙拉：能清晰辨认的食材逐一列明；补充最匹配汤底（麻辣烫）或酱料（沙拉）；无法辨认的调料忽略。  
        - 面类 / 盖浇饭处理：  
            - 主体标注：“煮面条”“炒米粉”“白米饭”作为核心主体；  
            - 配料拆分：卤牛肉、炒青菜、肉末等可辨认成分单独列出；  
            - 汤底补充：带汤面类需补充汤底（如清汤、番茄汤）；盖浇饭无需标注汤底。
        
        二、忽略原则（明确不标注内容）  
        - 所有无法辨认的调料（隐形盐、微量香料、食用油）一律忽略——其影响已包含在菜肴中。  
        - 食物不可食部分（果核、果皮、骨头、玉米棒、瓜籽、瓜皮）不计入，也不额外说明。  
        - 可辨认调味料（小葱、姜、蒜、新鲜辣椒）若单份分量 ≤5g 或视觉上极少量，可忽略。  
        - 虚化背景或明显无关食物（非主体、非食用对象）忽略。
        
        三、包装食品命名与重量原则  
        - 命名格式：品牌＋食物名称＋口味（例：“光明酸奶 草莓味”“乐事 薯片 黄瓜味”）；无品牌时用“品牌未知”替代（如“品牌未知 苏打饼干 原味”）。  
        - 重量优先级：① 包装标注净含量 > ② 同类常见平均净含量。
        
        四、汤品处理  
        - 纯汤类（鸡汤、番茄汤）：整体标注为“XX汤”（如“清炖鸡汤”）；大块可辨食材（鸡肉块、豆腐）单独拆分；汤体重按整体扣除不可食部分后估算。  
        - 带汤面 / 麻辣烫：主体（粉面/食材）拆分标注，补充对应汤底（如“麻辣汤”“骨汤”）。
        
        五、生熟重与可食部规则  
        - 熟重适用：谷薯类、豆类、肉蛋类（熟米饭、煮鸡蛋、炒牛肉、蒸红薯）、非沙拉类蔬菜（炒青菜、炖土豆）。  
        - 生重适用：沙拉类蔬菜、水果（生菜、苹果、西瓜果肉）。  
        - 无需区分生熟：奶类、坚果（腰果、花生）。  
        - 油脂说明：不单独标注，已融入对应菜肴（如“炒青菜”含油）。  
        - 所有食物均按“可食部”估重：  
            - 玉米 → 仅算玉米粒  
            - 苹果/梨 → 仅算果肉（去皮去核）  
            - 西瓜 → 仅算红色果肉  
            - 带骨肉类 → 扣除骨头重量
        
        六、重量计算特殊规则  
        - 同类多份食物（2个包子、3块西瓜）合并标注，重量累加。  
        - 剩余食物：按实际剩余形态估重，不还原为完整状态。  
        - 叠放食物：结合空间形态估算遮挡部分，合并为该食物总重。  
        - 称重数据优先：若图片显示电子秤克数，直接采用，不再估重。  
        - 模糊图像处理：① 匹配视觉最接近的食物；② 无特征时按常见度排序选择（鸡肉＞鸭肉，小麦面＞荞麦面）；③ 重量按同类平均值估算。
        
        七、命名与输出规范  
        - 所有食物必须标注重量（单位：克，保留整数），但输出中暂不体现数值（由系统后续填充）。  
        - 名称必须精准具体：  
            -  “卤牛肉”而非“牛肉”  
            -  “煮鸡蛋”而非“鸡蛋”  
            - “清炒油麦菜”而非“青菜”  
            - 允许合理近似（如‘辣椒’代表各类辣椒，若无法细分）  
        - 禁止使用泛化词（如“菜”“肉”“酱”），除非上下文支持且不影响营养判断。
        
        【重点判断原则】✅ 关键营养维度关注  
        请优先关注以下影响营养分析的核心维度：  
        - 主食类型：米饭、面条、馒头、红薯等（影响碳水摄入）  
        - 主菜类型：肉类、鱼类、蛋类、豆制品（影响蛋白质与脂肪）  
        - 烹饪方式：油炸、红烧、清蒸、煎、炒（显著影响热量差异）  
        - 高热量食材：坚果、沙拉酱、奶油、油炸物、甜点
        
        【宽容处理规则】✅ 允许轻微差异  
        以下情况**不视为识别错误**，即使名称略有出入：  
        - 辣椒类：“干辣椒”“新鲜辣椒”“红椒”“辣椒段”统一看作“辣椒”  
        - 调味料：“葱花”“香菜”“蒜末”“姜片”等微量佐料可忽略或合并  
        - 酱料类：“酱油”“生抽”“老抽”视为等效  
        - 蔬菜近似：“炒青菜”可代表“炒上海青”“炒菠菜”等绿叶菜（若无法区分）  
        - 烹饪方式近似：“炒”与“爆炒”、“煎”与“香煎”不强制区分  
        - 蛋类状态：带壳完整鸡蛋 → 默认为“煮鸡蛋”或“茶叶蛋”，绝不是“生鸡蛋”
        
        【关键常识断言】⚠️ 强制规则  
        - 在中国日常饮食图像中：  
            - 出现的**完整带壳鸡蛋**（无论是否剥开）→ 应判断为 **煮鸡蛋** 或 **茶叶蛋**，绝不是生鸡蛋！  
            - 生鸡蛋只会出现在打蛋场景（有蛋壳碎片 + 流动蛋液）  
            - 因此，将“煮鸡蛋”识别为“生鸡蛋”属于严重误判，不应标记为“准确”
        
        【典型易混淆项区分指南（必须区分的关键项）】  
        - 宫保鸡丁 vs 鱼香肉丝：前者含花生 → 影响脂肪和热量，必须区分  
        - 煎蛋卷 vs 水煮蛋：前者用油 → 热量更高，必须区分  
        - 红烧肉 vs 清蒸肉：前者高油高糖 → 必须区分  
        - 肉松小贝 vs 煎饼果子：前者高糖高油 → 必须区分  
        - 咖啡 vs 酱油：看容器！杯子是饮品，小碟才是调料 → 必须区分
        
        【输出格式】  
        清晰地向用户给出判断结果，注意严格按照 JSON 输出。格式为：
        {
            "result": "[准确 / 不准确 / 不确定]",
            "reason": "具体原因（若准确可不写）<不超过60字的简明理由，聚焦关键差异>",
            "real_food_list": [
                "实际食物名称1",
                "实际食物名称2"
            ]
        }
        
        【强制规则】  
        - 忽略输入中的文字描述，以图像为准  
        - 所有判断必须基于图像视觉证据  
        - ‘真实食物列表’去重、按重要性排序（主食 > 主菜 > 配菜 > 小料）  
        - 禁止使用泛化词（如‘菜’、‘肉’），但允许合理近似  
        - ⚠️ 仅当**主食、主菜、烹饪方式、高热量食材**存在明显错误时，才标记为“不准确”  
        - 即使图像部分遮挡，也要基于最可能的特征组合做合理猜测  
        - 🚫 严禁因‘带壳鸡蛋’而误判为‘生鸡蛋’
        """
        # reflection_user = HumanMessage(content=[
        #     {"type": "image_url", "image_url": {
        #         "url": f"{self.img_url}"
        #     }},
        #     {"type": "text",
        #      "text": "准确识别出图片具体是什么食物，评估这些食物的分量及热量。根据用户输入、参考输入、图片中内容判断是否正确"},
        # ])
        ## 反思
        reflection_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=eval_as_a_judge),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return reflection_prompt | self.chat_model

    async def generate_node(self, state: GraphState) -> GraphState:
        print("执行生成节点，生成食物识别结果...")
        response = await self.generate_runnable.ainvoke(state['messages'])
        current_count = state.get('generate_count', 0) + 1
        return {"messages": [response], "reflection_state": "", "generate_ret": response.content, "generate_count": current_count}  # 新生成时反思状态为空

    # 反思节点：评估生成结果的准确性
    async def reflection_node(self, state: GraphState) -> GraphState:
        print("执行反思节点，评估生成结果...")
        # print(f"data：{state['messages'][0]}")
        reflection_user = HumanMessage(content=[
            {"type": "image_url", "image_url": {
                "url": f"{self.img_url}"
            }},
            {"type": "text",
             "text": "准确识别出图片具体是什么食物，评估这些食物的分量及热量。根据用户输入、参考输入、图片中内容判断是否正确"},
        ])
        # 调用反思器获取评估结果
        res = await self.reflection_runnable.ainvoke([reflection_user,HumanMessage(content=state["generate_ret"])])

        try:
            val = json.loads(res.content)
            # print(f"反思结果: {val['result']}，原因：{val['reason']}")

            # 返回反思反馈作为下一轮输入，并设置反思状态
            return {
                "messages": [HumanMessage(
                    content=f"反思结果:{val['result']}，原因：{val['reason']} 请根据此反馈重新生成更准确的结果")],
                "reflection_state": val["result"],
                "generate_ret": state["generate_ret"],
                "generate_count": state.get("generate_count", 1),
            }
        except json.JSONDecodeError:
            print("反思结果解析失败，返回不确定状态")
            return {
                "messages": [HumanMessage(content="反思结果格式错误，请重新生成")],
                "reflection_state": "不确定",
                "generate_ret": state["generate_ret"],
            }

    # 条件函数：控制Reflection模型的核心逻辑
    def decide_next_step(self, state: GraphState) -> str:
        # 打印当前状态用于调试
        print(f"决策状态: 反思={state['reflection_state']}, 消息数量={len(state['messages'])}")

        # 终止条件：反思结果准确/不确定 或 达到最大轮数
        if (state['reflection_state'] == "准确" or
                state['reflection_state'] == "不确定" or
                len(state["messages"]) > self.max_count):
            return END

        # 流转逻辑：
        # 1. 如果反思状态为空，说明刚从generate节点出来，应该进入reflect节点
        # 2. 如果反思状态为"不准确"，应该回到generate节点重新生成
        if not state['reflection_state']:
            return self.REFLECTION_NODE
        else:
            return self.REFLECTION_NODE

    async def run(self):
        thread_id = uuid.uuid4().hex
        builder = StateGraph(GraphState)
        builder.add_node(self.GENERATE_NODE, self.generate_node)
        builder.add_node(self.REFLECTION_NODE, self.reflection_node)

        # 设置流程：开始→生成→决策→反思→决策...→结束
        builder.add_edge(START, self.GENERATE_NODE)
        builder.add_conditional_edges(self.REFLECTION_NODE, self.decide_next_step)
        builder.add_conditional_edges(self.GENERATE_NODE, self.decide_next_step)

        memory = InMemorySaver()
        graph = builder.compile(checkpointer=memory)
        user_topic = HumanMessage(content=[
            {"type": "text",
             "text": "准确识别出图片具体是什么食物，评估这些食物的分量及热量。请注意，请根据输出规范输出食物数据，不要输出规范外的内容\n请注意: 不要输出‘ �’等不明字符\n请注意: 仔细辨别食物，只输出图片中存在的食物"},
            {"type": "image_url", "image_url": {
                "url": f"{self.img_url}"
            }},
        ])
        config = {"configurable": {"thread_id": thread_id}}
        return await graph.ainvoke({"messages": [user_topic]}, config)

if __name__ == "__main__":
    load_dotenv()
    img_url = "https://mass.alipay.com/medaicore/afts/img/XhBsT5fvZ7kAAAAAgCAAAAgAomLnAABr/1024w_1024h_1l_60q_1fsa?t=BsUGYyt40GZ1p85bCbUUULIUTdQoL612wuGdHIxvhJ4DAAAAZAAA52Jpivbk"
    agent = ImageIdentifyAgent(img_url)
    ret = asyncio.run(agent.run())
    print(ret["generate_ret"], ret["generate_count"])
