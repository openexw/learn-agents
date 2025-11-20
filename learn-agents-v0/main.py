import asyncio
import pandas as pd
from reflection_agent.img_identify import ImageIdentifyAgent

def read_image_urls_from_csv(csv_file_path: str) -> list:
    """
    从CSV文件中读取图片URL列表
    
    Args:
        csv_file_path (str): CSV文件路径
        
    Returns:
        list: 图片URL列表
    """
    df = pd.read_csv(csv_file_path)
    return df['img_url'].tolist()

def main():
    print("图片识别示例")
    
    # # 示例1: 单张图片识别
    # print("\n1. 单张图片识别:")
    # img_url = "https://mass.alipay.com/medaicore/afts/img/XhBsT5fvZ7kAAAAAgCAAAAgAomLnAABr/1024w_1024h_1l_60q_1fsa?t=BsUGYyt40GZ1p85bCbUUULIUTdQoL612wuGdHIxvhJ4DAAAAZAAA52Jpivbk"
    # result = asyncio.run(ImageIdentifyAgent.run(img_url))
    # print(f"识别结果: {result['generate_ret']}")
    #
    # # 示例2: 批量处理图片
    # print("\n2. 批量处理图片:")
    # image_urls = [
    #     "https://mass.alipay.com/medaicore/afts/img/XhBsT5fvZ7kAAAAAgCAAAAgAomLnAABr/1024w_1024h_1l_60q_1fsa?t=BsUGYyt40GZ1p85bCbUUULIUTdQoL612wuGdHIxvhJ4DAAAAZAAA52Jpivbk",
    #     "https://mass.alipay.com/medaicore/afts/img/MEi3SZ7F5e0AAAAAgCAAAAgAomLnAABr/1024w_1024h_1l_60q_1fsa?t=FpXUqghxDPldbBaX6lpkJR-kuYwOZkN2vCLJscEsWUEDAAAAZAAA52Jpivbl",
    #     "https://mass.alipay.com/medaicore/afts/img/rUjEQoxIVdsAAAAAgCAAAAgAomLnAABr/1024w_1024h_1l_60q_1fsa?t=J3FpHgrRMLj2BZd8Dak_lxwloL7tYxqp_Utjga5YoTQDAAAAZAAA52Jpivbm"
    # ]
    #
    # # 批量处理图片，控制并发数为2
    # results = asyncio.run(ImageIdentifyAgent.batch_run(image_urls, max_concurrent=2))
    #
    # # 打印结果
    # print("\n批量处理结果:")
    # for result in results:
    #     if result["status"] == "success":
    #         print(f"✓ 图片 {result['image_url']} 识别成功: {result['result']}, 生成次数: {result['generate_count']}")
    #     else:
    #         print(f"✗ 图片 {result['image_url']} 处理失败: {result['error']}, 生成次数: {result['generate_count']}")

    # 示例3: 从CSV文件读取图片URL并批量处理
    print("\n3. 从CSV文件读取图片URL并批量处理:")
    csv_file_path = "/Users/boohee/Workspace/llms/learn-agents/learn-agents-v0/dataset/支付宝-1118badcase.csv"

    # 读取图片URL
    image_urls = read_image_urls_from_csv(csv_file_path)

    # 只处理前3张图片作为示例
    sample_image_urls = image_urls

    # 批量处理图片，控制并发数为3
    results = asyncio.run(ImageIdentifyAgent.batch_run(sample_image_urls, max_concurrent=5, max_count=10))

    # 打印结果
    print("\n从CSV文件读取的图片处理结果:")
    for result in results:
        if result["status"] == "success":
            print(f"✓ 图片 {result['image_url']} 生成次数: {result['generate_count']} 识别成功: {result['result']}")
        else:
            print(f"✗ 图片 {result['image_url']} 生成次数: {result['generate_count']},处理失败: {result['error']}")

if __name__ == "__main__":
    main()