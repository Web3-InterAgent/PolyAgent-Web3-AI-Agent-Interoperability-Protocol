import requests
import time
import json

def test_stream_hello(text_input: str = "hello world"):
    """
    测试流式hello接口的客户端
    """
    url = "http://127.0.0.1:8001/hello"
    
    # 准备请求数据
    data = {"text": text_input}
    headers = {"Content-Type": "application/json"}
    
    print(f"正在调用流式API，输入内容: '{text_input}'")
    print("响应内容:", end=" ")
    
    try:
        # 发送POST请求并获取流式响应
        response = requests.post(url, json=data, headers=headers, stream=True)
        
        if response.status_code == 200:
            # 逐字符接收并打印响应
            for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                if chunk:
                    print(chunk, end="", flush=True)
                    time.sleep(0.05)  # 添加小延迟来看清流式效果
            print()  # 换行
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        print("请确保服务器正在运行 (python simple_server.py)")

def interactive_test():
    """
    交互式测试函数
    """
    print("=== FastAPI 流式响应测试 ===")
    while True:
        user_input = input("\n请输入要转换为大写的文本 (输入 'quit' 退出): ")
        if user_input.lower() == 'quit':
            print("再见！")
            break
        
        test_stream_hello(user_input)

if __name__ == "__main__":
    # 首先进行一个默认测试
    test_stream_hello("hello world")
    
    # 然后进入交互模式
    interactive_test()
