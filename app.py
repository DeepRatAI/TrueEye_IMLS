"""
TrueEye – Gradio front-end
UI inspired by the provided mock-up image.
Requires:
  - langflow
  - gradio >=4
  - anthropic   (API key via $ANTHROPIC_API_KEY)
Place this file next to `trueeye_flow.json`.
"""

import os
from pathlib import Path
import re
import gradio as gr
from langflow import load_flow_from_json

FLOW_PATH = Path(__file__).parent / "trueeye_flow.json"
flow = load_flow_from_json(str(FLOW_PATH))


# ─── Helpers ────────────────────────────────────────────────────────────────────
def extract_sections(markdown: str) -> dict:
    """Rudimentary splitter to populate cards individually."""
    sections = {
        "results": "",
        "risk": "—",
        "citations": [],
        "explanation": "",
        "tags": [],
    }

    # Risk (look for 'Nivel de Peligrosidad' or 'Risk Level: ...')
    risk_match = re.search(r"(Risk Level|Nivel de Peligrosidad).*?(Low|Moderate|High)",
                           markdown, re.I | re.S)
    if risk_match:
        sections["risk"] = risk_match.group(2).capitalize()

    # Citations: lines that look like URLs
    sections["citations"] = re.findall(r"https?://\S+", markdown)

    # Explanation block (heuristic: first bullet list or paragraph after tags)
    explanation_match = re.search(r"##? Explicación.*?\n([\s\S]+?)\n##", markdown)
    if explanation_match:
        sections["explanation"] = explanation_match.group(1).strip()

    # Bias / misinformation / manipulation tags
    tag_match = re.search(r"Matices detectados.*?:\s*(.+)", markdown)
    if tag_match:
        tags_raw = tag_match.group(1)
        sections["tags"] = [t.strip().capitalize() for t in re.split(r",|\|", tags_raw)]

    # Detection results = summary paragraph after title
    det_match = re.search(r"Resumen del corpus\s*:\s*\n([\s\S]+?)\n\n", markdown)
    if det_match:
        sections["results"] = det_match.group(1).strip()

    return sections


def gauge_value(risk: str) -> float:
    return {"Low": 0.25, "Moderate": 0.5, "High": 0.75}.get(risk, 0.0)


# ─── Core inference ─────────────────────────────────────────────────────────────
def analyze(url: str):
    if not url:
        return gr.update(value=""), "", 0.0, "", [], []

    out = flow({"Chat Input": url})
    report = out["Chat Output"].strip()

    # Parse sections for fancy UI parts
    parts = extract_sections(report)
    risk_val = gauge_value(parts["risk"])

    return (report,
            parts["results"],
            risk_val,
            parts["explanation"],
            parts["tags"],
            parts["citations"])


# ─── Interface ──────────────────────────────────────────────────────────────────
with gr.Blocks(theme=gr.themes.Soft(text_size="base"), css="""
#side {background:#111;}
.card   {background:#1b1d22; border-radius:8px; padding:16px;}
.tag    {background:#273043; color:#a1c9f1; padding:4px 10px; border-radius:6px;}
""") as demo:
    # Sidebar
    with gr.Row():
        gr.Markdown("<h2 style='margin:0;color:#38bdf8'>TrueEye</h2>"
                    "<span style='color:#0ea5e9;font-size:14px'>Intelligent Media Literacy System</span>")
        analyze_btn = gr.Button("Analyze", scale=0)

    url_in = gr.Textbox(placeholder="Enter URL or text to analyze")

    with gr.Row():
        with gr.Column():
            # Detection Results card
            with gr.Column(elem_classes="card"):
                gr.Markdown("### Detection Results")
                results_box = gr.Textbox(show_label=False, interactive=False)

            # Tags
            tags_box = gr.HighlightedText(value=[], color_map={}, elem_id="tags")

            # Explanation card
            with gr.Column(elem_classes="card"):
                gr.Markdown("### Explanation")
                explanation_box = gr.Textbox(show_label=False, interactive=False)

        with gr.Column():
            # Risk Gauge
            with gr.Column(elem_classes="card"):
                gr.Markdown("### Risk Level")
                risk_gauge = gr.Gauge(label="", value=0.0, minimum=0, maximum=1)

            # Citations
            with gr.Column(elem_classes="card"):
                gr.Markdown("### Citations")
                citations_box = gr.Markdown()

    # Full report hidden (expandable)
    full_report = gr.Markdown(visible=False)

    # Bind actions
    url_in.submit(analyze, url_in,
                  [full_report, results_box, risk_gauge, explanation_box,
                   tags_box, citations_box])
    analyze_btn.click(analyze, url_in,
                      [full_report, results_box, risk_gauge, explanation_box,
                       tags_box, citations_box])

demo.launch(debug=True)

