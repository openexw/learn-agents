import re
import time

from bs4 import BeautifulSoup, Comment
from mcp.server.fastmcp import FastMCP
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

mcp = FastMCP()


def get_chrome_instance():
    chromedriver_path = "/Users/sam/llm/chromedriver/chromedriver"

    # chrome_options = Options()
    # chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    service = Service(executable_path=chromedriver_path)

    # driver = webdriver.Chrome(options=chrome_options, service=service)
    driver = webdriver.Chrome(service=service)

    # print(f"成功连接到Chrome浏览器，当前URL：{driver.current_url}")
    return driver


def open_chrome():
    driver = get_chrome_instance()
    driver.get("https://www.baidu.com/")
    print(driver.current_url)

    time.sleep(5)
    driver.execute_script("window.open('https://www.qq.com', '_blank');")
    # 获取所有句柄
    all_handles = driver.window_handles
    print(all_handles)

    time.sleep(5)
    driver.switch_to.window(all_handles[-1])
    print(driver.current_url)
    driver.close()

    # 切换句柄
    driver.switch_to.window(all_handles[0])
    print(driver.current_url)


# @mcp.tool(description="search query word in Baidu")
def search_in_baidu(query: str) -> str:
    driver = webdriver.Chrome()
    try:
        driver.get("https://www.baidu.com")

        text_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "kw"))
        )

        text_box.send_keys(query)

        submit_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "su"))
        )
        submit_button.click()

        WebDriverWait(driver, 5).until(
            EC.title_contains(query[:10])
        )

        # 翻页优化
        page_text_list = []
        for i in range(3):
            if i > 0:
                results = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".page-inner_2jZi2>a"))
                )
                if i == 1:
                    results[i - 1].click()
                else:
                    results[i].click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # 滚动优化
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

                # 检查是否加载完成
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            page_content = driver.find_element(By.TAG_NAME, "body")
            page_text = page_content.text
            page_text_list.append(f"第{i + 1}页\n" + page_text + "\n --- \n")

        driver.quit()

        return '\n'.join(page_text_list)

    except Exception as e:
        print(e)
        return ""


@mcp.tool(description="search query word in Baidu")
def search_in_baidu_with_html(query: str) -> str:
    # driver = webdriver.Chrome()
    driver = get_chrome_instance()
    try:
        driver.get("https://www.baidu.com")

        text_box = WebDriverWait(driver, 5).until(
            # EC.presence_of_element_located((By.ID, "kw"))
            EC.presence_of_element_located((By.ID, "chat-textarea"))
        )

        text_box.send_keys(query)

        submit_button = WebDriverWait(driver, 5).until(
            # EC.element_to_be_clickable((By.ID, "su"))
            EC.element_to_be_clickable((By.ID, "chat-submit-button"))
        )
        submit_button.click()

        WebDriverWait(driver, 5).until(
            EC.title_contains(query[:10])
        )

        # 翻页优化
        page_text_list = []
        for i in range(1):
            if i > 0:
                results = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".page-inner_2jZi2>a"))
                )
                if i == 1:
                    results[i - 1].click()
                else:
                    results[i].click()

            WebDriverWait(driver, 10).until(
                # EC.presence_of_element_located((By.TAG_NAME, "body"))
                EC.presence_of_element_located((By.ID, "container"))
            )

            # 滚动优化
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

                # 检查是否加载完成
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # page_content = driver.find_element(By.TAG_NAME, "body")
            page_content = driver.find_element(By.ID, "container")
            page_text = page_content.get_attribute("innerHTML")
            page_text_list.append(page_text)

        driver.quit()

        html = '\n'.join(page_text_list)
        return pretty_html(html)

    except Exception as e:
        print(e)
        return ""


def pretty_html(html: str) -> str:
    # 未优化：713533
    # 移除指定标签后：589841
    # 移除所有display: none的标签后：307366
    # 移除注释后：270281
    # 移出无用属性后：141967
    # 只获取container数据后：116415

    # 移除指定标签
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "link", "meta", "symbol", "path", "canvas", "svg"]):
        tag.extract()

    # 移除所有display:none的标签
    display_none_re = re.compile(r"display\s*:\s*none", re.IGNORECASE)
    for tag in soup.find_all(True):
        style = tag.get("style", "")
        if display_none_re.search(style):
            tag.extract()

    # 移除所有代码注释
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 移除无用属性
    for tag in soup.find_all(True):
        if tag.name == "a":
            if "href" in tag.attrs:
                if "javascript:" in tag.attrs["href"] or "/" == tag.attrs["href"]:
                    tag.extract()
                else:
                    tag.attrs = {"href": tag.attrs["href"]}
        else:
            tag.attrs = {}

    html = soup.prettify()

    # print(html)
    # print(len(html))
    return html


if __name__ == "__main__":
    mcp.run(transport="stdio")
    # res = search_in_baidu("北京的天气")
    # print(res)
    # open_chrome()

    # search_in_baidu_with_html("北京的天气")