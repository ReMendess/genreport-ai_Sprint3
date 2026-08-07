import streamlit as st

from app.config import RAW_DATA_DIR
from app.ui import inject_dasa_styles, render_hero, render_info_cards


@st.cache_resource(show_spinner=False)
def load_vector_store():
    from app.report_pipeline import prepare_vector_store

    vectordb, pdf_path, fingerprint = prepare_vector_store()
    return vectordb, pdf_path.name, fingerprint


@st.cache_resource(show_spinner=False)
def load_report_data():
    """Carrega os dados estruturados do relatório para o dashboard."""
    from app.report_parser import load_parsed_report

    return load_parsed_report()


def render_sidebar(report_name: str, fingerprint: str) -> None:
    st.sidebar.markdown(
        """
        <div style="text-align:center;padding:0.5rem 0 1rem 0;">
            <span style="font-size:2rem;font-weight:800;letter-spacing:0.12em;">DASA</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("### Relatório carregado")
    st.sidebar.success(f"**{report_name}**")
    st.sidebar.caption(f"Origem: `{RAW_DATA_DIR}`")
    st.sidebar.caption(f"Cache: `{fingerprint[:24]}…`")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Ações")
    if st.sidebar.button("Reprocessar relatório"):
        from app.vector_store import clear_vector_cache

        clear_vector_cache()
        st.cache_resource.clear()
        st.session_state.messages = []
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        **Sugestões de perguntas**
        - Quais são meus principais riscos genéticos?
        - O que significam os resultados do relatório?
        - Quais hábitos de prevenção são recomendados?
        """
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Este assistente não substitui consulta médica. "
        "Sempre consulte um profissional de saúde."
    )


def render_navigation() -> str:
    """Barra de navegação principal (Dashboard / Assistente)."""
    st.sidebar.markdown("### Navegação")
    page = st.sidebar.radio(
        "Ir para",
        ["📊 Dashboard", "💬 Assistente"],
        label_visibility="collapsed",
    )
    return page


def render_dashboard_page() -> None:
    """Tela principal: dashboard com resumo do relatório genético."""
    from app.dashboard import render_dashboard

    report = load_report_data()
    render_dashboard(report)


def render_chat_page(vectordb) -> None:
    """Tela do assistente conversacional (RAG) — funcionalidade existente."""
    render_hero()
    render_info_cards()

    st.markdown("### Assistente genético")

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧬" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("Fontes utilizadas"):
                    st.markdown(message["sources"])

    if prompt := st.chat_input("Faça uma pergunta sobre o seu relatório genético..."):
        from app.rag_engine import ask_question

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🧬"):
            with st.spinner("Analisando relatório…"):
                result = ask_question(vectordb, prompt)
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander("Fontes utilizadas"):
                    st.markdown(result["sources"])

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
            }
        )


def main():
    inject_dasa_styles()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    try:
        with st.spinner("Carregando índice do relatório…"):
            vectordb, report_name, fingerprint = load_vector_store()
    except Exception as exc:
        from app.report_pipeline import ReportNotFoundError

        if isinstance(exc, ReportNotFoundError):
            st.error(str(exc))
            st.info(
                f"Adicione o arquivo PDF em `{RAW_DATA_DIR}` "
                "(por exemplo, `genetic_report.pdf`) e recarregue a página."
            )
        else:
            st.error(f"Erro ao processar o relatório: {exc}")
        return

    render_sidebar(report_name, fingerprint)
    page = render_navigation()

    if page == "📊 Dashboard":
        render_dashboard_page()
    else:
        render_chat_page(vectordb)


if __name__ == "__main__":
    main()