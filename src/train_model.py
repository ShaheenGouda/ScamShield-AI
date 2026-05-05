import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    roc_curve,
    confusion_matrix,
    f1_score
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.extract_features import extract_url_features


print("🚀 Starting ELITE Stacking Training Pipeline...")

# ✅ 1. Load dataset
df = pd.read_csv("data/urls/urls.csv")

df["Label"] = df["Label"].astype(str).str.lower()
df["Label"] = df["Label"].map({"bad": 1, "good": 0})

print("✅ Dataset Loaded:", df.shape)

# ✅ 2. Feature Engineering
print("🔎 Extracting Features...")
feature_list = df["URL"].apply(extract_url_features)

X = pd.DataFrame(feature_list.tolist())
y = df["Label"]

# ✅ 3. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("✅ Data Split Complete")

# ✅ 4. Base Models
rf = RandomForestClassifier(
    n_estimators=300,
    class_weight="balanced",
    random_state=42
)

gb = GradientBoostingClassifier(
    n_estimators=300,
    learning_rate=0.05,
    random_state=42
)

lr = Pipeline([
    ("scaler", StandardScaler()),
    ("model", LogisticRegression(max_iter=2000))
])

# ✅ 5. Stacking Ensemble
stack_model = StackingClassifier(
    estimators=[
        ("rf", rf),
        ("gb", gb),
        ("lr", lr)
    ],
    final_estimator=LogisticRegression(),
    cv=3,
    n_jobs=-1
)

print("🔎 Training Stacking Ensemble...")
stack_model.fit(X_train, y_train)

# ✅ 6. Cross-Validated AUC
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
cv_scores = cross_val_score(stack_model, X, y, cv=cv, scoring="roc_auc")

print(f"✅ Cross-Validated AUC: {cv_scores.mean():.4f}")

# ✅ 7. Test AUC
y_prob = stack_model.predict_proba(X_test)[:, 1]
test_auc = roc_auc_score(y_test, y_prob)

print(f"✅ Test ROC-AUC: {test_auc:.4f}")

# ✅ 8. Threshold Selection (Max F1)
precisions, recalls, thresholds = precision_recall_curve(y_test, y_prob)

best_threshold = 0.5
best_f1 = 0

for t in thresholds:
    y_pred_custom = (y_prob >= t).astype(int)
    f1 = f1_score(y_test, y_pred_custom)

    if f1 > best_f1:
        best_f1 = f1
        best_threshold = t

print(f"✅ Selected Threshold (Max F1): {best_threshold:.3f}")
print(f"✅ Best F1 Score: {best_f1:.3f}")

# ✅ 9. Final Predictions for Plots
y_pred_final = (y_prob >= best_threshold).astype(int)

# ✅ Confusion Matrix
cm = confusion_matrix(y_test, y_pred_final)

plt.figure(figsize=(6,5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.savefig("models/confusion_matrix.png")
plt.close()

print("✅ Confusion matrix saved.")

# ✅ ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_prob)

plt.figure()
plt.plot(fpr, tpr)
plt.plot([0,1], [0,1], linestyle="--")
plt.title("ROC Curve")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.tight_layout()
plt.savefig("models/roc_curve.png")
plt.close()

print("✅ ROC curve saved.")

# ✅ Precision-Recall Curve
precision, recall, _ = precision_recall_curve(y_test, y_prob)

plt.figure()
plt.plot(recall, precision)
plt.title("Precision-Recall Curve")
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.tight_layout()
plt.savefig("models/pr_curve.png")
plt.close()

print("✅ PR curve saved.")

# ✅ Feature Importance (from Random Forest inside stacking)
rf_model = stack_model.named_estimators_["rf"]
importances = rf_model.feature_importances_

importance_df = pd.DataFrame({
    "Feature": X.columns,
    "Importance": importances
}).sort_values(by="Importance", ascending=False)

print("\nTop 10 Important Features:")
print(importance_df.head(10))

plt.figure(figsize=(8,6))
plt.barh(
    importance_df.head(10)["Feature"][::-1],
    importance_df.head(10)["Importance"][::-1]
)
plt.title("Top 10 Feature Importances")
plt.xlabel("Importance")
plt.tight_layout()
plt.savefig("models/feature_importance.png")
plt.close()

print("✅ Feature importance plot saved.")

# ✅ 10. Save Model + Threshold
os.makedirs("models", exist_ok=True)
joblib.dump(stack_model, "models/scam_model.pkl")
joblib.dump(best_threshold, "models/decision_threshold.pkl")

print("✅ Model & Threshold Saved")
print("✅ Training Complete")