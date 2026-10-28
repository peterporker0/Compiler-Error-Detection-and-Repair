# CodeLens AI — Compiler Studio

**Assignment 25:** LLM- and Machine Learning-Assisted Compiler for Intelligent Error Explanation and Code Repair.

CodeLens AI is a local-first educational prototype that combines a Python tokenizer, GCC C11 syntax diagnostics, heuristic semantic checks, a scikit-learn error/repair classifier, explanation templates, optional local Ollama explanations, and cautious repair-candidate validation.

## Run on Windows

1. Install Python and GCC. Confirm `python --version` and `gcc --version` work in VS Code's terminal.
2. Open this folder in VS Code.
3. In Terminal > New Terminal, run these one at a time:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe train_model.py
.\venv\Scripts\python.exe -m streamlit run app.py
```

4. Open the local URL shown by Streamlit, usually `http://localhost:8501`.

PowerShell activation is not required. This direct-venv approach also avoids the common execution-policy error.

## Tests

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Limitations

The included dataset is small and illustrative; do not claim high generalization accuracy from it. Semantic analysis is heuristic. A candidate passing GCC syntax validation does not prove program correctness. Submitted C code is syntax-checked and is not executed by the app. Review all proposed repairs manually.

## Optional local LLM

The app works without an LLM. To use local generation, install Ollama separately, pull a compatible model (for example `ollama pull llama3.2`), start Ollama, then enable **Use local Ollama model** in the sidebar.
