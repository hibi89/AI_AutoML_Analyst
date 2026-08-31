from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC


CLASSIFICATION_MODELS = {
    "logistic_regression": LogisticRegression(
        max_iter=1000,
    ),
    "random_forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    ),
    "extra_trees": ExtraTreesClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    ),
    "hist_gradient_boosting": HistGradientBoostingClassifier(
        random_state=42,
    ),
    "svm": SVC(
        probability=True,
        random_state=42,
    ),
}


def get_classification_models() -> dict:
    return CLASSIFICATION_MODELS.copy()