from dotenv import load_dotenv
import os
from typing import Annotated,TypedDict
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
import json
import asyncio
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage,SystemMessage
from  langchain_community.chat_models import ChatOpenAI

load_dotenv()

sys_prompt1 = """
# 角色
你是一位高精度的食物图像鉴别专家，专长在于通过分析图片精确识别全球各式食物，无论是烹饪佳肴还是预包装商品，都能详尽提供食材名称、估算重量、热量信息及品牌辨识。

## 技能
### 技能 1: 图像识别食材信息
- 运用先进的图像识别技术，从用户上传的图片中精确区分并识别食材名称。
- 分析图片内容，估算食物的大致重量（单位：克）。
- 对混合度较高的菜肴，请按照食材进行拆解，类似麻辣烫、拌饭、盖浇饭等高度混合的菜肴，拆解时尽可能列出所有食材
- 若菜肴名称与常识不符，请按照食材进行拆解，拆解时尽可能列出所有食材
- 若烹饪方式明确，请对烹饪方式进行说明，但不要杜撰
- 列出图中明确可见的食物（最多20种），要求如下：
  - 如果是**成型菜品**（如宫保鸡丁、肉松小贝），直接输出菜名，不拆解
  - 如果是**散装组合餐**，拆解为主食、主菜、配菜等成分，每个成分都要列出名称、重量（单位：克）
  - 名称尽量具体，但允许合理近似（如‘辣椒’可接受，不必细分干/鲜）
  - 注意常见搭配（如黄焖鸡配米饭）

### 技能 2: 营养信息估算
- 根据识别出的食物类型，提供近似的热量值（单位：千卡），考虑食物的普遍标准或平均值。

### 技能 3: 品牌识别
- 若图片中的食物为预包装商品，识别并提供品牌名称；若无品牌信息，则标记为“无”。
- 若从图中没有明确标识品牌名称或者识别呢绒不清楚，请不要杜撰

### 技能4：输出前反思结果是否正确
- 食物名称是否是真的食物或菜肴
- 食物重量是否合理
- 反思每一个结果是否合理

## 约束
- 仅处理与食物图像识别相关的请求。
- 识别结果基于当前图像识别技术的准确性和数据库信息的完整性。
- 热量和重量为估算值，可能因具体烹饪方式、品牌差异等因素有所偏差。
- 不要出现�等不明字符
- 若为外卖订单，请不要将平台信息当做品牌，如饿了么、每天、京东秒杀等

## 输出规范
- 必须严格遵循指定格式反馈识别结果：
食物: <食物名称>, <食物重量, 单位: 克>, <食物热量, 单位: 千卡>, <品牌名称/无>

## 示例输出
食物：鸡腿, 150g, 250大卡, 无
食物：纯牛奶, 250g, 300大卡, 伊利
"""
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

eval_as_a_judge = """
你是全球最专业的食品图像识别与营养分析专家，拥有10年以上临床营养师和AI视觉分析经验。
你精通中国八大菜系、地方小吃、便利店零食、外卖套餐的组成结构与常见搭配，并具备强大的生活常识推理能力。

【核心任务】
根据提供的图片和AI识别结果，完成以下三项任务：
1. 判断AI识别是否**在营养意义上准确**（即是否会影响热量、宏量营养素、膳食结构评估）
2. 若不准确，仅指出**关键误识别项**（如主食、主菜、高热量食材）
3. 列出图中明确可见的食物（最多20种），要求如下：
- 如果是**成型菜品**（如宫保鸡丁、肉松小贝），直接输出菜名，不拆解
- 如果是**散装组合餐**，拆解为主食、主菜、配菜等成分
- 名称尽量具体，但允许合理近似（如‘辣椒’可接受，不必细分干/鲜）
- 注意常见搭配（如黄焖鸡配米饭）

【重点判断原则】✅ 新增
请优先关注以下**影响营养分析的关键维度**：
- 主食类型：米饭、面条、馒头、红薯等（影响碳水摄入）
- 主菜类型：肉类、鱼类、蛋类、豆制品（影响蛋白质与脂肪）
- 烹饪方式：油炸、红烧、清蒸、煎、炒（影响热量差异）
- 高热量食材：坚果、沙拉酱、油炸物、甜点

【宽容处理规则】✅ 新增
以下情况**不视为识别错误**，即使名称略有差异：
- 辣椒类：‘干辣椒’、‘新鲜辣椒’、‘辣椒段’、‘红椒’等统一看作‘辣椒’
- 调味料：‘葱花’、‘香菜’、‘蒜末’、‘姜片’等微量佐料可忽略或合并
- 酱料类：‘酱油’、‘生抽’、‘老抽’视为等效
- 蔬菜近似：‘炒青菜’可代表‘炒上海青’、‘炒菠菜’等绿叶菜（若无法区分）
- 烹饪方式近似：‘炒’与‘爆炒’、‘煎’与‘香煎’不强制区分
- 蛋类状态：带壳的完整鸡蛋 → 默认为‘煮鸡蛋’，不视为‘生鸡蛋’；只有流动蛋液才是生鸡蛋

【关键常识断言】⚠️ 强制规则
在中国日常饮食图像中：
- 出现的**完整带壳鸡蛋**（无论是否剥开）→ 应判断为 **煮鸡蛋** 或 **茶叶蛋**，绝不是生鸡蛋！
- 生鸡蛋只会出现在烹饪前的打蛋场景（有蛋壳碎片 + 流动蛋液）
- 因此，将‘煮鸡蛋’识别为‘生鸡蛋’属于误判，不应标记为‘准确’

【典型易混淆项区分指南（仅限关键项）】
- 宫保鸡丁 vs 鱼香肉丝：前者有花生 → 影响脂肪和热量，必须区分
- 煎蛋卷 vs 水煮蛋：前者用油 → 热量显著更高，必须区分
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
- ‘真实食物列表’去重、按重要性排序
- 禁止使用泛化词（如‘菜’、‘肉’），但允许合理近似
- ⚠️ 仅当**主食、主菜、烹饪方式、高热量食材**存在明显错误时，才标记为‘不准确’
- 即使图像部分遮挡，也要基于最可能的特征组合做合理猜测
- 🚫 严禁因‘带壳鸡蛋’而误判为‘生鸡蛋’
"""

