import streamlit as st
from core.tokenizer import analyze_token_usage, format_token_report
from agents.cache_agent import CacheAgent

st.set_page_config(
    layout="wide",
    page_title="Trading Analysis",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Trading Analysis System - Educational purposes only",
    },
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_tokens" not in st.session_state:
    st.session_state.show_tokens = False
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False


@st.cache_resource(show_spinner=False)
def get_system():
    from core.system_builder import build_system

    return build_system("data/data.pdf")


if "manager" not in st.session_state:
    st.session_state.manager = get_system()

if "cache_agent" not in st.session_state:
    from llama_index.core import Settings

    st.session_state.cache_agent = CacheAgent(
        embed_model=Settings.embed_model, max_cache_size=50, similarity_threshold=0.8
    )

col1, col2 = st.columns([2.5, 1])

with col1:
    st.markdown("💬 Chat")

    chat_container = st.container(height=600)

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "token_info" in msg and st.session_state.show_tokens:
                    st.caption(msg["token_info"])

    user_input = st.chat_input(
        (
            "Processing..."
            if st.session_state.is_processing
            else "Ask about trading data..."
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

        cached = st.session_state.cache_agent.get(prompt)

        if cached:
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    st.markdown(cached["response"])

                    similarity = cached.get("similarity", 1.0)
                    if similarity == 1.0:
                        st.caption("💾 Cached response (exact match)")
                    else:
                        st.caption(
                            f"💾 Cached response (similar query: {similarity:.0%})"
                        )

                    if st.session_state.show_tokens:
                        st.caption(cached["token_info"])

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": cached["response"],
                    "token_info": cached["token_info"],
                }
            )
            st.session_state.is_processing = False
            st.rerun()

        else:
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    manager = st.session_state.manager

                    status_placeholder = st.empty()
                    message_placeholder = st.empty()

                    full_response = ""
                    contexts = []
                    stream_started = False

                    with status_placeholder:
                        with st.spinner("🔄 Processing..."):
                            st.caption("🧠 Routing to agent...")
                            st.caption("📊 Retrieving contexts...")
                            st.caption("🔍 Running AutoMerging...")

                            for delta, ctxs, is_final in manager.route_stream(prompt):
                                if not is_final:
                                    if not stream_started:
                                        status_placeholder.empty()
                                        stream_started = True

                                    full_response += delta
                                    message_placeholder.markdown(full_response + "▌")
                                else:
                                    full_response = delta
                                    contexts = ctxs

                    status_placeholder.empty()
                    message_placeholder.markdown(full_response)

                    if st.session_state.show_tokens:
                        token_data = analyze_token_usage(
                            query=prompt,
                            answer=full_response,
                            contexts=contexts,
                            response_obj=None,
                        )
                        st.caption(format_token_report(token_data))

                    token_data = analyze_token_usage(
                        prompt, full_response, contexts, None
                    )
                    token_info = format_token_report(token_data)

                    st.session_state.cache_agent.put(
                        prompt, full_response, contexts, token_info
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": full_response,
                            "token_info": token_info,
                        }
                    )

            st.session_state.is_processing = False
            st.rerun()

with col2:
    st.markdown("**📊 Statistical Queries**")

    for q in [
        "What was the highest daily percentage increase?",
        "What was the lowest daily percentage change?",
        "Which day had the largest volume?",
    ]:
        if st.button(q, key=f"stat_{q}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

    st.markdown("**📅 Date-Specific**")

    for q in [
        "What happened on 2025-11-10?",
        "Show me trading data for November 20",
        "What was the close price on 2025-11-24?",
    ]:
        if st.button(q, key=f"date_{q}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

    st.markdown("**📈 Analytical**")

    for q in [
        "Compare first vs last week",
        "How many [UP] days?",
        "Average closing price?",
        "7-day moving average",
        "Summarize November trend",
    ]:
        if st.button(q, key=f"anal_{q}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

with st.sidebar:
    st.header("⚙️ Settings")

    st.session_state.show_tokens = st.checkbox(
        "Show Token Usage", value=st.session_state.show_tokens
    )

    st.divider()

    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.markdown("**📚 System Info**")
    st.caption("• Hierarchical Indexing")
    st.caption("• AutoMerging Retrieval")
    st.caption("• MapReduce Summaries")

    st.divider()

    stats = st.session_state.cache_agent.get_stats()
    st.caption(f"💾 Cached: {stats['total_cached']}/{stats['max_size']}")
    st.caption(f"🎯 Threshold: {stats['similarity_threshold']:.0%}")
    st.caption(f"🧠 Method: {stats['method']}")
