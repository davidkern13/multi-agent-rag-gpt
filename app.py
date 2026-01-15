"""
Streamlit App - SEC Filing Analysis
Based on original structure - only bug fix and topic adaptation
"""

import streamlit as st
import time

st.set_page_config(
    layout="wide",
    page_title="SEC Filing Analysis",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "SEC Filing Analysis System - Educational purposes only",
    },
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_confidence" not in st.session_state:
    st.session_state.show_confidence = True
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False


@st.cache_resource(show_spinner=False)
def get_system():
    from core.system_builder import build_system
    return build_system()


if "manager" not in st.session_state:
    st.session_state.manager = get_system()

col1, col2 = st.columns([2.5, 1])

with col1:
    st.markdown("💬 Chat")

    chat_container = st.container(height=600)

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("confidence") and st.session_state.show_confidence:
                    conf_icons = {"high": "🟢", "medium": "🟡", "low": "🟠", "uncertain": "🔴"}
                    conf = msg.get("confidence", "")
                    if conf in conf_icons:
                        st.caption(f"{conf_icons[conf]} Confidence: {conf}")

    user_input = st.chat_input(
        (
            "Processing..."
            if st.session_state.is_processing
            else "Ask about SEC filing..."
        ),
        disabled=st.session_state.is_processing,
    )

    st.markdown(
        "<p style='text-align: center; color: #888; font-size: 0.85em; margin-top: 0.5rem;'>"
        "⚠️ AI can make mistakes • Not financial advice • Educational purposes only"
        "</p>",
        unsafe_allow_html=True,
    )

    prompt = None
    if st.session_state.pending_query:
        prompt = st.session_state.pending_query
        st.session_state.pending_query = None
    elif user_input:
        prompt = user_input

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.is_processing = True

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                manager = st.session_state.manager

                status_placeholder = st.empty()
                message_placeholder = st.empty()

                with status_placeholder:
                    with st.spinner("🔄 Processing..."):
                        st.caption("🧠 Routing to agent...")
                        st.caption("📊 Retrieving contexts...")
                        st.caption("🔍 Running AutoMerging...")

                        # FIX: Use non-streaming to avoid bug
                        answer, contexts, meta = manager.route(prompt)

                status_placeholder.empty()
                
                # FIX: Typing animation after response is ready
                displayed = ""
                for char in answer:
                    displayed += char
                    message_placeholder.markdown(displayed + "▌")
                    time.sleep(0.003)
                
                message_placeholder.markdown(answer)

                # Show confidence
                confidence = meta.get("confidence") if meta else None
                if confidence and st.session_state.show_confidence:
                    conf_icons = {"high": "🟢", "medium": "🟡", "low": "🟠", "uncertain": "🔴"}
                    if confidence in conf_icons:
                        st.caption(f"{conf_icons[confidence]} Confidence: {confidence}")

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "confidence": confidence,
                    }
                )

        st.session_state.is_processing = False
        st.rerun()

with col2:
    st.markdown("**🔍 Deep Analysis**")

    for q in [
        "What can we infer about the company's future?",
        "What are the main risks and their impact?",
        "How does management view competitive position?",
    ]:
        if st.button(q, key=f"deep_{q}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

    st.markdown("**📊 Financial Health**")

    for q in [
        "Is the company financially healthy? Why?",
        "What are the warning signs?",
        "What does cash flow tell us?",
    ]:
        if st.button(q, key=f"health_{q}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

    st.markdown("**🎯 Management & Strategy**")

    for q in [
        "What is management's outlook?",
        "What are the growth initiatives?",
        "What assumptions is management making?",
    ]:
        if st.button(q, key=f"mgmt_{q}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

    st.markdown("**📈 Specific Data**")

    for q in [
        "What was the total revenue?",
        "What was the net income or loss?",
        "How much cash does the company have?",
        "What are the main risk factors?",
        "How did revenue change YoY?",
    ]:
        if st.button(q, key=f"data_{q}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

with st.sidebar:
    st.header("⚙️ Settings")

    st.session_state.show_confidence = st.checkbox(
        "Show Confidence Level", value=st.session_state.show_confidence
    )

    st.divider()

    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        if hasattr(st.session_state.manager, 'clear_memory'):
            st.session_state.manager.clear_memory()
        st.rerun()

    st.divider()

    st.markdown("**📚 System Info**")
    st.caption("• Hierarchical Indexing")
    st.caption("• AutoMerging Retrieval")
    st.caption("• Conversation Memory")
    st.caption("• Human-in-the-Loop")