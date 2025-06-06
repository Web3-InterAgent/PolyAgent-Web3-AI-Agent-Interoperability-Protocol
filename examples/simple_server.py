from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Callable, Optional
import uvicorn
import time
import asyncio

class MessageRequest(BaseModel):
    text: str

async def default_hello_handler(request: MessageRequest):
    """
    默认的hello处理函数：接收用户输入的内容，将其转换为大写并流式返回
    """
    async def generate_response():
        # 将输入文本转换为大写
        message = request.text.upper()
        # 逐字符流式返回
        for char in message:
            yield char
            await asyncio.sleep(0.1)  # 添加小延迟来模拟流式效果
    
    return StreamingResponse(generate_response(), media_type="text/plain")

def start_server(
    hello_handler: Optional[Callable] = None,
    host: str = "127.0.0.1", 
    port: int = 8001
):
    """
    启动HTTP服务的函数
    Args:
        hello_handler: 处理/hello接口的函数，如果为None则使用默认处理函数
        host: 服务器主机地址
        port: 服务器端口
    """
    app = FastAPI()
    
    # 如果没有提供handler，使用默认的handler
    if hello_handler is None:
        hello_handler = default_hello_handler
    
    # 注册hello接口
    app.post("/hello")(hello_handler)
    
    print(f"Starting server at http://{host}:{port}")
    print(f"API endpoint: POST http://{host}:{port}/hello")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()