chat_model = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen3-vl-plus",
)

generate_prompt = ChatPromptTemplate.from_messages([
         SystemMessage(content=sys_prompt),
         MessagesPlaceholder(variable_name="messages"),
    ]
)
generate =  generate_prompt|chat_model

# generate_val = generate.invoke({"messages": [user_topic]})
# print(generate_val)

## 反思
reflection_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=eval_as_a_judge),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
img_url = "https://mass.alipay.com/medaicore/afts/img/TRFnRar_PfMAAAAAgFAAAAgAomLnAABr/original?t=pLn5riBele9cFgwvANR3Xey2XWIf4eabWPXh7LmcuvEDAAAAZAAA52JpGYlA"
# generate_human = HumanMessage(content=generate_val.content)
reflection_user = HumanMessage(content=[
            {"type": "image_url", "image_url":{
                "url": f"{img_url}"
            }},
            {"type": "text", "text": "准确识别出图片具体是什么食物，评估这些食物的分量及热量。根据用户输入、参考输入、图片中内容判断是否正确"},
        ])
reflection = reflection_prompt | chat_model
# reflection_resp = reflection.invoke(input={
#     "messages": [generate_human, reflection_user],
#     "img_url": img_url})
# print(reflection_resp.content, type(reflection_resp.content))



# 定义状态
class State(TypedDict):
    messages: Annotated[list, add_messages]
    reflection_state: str

# 定义最大迭代轮数
MAX_ROUND = 5

# 生成节点：根据当前消息生成食物识别结果
async def generate_node(state: State) -> State:
    print("执行生成节点，生成食物识别结果...")
    response = await generate.ainvoke(state['messages'])
    return {"messages": [response], "reflection_state": ""}  # 新生成时反思状态为空

# 反思节点：评估生成结果的准确性
async def reflection_node(state: State) -> State:
    print("执行反思节点，评估生成结果...")
    # 创建消息类型映射，用于角色互换
    cls_map = {"ai": HumanMessage, "human": AIMessage}
    
    # 转换消息类型并添加反思用户提示
    translated = [state['messages'][0]] + [
        cls_map[msg.type](content=msg.content) for msg in state['messages'][1:]
    ] + [reflection_user]
    
    # 调用反思器获取评估结果
    res = await reflection.ainvoke(translated)
    
    try:
        val = json.loads(res.content)
        print(f"反思结果: {val['result']}，原因：{val['reason']}")
        
        # 返回反思反馈作为下一轮输入，并设置反思状态
        return {
            "messages": [HumanMessage(content=f"反思结果:{val['result']}，原因：{val['reason']} 请根据此反馈重新生成更准确的结果")],
            "reflection_state": val["result"]
        }
    except json.JSONDecodeError:
        print("反思结果解析失败，返回不确定状态")
        return {
            "messages": [HumanMessage(content="反思结果格式错误，请重新生成")], 
            "reflection_state": "不确定"
        }

# 条件函数：控制Reflection模型的核心逻辑
def decide_next_step(state: State) -> str:
    # 打印当前状态用于调试
    print(f"决策状态: 反思={state['reflection_state']}, 消息数量={len(state['messages'])}")
    
    # 终止条件：反思结果准确/不确定 或 达到最大轮数
    if (state['reflection_state'] == "准确" or 
        state['reflection_state'] == "不确定" or 
        len(state["messages"]) > MAX_ROUND):
        return END
    
    # 流转逻辑：
    # 1. 如果反思状态为空，说明刚从generate节点出来，应该进入reflect节点
    # 2. 如果反思状态为"不准确"，应该回到generate节点重新生成
    if not state['reflection_state']:
        return "reflect"
    else:
        return "generate"

# 创建状态图
builder = StateGraph(State)
builder.add_node("generate", generate_node)
builder.add_node("reflect", reflection_node)

# 设置流程：开始→生成→决策→反思→决策...→结束
builder.add_edge(START, "generate")
builder.add_conditional_edges("generate", decide_next_step)
builder.add_conditional_edges("reflect", decide_next_step)

memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)

async def main():
    user_topic = HumanMessage(content=[
        {"type": "text",
         "text": "准确识别出图片具体是什么食物，评估这些食物的分量及热量。请注意，请根据输出规范输出食物数据，不要输出规范外的内容\n请注意: 不要输出‘ �’等不明字符\n请注意: 仔细辨别食物，只输出图片中存在的食物"},
        {"type": "image_url", "image_url": {
            "url": f"{img_url}"
        }},
    ])
    config = {"configurable": {"thread_id": "1"}}
    async for event in graph.astream({"messages": [user_topic]}, config):
        print(event)
        print("---")

if __name__ == "__main__":
    asyncio.run(main())