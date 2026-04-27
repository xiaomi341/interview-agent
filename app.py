import streamlit as st
import os
import sys
from langchain_core.messages import HumanMessage, AIMessage
# from langgraph.checkpoint import RunnableConfig

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import build_agent

# 页面配置
st.set_page_config(
    page_title="模拟面试官",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .ai-message {
        background-color: #f1f8e9;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #4caf50;
    }
    .jd-input {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #ff9800;
    }
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "config" not in st.session_state:
    st.session_state.config = None
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""

def init_agent():
    """初始化Agent"""
    if st.session_state.agent is None:
        with st.spinner("正在初始化面试官..."):
            try:
                st.session_state.agent = build_agent()
                # 生成唯一的thread_id
                import uuid
                st.session_state.thread_id = str(uuid.uuid4())
                # 创建配置
                st.session_state.config = RunnableConfig(
                    configurable={"thread_id": st.session_state.thread_id}
                )
                st.success("面试官初始化成功！")
            except Exception as e:
                st.error(f"初始化失败: {str(e)}")
                return False
    return True

def reset_conversation():
    """重置对话"""
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.session_state.config = None
    st.session_state.jd_text = ""
    # 重新初始化agent
    st.session_state.agent = None

# 主界面
st.markdown('<div class="main-title">🎯 模拟面试官</div>', unsafe_allow_html=True)

st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("📋 岗位JD")
    jd_text = st.text_area(
        "请输入岗位JD（职位描述）",
        value=st.session_state.jd_text,
        height=300,
        placeholder="例如：\n岗位要求：\n1. 3年以上Java开发经验\n2. 熟悉Spring Boot、Spring Cloud\n3. 有高并发系统经验\n..."
    )
    st.session_state.jd_text = jd_text

    st.markdown("---")
    st.header("🔧 操作")
    if st.button("🔄 开始新面试", type="primary"):
        reset_conversation()
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 使用说明")
    st.markdown("""
    1. 在上方输入岗位JD
    2. 点击"开始新面试"重置对话
    3. 在输入框中输入消息开始面试
    4. 面试官会根据JD对你进行连环追问
    """)

# 检查JD是否已输入
if not st.session_state.jd_text:
    st.info("👈 请先在左侧侧边栏输入岗位JD，然后开始面试")
    st.stop()

# 初始化Agent
if not init_agent():
    st.stop()

# 如果有JD但没有对话历史，自动添加开始消息
if st.session_state.jd_text and len(st.session_state.messages) == 0:
    start_message = f"你好，我想应聘这个岗位，JD如下：\n\n{st.session_state.jd_text}\n\n麻烦开始面试。"
    st.session_state.messages.append({"role": "user", "content": start_message})

    # 发送第一条消息给agent
    with st.spinner("面试官正在思考..."):
        try:
            response = st.session_state.agent.invoke(
                {"messages": [HumanMessage(content=start_message)]},
                config=st.session_state.config
            )
            ai_message = response["messages"][-1]
            st.session_state.messages.append({
                "role": "assistant",
                "content": ai_message.content
            })
        except Exception as e:
            st.error(f"获取面试官回复失败: {str(e)}")

# 显示对话历史
st.markdown("### 💬 面试对话")
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.container():
            st.markdown(f'<div class="user-message"><strong>👤 你：</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.container():
            st.markdown(f'<div class="ai-message"><strong>🤖 面试官：</strong><br>{message["content"]}</div>', unsafe_allow_html=True)

# 用户输入
st.markdown("---")
user_input = st.text_area(
    "请输入你的回答",
    placeholder="请回答面试官的问题...",
    height=100,
    key="user_input"
)

# 发送按钮
if st.button("发送", type="primary"):
    if user_input.strip():
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 清空输入框
        st.session_state.user_input = ""

        # 获取AI回复
        with st.spinner("面试官正在思考..."):
            try:
                # 构建消息历史
                messages = []
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))

                # 调用agent
                response = st.session_state.agent.invoke(
                    {"messages": messages},
                    config=st.session_state.config
                )

                # 添加AI回复
                ai_message = response["messages"][-1]
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_message.content
                })

                # 重新运行以显示更新
                st.rerun()

            except Exception as e:
                st.error(f"获取面试官回复失败: {str(e)}")
                st.error(f"错误详情: {e}")
else:
    st.warning("请输入内容后再发送")

# 底部信息
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8rem;'>
    💡 提示：面试官会根据你的回答进行深度追问，请详细回答每个问题。
</div>
""", unsafe_allow_html=True)
