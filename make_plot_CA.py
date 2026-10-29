import csv
from functools import lru_cache
import pickle
import plotly.graph_objects as go
import os
import numpy as np
from pathlib import Path


DATASET_COLORS = {
    "hook": {"train": "#1f77b4", "val": "#9ecae1"},
    "jazz": {"train": "#d62728", "val": "#ff9896"},
    "nott": {"train": "#2ca02c", "val": "#98df8a"},
    "wiki": {"train": "#8c564b", "val": "#c49c94"},
}
SPLIT_MARKER_SYMBOLS = {"train": "circle", "val": "x"}


def _load_metrics_features():
    metrics_dir = Path("data/metricsCA")
    csv_paths = sorted(metrics_dir.glob("*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in {metrics_dir}")

    metadata = []
    feature_rows = []
    feature_names = None

    for csv_path in csv_paths:
        file_key = (
            csv_path.stem[:-3]
            if csv_path.stem.endswith("_df")
            else csv_path.stem
        )
        try:
            dataset, split = file_key.rsplit("_", 1)
        except ValueError as error:
            raise ValueError(f"Unexpected metrics CSV name: {csv_path.name}") from error
        if dataset not in DATASET_COLORS or split not in SPLIT_MARKER_SYMBOLS:
            raise ValueError(f"Unexpected metrics CSV name: {csv_path.name}")

        with csv_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or len(reader.fieldnames) < 9:
                raise ValueError(f"{csv_path} must contain at least nine columns")
            current_feature_names = reader.fieldnames[-9:]
            if "filepath" not in reader.fieldnames:
                raise ValueError(f"{csv_path} is missing the filepath column")
            if feature_names is None:
                feature_names = current_feature_names
            elif current_feature_names != feature_names:
                raise ValueError(
                    f"Feature columns in {csv_path} do not match the other CSV files"
                )

            for line_number, row in enumerate(reader, start=2):
                try:
                    values = [
                        float(row[column]) if row[column] and row[column].strip()
                        else np.nan
                        for column in current_feature_names
                    ]
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"Non-numeric feature value in {csv_path} at line {line_number}"
                    ) from error
                if not np.isfinite(values).all():
                    continue

                filepath = row["filepath"]
                if not filepath:
                    raise ValueError(
                        f"Missing filepath in {csv_path} at line {line_number}"
                    )
                feature_rows.append(values)
                metadata.append({
                    "dataset": dataset,
                    "split": split,
                    "piece": os.path.basename(filepath),
                })

    if len(feature_rows) < 2:
        raise ValueError("At least two rows with complete feature values are required")

    return metadata, np.asarray(feature_rows, dtype=float), feature_names


def make_interactive_pca_plot():
    metadata, features, _ = _load_metrics_features()
    feature_scales = features.std(axis=0)
    feature_scales[feature_scales == 0] = 1
    standardized_features = (features - features.mean(axis=0)) / feature_scales
    left_vectors, singular_values, _ = np.linalg.svd(
        standardized_features,
        full_matrices=False,
    )
    coordinates = left_vectors[:, :2] * singular_values[:2]
    total_variance = np.sum(singular_values ** 2)
    explained_variance = (
        singular_values[:2] ** 2 / total_variance * 100
        if total_variance
        else np.zeros(2)
    )

    fig = go.Figure()
    for dataset, split_colors in DATASET_COLORS.items():
        for split, color in split_colors.items():
            selected = [
                index
                for index, item in enumerate(metadata)
                if item["dataset"] == dataset and item["split"] == split
            ]
            fig.add_trace(go.Scattergl(
                x=coordinates[selected, 0],
                y=coordinates[selected, 1],
                mode="markers",
                name=f"{dataset.title()} {split}",
                customdata=[
                    [metadata[index]["dataset"], metadata[index]["piece"]]
                    for index in selected
                ],
                marker=dict(
                    color=color,
                    symbol=SPLIT_MARKER_SYMBOLS[split],
                    size=6,
                    opacity=0.7,
                ),
                hovertemplate=(
                    "Dataset: %{customdata[0]}<br>"
                    "Piece: %{customdata[1]}<br>"
                    "PC1: %{x:.3f}<br>"
                    "PC2: %{y:.3f}"
                    "<extra></extra>"
                ),
            ))

    fig.update_layout(
        title="PCA of piece features",
        xaxis_title=f"PC1 ({explained_variance[0]:.1f}% variance)",
        yaxis_title=f"PC2 ({explained_variance[1]:.1f}% variance)",
        hovermode="closest",
    )

    output_path = Path("html") / "metricsCA_pca.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    return output_path
# end make_interactive_pca_plot


def make_interactive_umap_plot():
    from umap import UMAP

    metadata, features, feature_names = _load_metrics_features()
    feature_scales = features.std(axis=0)
    feature_scales[feature_scales == 0] = 1
    standardized_features = (features - features.mean(axis=0)) / feature_scales
    coordinates = UMAP(
        n_components=2,
        n_neighbors=5,
        min_dist=0.01,
        metric="euclidean",
        random_state=42,
    ).fit_transform(standardized_features)
    feature_hover = ", ".join(
        f"{name}: %{{customdata[{index + 2}]:.3f}}"
        for index, name in enumerate(feature_names)
    )

    fig = go.Figure()
    for dataset, split_colors in DATASET_COLORS.items():
        for split, color in split_colors.items():
            selected = [
                index
                for index, item in enumerate(metadata)
                if item["dataset"] == dataset and item["split"] == split
            ]
            fig.add_trace(go.Scattergl(
                x=coordinates[selected, 0],
                y=coordinates[selected, 1],
                mode="markers",
                name=f"{dataset.title()} {split}",
                customdata=[
                    [
                        metadata[index]["dataset"],
                        metadata[index]["piece"],
                        *features[index],
                    ]
                    for index in selected
                ],
                marker=dict(
                    color=color,
                    symbol=SPLIT_MARKER_SYMBOLS[split],
                    size=6,
                    opacity=0.7,
                ),
                hovertemplate=(
                    "Dataset: %{customdata[0]}<br>"
                    "Piece: %{customdata[1]}<br>"
                    f"Features: {feature_hover}<extra></extra>"
                ),
            ))

    fig.update_layout(
        title="UMAP of piece features",
        xaxis_title="UMAP 1",
        yaxis_title="UMAP 2",
        hovermode="closest",
    )

    output_path = Path("html") / "metricsCA_umap.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    return output_path


if __name__ == "__main__":
    # make_interactive_pca_plot()
    make_interactive_umap_plot()