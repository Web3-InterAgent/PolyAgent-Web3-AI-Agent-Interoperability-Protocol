import os

class Config:
    """
    基础配置类，用于存放应用的核心设置。
    """
    # OpenAI API 配置
    # 强烈建议使用环境变量来设置 API 密钥，避免硬编码
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')
    OPENAI_API_URL = os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1/')
    
    # ModelScope API 配置  
    MODELSCOPE_API_KEY = os.getenv('MODELSCOPE_API_KEY', 'your-modelscope-api-key-here')

    # 服务器配置
    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    # 在生产环境中应设置为 False
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')

    # IoTeX 网络配置
    IOTEX_RPC_URL = os.getenv('IOTEX_RPC_URL', 'https://babel-api.testnet.iotex.io')
    IOTEX_CHAIN_ID = int(os.getenv('IOTEX_CHAIN_ID', 4690))

# 导出一个可直接使用的配置实例
config = Config() 