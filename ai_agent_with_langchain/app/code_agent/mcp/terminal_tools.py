import subprocess
import time
from typing import Annotated, List

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP()

def run_applescript(script):
    p = subprocess.Popen(["osascript", "-e", script],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, error = p.communicate()

    return output.decode("utf-8").strip(), error.decode("utf-8").strip()


def get_all_terminal_window_ids() -> str:
    """获取所有终端窗口的ID列表"""
    output, error = run_applescript("""
tell application "Terminal"
    set outputList to {}
    repeat with aWindow in windows
        set windowID to id of aWindow
        set tabCount to number of tabs of aWindow
        repeat with tabIndex from 1 to tabCount
            set end of outputList to {tab tabIndex of window id windowID}
        end repeat
    end repeat
end tell
return outputList
""")
    if error:
        return f"错误: {error}"
    return output


def parse_key_code(button):
    button = button.lower()

    keycode_map = {
        'return': 'return',
        'space': 'space',
        'up': 126,
        'down': 125,
        'left': 123,
        'right': 124,
        'a': 0,
        'b': 11,
        'c': 8,
        'd': 2,
        'e': 14,
        'f': 3,
        'g': 5,
        'h': 4,
        'i': 34,
        'j': 38,
        'k': 40,
        'l': 37,
        'm': 46,
        'n': 45,
        'o': 31,
        'p': 35,
        'q': 12,
        'r': 15,
        's': 1,
        't': 17,
        'u': 32,
        'v': 9,
        'w': 13,
        'x': 7,
        'y': 16,
        'z': 6,
        '.': 47,
        'dot': 47,
        '0': 29,
        '1': 18,
        '2': 19,
        '3': 20,
        '4': 21,
        '5': 23,
        '6': 22,
        '7': 26,
        '8': 28,
        '9': 25,
        '-': 27,
    }

    return keycode_map[button]


def concat_key_codes(key_codes):
    script = ''
    for key in key_codes:
        key_code = parse_key_code(key)
        script += f'keystroke {key_code}\n'
        script += 'delay 0.5\n'
    return script.strip()


@mcp.tool(name="send_terminal_keyboard_key", description="send a terminal keyboard key to an existing terminal")
def send_terminal_keyboard_key(key_codes: Annotated[List[str], Field(description="向终端输入一组按键", examples="['up', 'down']")]) -> bool:
    print('\nsend_terminal_keyboard_key keycode:', key_codes)
    print('-' * 50)
    script = f'''
tell application "Terminal"
    activate
    tell application "System Events"
        {concat_key_codes(key_codes)}
    end tell
end tell'''
    print(script)
    terminal_content, error = run_applescript(script)
    if error:
        return False
    else:
        return True


@mcp.tool(name="close_terminal", description="关闭终端应用程序")
def close_terminal_if_open() -> str:
    """关闭终端应用程序（如果正在运行）"""
    output, error = run_applescript("""
tell application "System Events"
    if exists process "Terminal" then
        tell application "Terminal" to quit
    end if
end tell
""")
    if error:
        return f"关闭终端失败: {error}"
    else:
        return "终端已成功关闭"


@mcp.tool(name="open_terminal", description="打开新的终端窗口")
def open_new_terminal(window_id: 
    Annotated[str, Field(description="可选的窗口ID，为空则打开新窗口", examples="12345")] = "") -> str:
    """打开新的终端窗口或激活指定的窗口"""
    if window_id:
        output, error = run_applescript(f"""
tell application "Terminal"
    if (count of windows) > 0 then
        set theWindow to window id {window_id}
        set frontmost of theWindow to true
        activate
    else
        activate
    end if
end tell""")

    else:
        output, error = run_applescript(f"""
tell application "Terminal"
    activate
end tell""")
    
    if error:
        return f"打开终端失败: {error}"
    else:
        time.sleep(2)  # 减少等待时间
        window_ids = get_all_terminal_window_ids()
        return f"终端已打开，窗口ID: {window_ids}"


@mcp.tool(name="run_terminal_script", description="在终端中运行脚本命令")
def run_script_in_terminal(script: 
    Annotated[str, Field(description="要在终端中执行的脚本命令", examples="ls -al")]) -> str:
    """在终端中运行指定的脚本命令"""
    print("-" * 50)
    print("run_script_in_terminal:")
    print(script)
    print("-" * 50)
    output, error = run_applescript(f"""
tell application "Terminal"
    activate
    if (count of windows) > 0 then
        do script "{script}" in window 1
    else
        do script "{script}"
    end if
end tell""")
    if error:
        return f"执行脚本失败: {error}"
    else:
        return f"脚本已执行: {script}"


@mcp.tool(name="get_terminal_text", description="获取终端的完整文本内容")
def get_terminal_full_text() -> str:
    """获取当前选中终端标签页的完整历史文本"""
    output, error = run_applescript(f"""
tell application "Terminal"
    set fullText to history of selected tab of front window
end tell""")
    if error:
        return f"获取终端文本失败: {error}"
    else:
        return output


if __name__ == '__main__':
    mcp.run(transport="stdio")
    # close_terminal_if_open()
    # window_ids = open_new_terminal()
    # print(window_ids)

    # run_script_in_terminal("pwd")
    # full_text = get_terminal_full_text()
    # print(full_text)