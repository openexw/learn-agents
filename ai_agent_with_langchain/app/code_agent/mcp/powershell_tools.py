import subprocess
import time
import psutil
import os
import pyautogui
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP()

def run_powershell_command(command: str, capture_output: bool = True):
    """执行 PowerShell 命令"""
    try:
        # 使用 PowerShell 执行命令
        cmd = ["powershell", "-Command", command]
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        else:
            result = subprocess.run(cmd, shell=True)
            return "", "", result.returncode
    except Exception as e:
        return "", str(e), 1


def get_powershell_processes():
    """获取所有 PowerShell 进程"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'powershell' in proc.info['name'].lower():
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': proc.info['cmdline']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes


def activate_powershell_window():
    """激活 PowerShell 窗口"""
    try:
        # 设置 pyautogui 的安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # 使用 Alt+Tab 切换到 PowerShell 窗口
        # 首先尝试通过窗口标题查找
        windows = pyautogui.getWindowsWithTitle('Windows PowerShell')
        if not windows:
            windows = pyautogui.getWindowsWithTitle('PowerShell')
        
        if windows:
            # 激活第一个找到的 PowerShell 窗口
            window = windows[0]
            window.activate()
            time.sleep(0.5)  # 等待窗口激活
            return True
        else:
            # 如果没找到窗口，尝试通过快捷键
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.5)
            return False
    except Exception as e:
        print(f"激活 PowerShell 窗口失败: {e}")
        return False


@mcp.tool(name="get_powershell_processes", description="获取所有 PowerShell 进程信息")
def get_all_powershell_processes() -> str:
    """获取所有正在运行的 PowerShell 进程列表"""
    try:
        processes = get_powershell_processes()
        if not processes:
            return "当前没有运行的 PowerShell 进程"

        result = "PowerShell 进程列表:\n"
        for proc in processes:
            result += f"PID: {proc['pid']}, 名称: {proc['name']}\n"
        return result
    except Exception as e:
        return f"获取 PowerShell 进程失败: {str(e)}"


@mcp.tool(name="close_powershell", description="关闭所有 PowerShell 进程")
def close_all_powershell() -> str:
    """关闭所有 PowerShell 进程"""
    try:
        processes = get_powershell_processes()
        if not processes:
            return "没有找到需要关闭的 PowerShell 进程"

        closed_count = 0
        for proc_info in processes:
            try:
                proc = psutil.Process(proc_info['pid'])
                proc.terminate()
                closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return f"已成功关闭 {closed_count} 个 PowerShell 进程"
    except Exception as e:
        return f"关闭 PowerShell 进程失败: {str(e)}"


@mcp.tool(name="open_powershell", description="打开新的 PowerShell 窗口")
def open_new_powershell(working_directory:
    Annotated[str, Field(description="可选的工作目录，为空则使用当前目录", examples="C:\\Users")] = "") -> str:
    """打开新的 PowerShell 窗口"""
    try:
        if working_directory and os.path.exists(working_directory):
            # 在指定目录打开 PowerShell
            command = f'Start-Process powershell -WorkingDirectory "{working_directory}"'
        else:
            # 在当前目录打开 PowerShell
            command = 'Start-Process powershell'

        stdout, stderr, returncode = run_powershell_command(command, capture_output=False)

        if returncode != 0 and stderr:
            return f"打开 PowerShell 失败: {stderr}"

        time.sleep(2)  # 等待窗口打开
        processes = get_powershell_processes()
        return f"PowerShell 已打开，当前运行进程数: {len(processes)}"
    except Exception as e:
        return f"打开 PowerShell 失败: {str(e)}"


@mcp.tool(name="run_powershell_script", description="通过 pyautogui 向 PowerShell 窗口发送命令")
def run_powershell_script(script: 
    Annotated[str, Field(description="要在 PowerShell 窗口中执行的脚本命令", examples="Get-Location")]) -> str:
    """通过 pyautogui 向活动的 PowerShell 窗口发送命令"""
    try:
        print("-" * 50)
        print("run_powershell_script (pyautogui):")
        print(script)
        print("-" * 50)
        
        # 检查是否有 PowerShell 进程在运行
        processes = get_powershell_processes()
        if not processes:
            return "没有找到运行中的 PowerShell 进程，请先打开 PowerShell 窗口"
        
        # 激活 PowerShell 窗口
        if not activate_powershell_window():
            return "无法激活 PowerShell 窗口，请确保 PowerShell 窗口已打开"
        
        # 清空当前输入行（如果有的话）
        pyautogui.hotkey('ctrl', 'c')  # 取消当前命令
        time.sleep(0.2)
        
        # 确保光标在命令行
        pyautogui.press('end')
        time.sleep(0.1)
        
        # 输入命令
        pyautogui.write(script, interval=0.02)
        time.sleep(0.3)
        
        # 按 Enter 执行命令
        pyautogui.press('enter')
        
        return f"命令已发送到 PowerShell 窗口: {script}"
        
    except Exception as e:
        return f"发送 PowerShell 命令失败: {str(e)}"


if __name__ == '__main__':
    mcp.run(transport="stdio")
    # 测试代码（注释掉）
    # close_all_powershell()
    # open_new_powershell()
    # run_powershell_script("Get-Location")
