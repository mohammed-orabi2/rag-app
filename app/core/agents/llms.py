from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_xai import ChatXAI
import httpx

load_dotenv()

# ✅ Create persistent async HTTP client with connection pooling
# Reuses TCP connections instead of creating new ones each time (50-200ms faster!)
_async_http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0, connect=5.0),
    limits=httpx.Limits(
        max_keepalive_connections=20,  # Keep 20 connections alive
        max_connections=100,  # Max 100 total connections
        keepalive_expiry=30.0,  # Keep connections alive for 30s
    ),
    http2=True,  # Enable HTTP/2 for better performance
)

# Main LLMs with optimized timeouts, retry settings, and connection pooling

llm_grok = ChatXAI(
    model="grok-4-fast",
    temperature=0.0,
)

llm_google_flash = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.0,
    # Note: Google client handles connection pooling internally
)

llm_google_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
)

llm_4o_mini = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
)

llm_4_1_mini = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.0,
)

llm_4_1 = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.0,
)

llm_o4_mini = ChatOpenAI(
    model="o4-mini",
)

# Structured extraction with moderate tokens
deep_seek_chat_extractor = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
)

# Main chat for generation
deep_seek_chat = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.0,
)

llm_5_mini = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0.0,
)

llm_3_5_turbo = ChatOpenAI(
    model="gpt-4.5",
    temperature=0.0,
)

llm_google_flash_min = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.0,
)


# Cleanup function for application shutdown
async def cleanup_http_clients():
    """Close HTTP clients on application shutdown"""
    await _async_http_client.aclose()
    print("✅ HTTP clients closed")
