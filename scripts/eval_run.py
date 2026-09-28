"""Executa a avaliação (set dorado) e gera evidência JSON + Markdown.

Uso:
    python scripts/eval_run.py                    # 2 execuções por pergunta
    python scripts/eval_run.py --runs 1 --limit 5 # smoke rápido

Saídas (padrão):
    data/eval/relatorio_avaliacao.json
    docs/evidencia_evaluacion_sprint4.md

As respostas são redigidas contra o nome do paciente (LGPD) antes de serem
persistidas — vazio se o relatório não puder ser lido.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.evaluation.harness import evaluate, load_golden_set, render_markdown  # noqa: E402
from app.governance.policy import mask_name  # noqa: E402
from app.report_pipeline import prepare_vector_store  # noqa: E402

DEFAULT_GOLDEN = ROOT / "data" / "eval" / "questions.json"
DEFAULT_JSON = ROOT / "data" / "eval" / "relatorio_avaliacao.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "evidencia_evaluacion_sprint4.md"


def build_redactor():
    """Redator de PII: mascara o nome do paciente nas respostas."""
    try:
        from app.report_parser import load_parsed_report

        name = load_parsed_report().patient_name
    except Exception:
        name = None

    if not name:
        return None

    masked = mask_name(name)

    def redact(text: str) -> str:
        return text.replace(name, masked)

    return redact


def main() -> int:
    parser = argparse.ArgumentParser(description="Avaliação do modelo (Etapa 5)")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()

    print(f"Carregando set dorado: {args.golden}")
    golden_meta, questions = load_golden_set(args.golden)
    print(f"{len(questions)} perguntas — execuções por pergunta: {args.runs}")

    print("Carregando índice vetorial + pipeline RAG...")
    vectordb, pdf_path, _fingerprint = prepare_vector_store()
    print(f"Relatório: {pdf_path.name}")

    redactor = build_redactor()
    print(f"Redação de PII: {'ativo' if redactor else 'sem nome detectado'}")
    print("-" * 60)

    report = evaluate(
        vectordb,
        questions,
        runs=args.runs,
        redactor=redactor,
        limit=args.limit,
        progress=print,
    )

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    markdown = render_markdown(report, golden_meta=golden_meta)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(markdown, encoding="utf-8")

    summary = report["summary"]
    print("-" * 60)
    print(f"Veredito: {report['verdict']['status']}")
    print(f"Aderência: {summary['behavior_accuracy']} | Consistência: {summary['consistency_rate']}")
    print(f"Groundedness média: {summary['groundedness_mean']} | Violações: {summary['policy_violations']}")
    print(f"Falhas: {len(summary['failures'])}")
    print(f"JSON: {args.json_out}")
    print(f"Evidência: {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
