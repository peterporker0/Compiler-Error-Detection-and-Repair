from pathlib import Path
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "error_dataset.csv"
MODELS = ROOT / "models"

def build_model():
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42)),
    ])

def _training_text(df):
    return [f"diagnostic: {row.error_message} context: {row.code_context}" for row in df.itertuples()]

def train_models():
    df = pd.read_csv(DATA).fillna("")
    required = {"error_message", "code_context", "error_type", "repair_type"}
    if not required.issubset(df.columns):
        raise ValueError(f"Dataset must contain columns: {', '.join(sorted(required))}")
    if len(df) < 4:
        raise ValueError("Add at least four labelled rows before training.")
    X = _training_text(df)
    error_model, repair_model = build_model(), build_model()
    error_model.fit(X, df["error_type"].astype(str))
    repair_model.fit(X, df["repair_type"].astype(str))
    MODELS.mkdir(exist_ok=True)
    joblib.dump(error_model, MODELS / "error.joblib")
    joblib.dump(repair_model, MODELS / "repair.joblib")
    return {"rows": len(df), "errors": sorted(df.error_type.astype(str).unique()), "repairs": sorted(df.repair_type.astype(str).unique())}

def load_models():
    if not (MODELS / "error.joblib").exists() or not (MODELS / "repair.joblib").exists():
        train_models()
    return joblib.load(MODELS / "error.joblib"), joblib.load(MODELS / "repair.joblib")

def predict(message, context):
    error_model, repair_model = load_models()
    text = f"diagnostic: {message} context: {context}"
    error_probs = error_model.predict_proba([text])[0]
    repair_probs = repair_model.predict_proba([text])[0]
    return {
        "error_type": str(error_model.predict([text])[0]),
        "repair_type": str(repair_model.predict([text])[0]),
        "error_confidence": float(max(error_probs)),
        "repair_confidence": float(max(repair_probs)),
    }

def evaluate_models(test_size=0.3):
    """Exploratory held-out evaluation. Results are unreliable on tiny/imbalanced datasets."""
    df = pd.read_csv(DATA).fillna("")
    X = _training_text(df)
    report = {"rows": len(df), "warning": "Starter dataset is small; metrics are exploratory, not evidence of production accuracy."}
    target = df["error_type"].astype(str)
    counts = target.value_counts()
    can_stratify = len(counts) > 1 and counts.min() >= 2 and len(df) >= 8
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, target, test_size=test_size, random_state=42,
            stratify=target if can_stratify else None,
        )
        if len(set(y_train)) < 2:
            raise ValueError("Not enough classes in training split.")
        model = build_model()
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, pred, average="weighted", zero_division=0)
        report.update({
            "evaluated": True,
            "accuracy": float(accuracy_score(y_test, pred)),
            "precision_weighted": float(precision),
            "recall_weighted": float(recall),
            "f1_weighted": float(f1),
            "labels": sorted(set(y_test) | set(pred)),
            "confusion_matrix": confusion_matrix(y_test, pred, labels=sorted(set(y_test) | set(pred))).tolist(),
            "classification_report": classification_report(y_test, pred, zero_division=0, output_dict=True),
            "test_rows": len(y_test),
        })
    except Exception as exc:
        report.update({"evaluated": False, "error": str(exc)})
    return report
