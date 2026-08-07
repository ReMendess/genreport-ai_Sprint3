from app.rag_engine import ask_question
from app.report_pipeline import prepare_vector_store

print("Carregando relatório...")
vectordb, pdf_path, _ = prepare_vector_store()
print(f"Relatório indexado: {pdf_path.name}")

while True:
    question = input("\nPergunta: ")

    if question.lower() == "sair":
        break

    result = ask_question(vectordb, question)

    print("\nRESPOSTA:")
    print(result["answer"])

    print("\nFONTES UTILIZADAS:")
    print(result["sources"])
