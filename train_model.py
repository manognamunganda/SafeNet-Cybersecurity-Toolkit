import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load dataset
data = pd.read_csv("dataset.csv", engine="python")


# -------- CLEANING (CRITICAL) --------
data = data.dropna()  # remove NaN rows

# Convert labels to numeric (force)
data["label"] = pd.to_numeric(data["label"], errors="coerce")

# Drop rows where label conversion failed
data = data.dropna(subset=["label"])

# Ensure correct type
data["label"] = data["label"].astype(int)

# ------------------------------------

X = data["query"]
y = data["label"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Vectorization
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    stop_words="english",
    max_features=5000
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Model
model = MultinomialNB()
model.fit(X_train_vec, y_train)

# Evaluation
y_pred = model.predict(X_test_vec)
accuracy = accuracy_score(y_test, y_pred)

print("Dataset size:", len(data))
print("Model Accuracy:", round(accuracy * 100, 2), "%")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, zero_division=0))

# Save model
joblib.dump(model, "waf_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("\nTraining completed. Model and vectorizer saved.")

# Save accuracy to a file
with open("model_accuracy.txt", "w") as f:
    f.write(str(round(accuracy * 100, 2)))
