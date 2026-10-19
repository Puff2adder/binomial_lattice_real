# Binomial Decisions Studio

An interactive Executive MBA learning studio for binomial option pricing and staged investment decisions. Instructor: Peter Ritchken.

## Deploy this folder

Upload **the contents of this folder** to the root of a GitHub repository. The repository root should contain `app.py` and `requirements.txt`. Preserve `.streamlit/config.toml` and `lattice_component/index.html`, including their folder names.

In Streamlit Community Cloud choose your repository and branch, use **app.py** as the main file, and select **Python 3.13** in Advanced settings. No secrets or API keys are required. See [DEPLOYMENT.md](DEPLOYMENT.md) for the complete steps.

## Run locally

From this folder, with Python 3.13 installed:

```sh
python -m venv .venv
```

Activate it on Windows with `.venv\Scripts\activate`, or on macOS/Linux with `source .venv/bin/activate`. Then:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Learning activities

- Build the lattice: calls/puts, European/American exercise, simple options/access gates, one to four periods, and dividend/convenience yield.
- Five guided problems: one period; two periods; two periods with gates; three periods; four periods with selected gates.
- Five multiple-choice setup questions reveal dt, u, d, R and p.
- Click a node and enter an expression. Correct values fill the lattice; incorrect entries can be retried. Earlier nodes require completed child values.
- In three- and four-period guided cases, a correct answer offers optional assisted completion of the rest of the column.
- Full worked lattices, interpretation questions and small experiments remain available.

All materials are ungraded practice. Each browser session has separate progress; progress is not a permanent student record. Students can download their own practice record. No student accounts or grade transmission are implemented. Worked answers are intentionally included.

## Files

| File | Purpose |
|---|---|
| app.py | Main Streamlit application, navigation and shared displays |
| builder.py / builder_model.py | Construction workspace and exercise/gate model |
| guided.py | Guided setup questions and clickable lecture exercises |
| finance.py | Lecture lattice engine and European benchmark calculations |
| content.py / questions.py | Lecture examples, rules and interpretation questions |
| calculator.py | Restricted mathematical expression evaluator |
| lattice_component/index.html | Local clickable lattice component; required at runtime |
| .streamlit/config.toml | Light theme and telemetry setting |
| requirements.txt | Tested Streamlit dependency version |
| tests/ | Automated mathematical and interface tests |
| MODEL_NOTES.md | Financial assumptions and teaching conventions |
| VALIDATION.md | Verification performed and release limits |
| RELEASE_MANIFEST.json | Packaged files and SHA-256 checksums |

## Run the tests

```sh
python -m unittest discover -s tests -v
```

The app does not require Excel, VBA, LaTeX, Node.js, external data files or a paid service. The HTML component is already built and served locally by Streamlit.
