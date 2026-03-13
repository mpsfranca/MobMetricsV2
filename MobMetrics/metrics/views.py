from io import BytesIO
import os
import shutil
import zipfile
import json
import subprocess
from typing import Any

import pandas as pd
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.conf import settings
import skmob

from .forms import (
    UploadForm,
    FileNameForm,
    DataAnalytcsParamsForm,
    ModelSelectForm,
    BonnmotionMobmetricsForm,
    BonnmotionScenarioForm,
    BonnmotionRandomSpeedBaseForm,
    ModelSpecificParametersForm,
)
from .utils.csv_converter import convert
from .process.factory import Factory
from .process.DataAnalytcs.pca import PCA
from .process.DataAnalytcs.tSNE import tSNE
from .process.DataAnalytcs.clustering.DBscan import DBscan
from .visualizations.comparative.pca_plots import (
    generate_pca_plot_html,
    generate_explained_variance_plot_html,
    generate_dbscan_pca_plot_html,
)
from .visualizations.comparative.tsne_plots import (
    generate_tsne_plot_html,
    generate_dbscan_tsne_plot_html,
)
from .visualizations.trace.trace_plot import (
    plot_trace_entities,
    plot_trace_in_time,
    plot_stay_points,
)
from .visualizations.metrics.global_metrics import (
    plot_radar_chart,
    plot_travel_distance_comparison,
    plot_metric_histogram,
    plot_metric_boxplot,
)
from .models import (
    ConfigModel,
    MetricsModel,
    JourneyModel,
    StayPointModel,
    VisitModel,
    ContactModel,
    QuadrantEntropyModel,
    GlobalMetricsModel,
    TraceModel,
)


def dashboard_view(request):
    """Handles the main dashboard page, including uploads, analysis, and visualization."""
    file_names = ConfigModel.objects.values_list("file_name", flat=True).distinct()

    pca_metrics_plot_html = ""
    pca_explained_plot_html = ""
    pca_dbscan_metrics_plot_html = ""
    tsne_metrics_plot_html = ""
    tsne_dbscan_metrics_plot_html = ""
    pca_global_plot_html = ""
    tsne_global_plot_html = ""

    upload_form = UploadForm()
    file_form = FileNameForm()
    select_form = ModelSelectForm()
    bm_mobmetrics_form = BonnmotionMobmetricsForm()
    bm_scenario_form = BonnmotionScenarioForm()
    bm_randomspeedbase_form = BonnmotionRandomSpeedBaseForm()
    model_specific_parameters_form = ModelSpecificParametersForm()
    analytcs_form = DataAnalytcsParamsForm()

    if request.method == "POST":
        if "upload" in request.POST:
            file_names = _handle_upload(request)
        elif "delete" in request.POST:
            file_names = _handle_delete(request)
        elif "download" in request.POST:
            return _handle_download(request)
        elif "generate_graphs" in request.POST:
            (
                pca_metrics_plot_html,
                pca_explained_plot_html,
                pca_dbscan_metrics_plot_html,
                tsne_metrics_plot_html,
                tsne_dbscan_metrics_plot_html,
                pca_global_plot_html,
                tsne_global_plot_html,
            ) = _handle_generate_graphs(request)
        elif "create" in request.POST:
            _handle_bonnmotion(request)

    last_config = ConfigModel.objects.last()

    uid = request.GET.get("uid")
    stay_point_id = request.GET.get("stay_point_id")
    trace_in_time_html = None

    if last_config:
        file_name = last_config.file_name
        metrics = MetricsModel.objects.filter(file_name=file_name).order_by("uid")
        global_metrics = GlobalMetricsModel.objects.filter(file_name=file_name).first()
        staypoints = StayPointModel.objects.filter(file_name=file_name).order_by("stay_point_id")
        trace_plot_html = plot_trace_entities(file_name=file_name, max_points=5000)
        radar_chart_html = plot_radar_chart(file_name=file_name)
        stay_points_html = plot_stay_points(file_name=file_name)

        if uid is not None:
            try:
                uid = int(uid)
                trace_in_time_html = plot_trace_in_time(file_name=file_name, uid=uid)
                travel_distance_compare_plot_html = plot_travel_distance_comparison(file_name=file_name, uid=uid)
                metric_histogram_html = plot_metric_histogram(file_name=file_name)
                metric_boxplot_html = plot_metric_boxplot(file_name=file_name)
            except ValueError:
                trace_in_time_html = plot_trace_in_time(file_name=file_name)
        else:
            trace_in_time_html = plot_trace_in_time(file_name=file_name)
            travel_distance_compare_plot_html = plot_travel_distance_comparison(file_name=file_name, uid=0)
            metric_histogram_html = plot_metric_histogram(file_name=file_name)
            metric_boxplot_html = plot_metric_boxplot(file_name=file_name)

        if stay_point_id is not None:
            try:
                stay_point_id = int(stay_point_id)
                stay_points_html = plot_stay_points(file_name=file_name, highlight_spId=stay_point_id)
            except ValueError:
                stay_points_html = plot_stay_points(file_name=file_name)
        else:
            stay_points_html = plot_stay_points(file_name=file_name)
    else:
        metrics = None
        global_metrics = None
        staypoints = None
        trace_plot_html = None
        radar_chart_html = None
        travel_distance_compare_plot_html = None
        metric_histogram_html = None
        metric_boxplot_html = None
        stay_points_html = None

    return render(request, "base.html", {
        "upload_form": upload_form,
        "file_form": file_form,
        "select_form": select_form,
        "bm_mobmetrics_form": bm_mobmetrics_form,
        "bm_scenario_form": bm_scenario_form,
        "bm_randomspeedbase_form": bm_randomspeedbase_form,
        "model_specific_parameters_form": model_specific_parameters_form,
        "analytcs_form": analytcs_form,
        "file_names": file_names,
        "metrics": metrics,
        "staypoints": staypoints,
        "global_metrics": global_metrics,
        "last_file_name": last_config.file_name if last_config else None,
        "trace_plot_html": trace_plot_html,
        "radar_chart_html": radar_chart_html,
        "trace_in_time_html": trace_in_time_html,
        "travel_distance_compare_plot": travel_distance_compare_plot_html,
        "metric_histogram": metric_histogram_html,
        "metric_boxplot": metric_boxplot_html,
        "stay_point_scatter_plot": stay_points_html,
        "pca_metrics_plot_html": pca_metrics_plot_html,
        "pca_explained_plot_html": pca_explained_plot_html,
        "pca_dbscan_metrics_plot_html": pca_dbscan_metrics_plot_html,
        "tsne_metrics_plot_html": tsne_metrics_plot_html,
        "tsne_dbscan_metrics_plot_html": tsne_dbscan_metrics_plot_html,
        "pca_global_plot_html": pca_global_plot_html,
        "tsne_global_plot_html": tsne_global_plot_html,
    })


def _handle_upload(request):
    """Validates an uploaded trace file, stores its data, and triggers metric extraction."""
    upload_form = UploadForm(request.POST, request.FILES)

    if not upload_form.is_valid():
        messages.error(request, "Invalid form data.")
        return ConfigModel.objects.values_list("file_name", flat=True).distinct()

    data = _get_data(upload_form)
    file_name = data["name"]

    if ConfigModel.objects.filter(file_name=file_name).exists():
        messages.warning(request, "A file with the same name already exists.")
        return ConfigModel.objects.values_list("file_name", flat=True).distinct()

    try:
        df = _create_data_frame(data)
        _create_config_model(data)
        _create_trace_model(df, file_name)
        Factory.extract(data, df)
        messages.success(request, "Upload and processing completed.")
    except Exception:
        messages.error(request, "Upload failed during processing.")
        return ConfigModel.objects.values_list("file_name", flat=True).distinct()


def _create_data_frame(data):
    """Builds the trajectory dataframe from the uploaded file."""
    for k in data.keys():
        print(f"----- {k} : {data[k]} -----")

    aux_df = pd.read_csv(data["file"])
    aux_df["time"] = pd.to_datetime(aux_df["time"], unit="s", utc=True)

    df = skmob.TrajDataFrame(
        aux_df,
        user_id="id",
        latitude="y",
        longitude="x",
        datetime="time",
    )

    df.insert(
        df.columns.get_loc("lat") + 1,
        "alt",
        aux_df["z"] if "z" in aux_df.columns else 0.0,
    )

    return df


def _handle_delete(request):
    """Deletes all persisted data associated with a selected file."""
    file_name = request.POST.get("fileName")
    models_list = [
        ConfigModel,
        MetricsModel,
        JourneyModel,
        StayPointModel,
        VisitModel,
        ContactModel,
        QuadrantEntropyModel,
        GlobalMetricsModel,
        TraceModel,
    ]

    if file_name:
        for model in models_list:
            model.objects.filter(file_name=file_name).delete()
        messages.success(request, f"Data for '{file_name}' deleted.")
    else:
        messages.error(request, "No file name provided.")

    file_names = ConfigModel.objects.values_list("file_name", flat=True).distinct()
    return file_names


def _handle_download(request):
    """Exports all stored data for a selected file as a ZIP archive."""
    file_name = request.POST.get("name")

    if file_name:
        zip_buffer = BytesIO()

        models = {
            "ConfigModel": ConfigModel.objects.filter(file_name=file_name),
            "MetricsModel": MetricsModel.objects.filter(file_name=file_name),
            "JurnayModel": JourneyModel.objects.filter(file_name=file_name),
            "StayPointModel": StayPointModel.objects.filter(file_name=file_name),
            "VisitModel": VisitModel.objects.filter(file_name=file_name),
            "ContactModel": ContactModel.objects.filter(file_name=file_name),
            "QuadrantEntropyModel": QuadrantEntropyModel.objects.filter(file_name=file_name),
            "GlobalMetricsModel": GlobalMetricsModel.objects.filter(file_name=file_name),
        }

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for model_name, queryset in models.items():
                if queryset.exists():
                    df = pd.DataFrame.from_records(queryset.values())
                    csv_buffer = BytesIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    zip_file.writestr(f"{model_name}.csv", csv_buffer.read())

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type="application/zip")
        response["Content-Disposition"] = f"attachment; filename={file_name}.zip"
        return response

    messages.error(request, "No file name provided.")
    return HttpResponse("File name not provided", status=400)


def _handle_generate_graphs(request):
    """Generates comparative analytics plots from stored metrics."""
    analytics_form = DataAnalytcsParamsForm(request.POST, request.FILES)

    pca_metrics_plot_html = ""
    pca_explained_plot_html = ""
    pca_dbscan_metrics_plot_html = ""
    tsne_metrics_plot_html = ""
    tsne_dbscan_metrics_plot_html = ""
    pca_global_plot_html = ""
    tsne_global_plot_html = ""

    if analytics_form.is_valid():
        pca_n_components = int(request.POST.get("PCA_n_components"))
        tsne_n_components = int(request.POST.get("tSNE_n_components"))
        tsne_perplexity = float(request.POST.get("tSNE_perplexity"))
        dbscan_eps = float(request.POST.get("dbscan_eps"))
        dbscan_min_samples = int(request.POST.get("dbscan_min_samples"))

        dbscan_parameters = (dbscan_eps, dbscan_min_samples)

        metrics_df = pd.DataFrame.from_records(MetricsModel.objects.all().values())
        global_metrics_df = pd.DataFrame.from_records(GlobalMetricsModel.objects.all().values())

        columns_metrics, columns_global = _columns_analytics(metrics_df, global_metrics_df)

        pca_metrics_results = PCA(
            pca_n_components,
            metrics_df.copy(),
            columns_metrics,
            dbscan_parameters,
        ).extract()
        pca_global_metrics_results = PCA(
            pca_n_components,
            global_metrics_df.copy(),
            columns_global,
            dbscan_parameters,
        ).extract()

        tsne_metrics_results = tSNE(
            tsne_n_components,
            tsne_perplexity,
            metrics_df.copy(),
            columns_metrics,
            dbscan_parameters,
        ).extract()
        tsne_global_metrics_results = tSNE(
            tsne_n_components,
            tsne_perplexity,
            global_metrics_df.copy(),
            columns_global,
            dbscan_parameters,
        ).extract()

        pca_metrics_plot_html = generate_pca_plot_html(
            data_frame=json.loads(pca_metrics_results["pca_json"]),
            contributors=pca_metrics_results["top_contributors"],
            n_components=pca_metrics_results["n_components"],
            title="PCA - MetricsModel",
            color_by="label",
        )

        pca_explained_plot_html = generate_explained_variance_plot_html(
            explained_variance_ratio=pca_metrics_results["explained_variance"],
            title="Explained Variance Components",
        )

        pca_dbscan_metrics_plot_html = generate_dbscan_pca_plot_html(
            data_frame=json.loads(pca_metrics_results["pca_json"]),
            contributors=pca_metrics_results["top_contributors"],
            n_components=pca_metrics_results["n_components"],
            title="DBSCAN - PCA MetricsModel",
            color_by="dbscan_cluster",
        )

        tsne_metrics_plot_html = generate_tsne_plot_html(
            data_frame=json.loads(tsne_metrics_results["components"]),
            tsne_components=[f"TSNE{i+1}" for i in range(tsne_n_components)],
            n_components=tsne_n_components,
            title="t-SNE - MetricsModel",
            color_by="label",
        )

        tsne_dbscan_metrics_plot_html = generate_dbscan_tsne_plot_html(
            data_frame=json.loads(tsne_metrics_results["components"]),
            tsne_components=[f"TSNE{i+1}" for i in range(tsne_n_components)],
            n_components=tsne_n_components,
            title="DBSCAN - tSNE MetricsModel",
            color_by="dbscan_cluster",
        )

        pca_global_plot_html = generate_pca_plot_html(
            data_frame=json.loads(pca_global_metrics_results["pca_json"]),
            contributors=pca_global_metrics_results["top_contributors"],
            n_components=pca_global_metrics_results["n_components"],
            title="PCA - GlobalMetricsModel",
            color_by="label",
        )

        tsne_global_plot_html = generate_tsne_plot_html(
            data_frame=json.loads(tsne_global_metrics_results["components"]),
            tsne_components=[f"TSNE{i+1}" for i in range(tsne_n_components)],
            n_components=tsne_n_components,
            title="t-SNE - GlobalMetricsModel",
            color_by="label",
        )

    return (
        pca_metrics_plot_html,
        pca_explained_plot_html,
        pca_dbscan_metrics_plot_html,
        tsne_metrics_plot_html,
        tsne_dbscan_metrics_plot_html,
        pca_global_plot_html,
        tsne_global_plot_html,
    )


def _columns_analytics(metrics_df, global_metrics_df):
    """Returns the metric columns used in comparative analytics."""
    exclude_columns_metrics = ["id", "file_name", "label", "uid", "lng_center", "lat_center", "alt_center"]
    exclude_columns_global = ["id", "file_name", "label", "uid", "avgX_center", "avgY_center", "avgZ_center"]

    columns_metrics = [col for col in metrics_df.columns if col not in exclude_columns_metrics]
    columns_global = [col for col in global_metrics_df.columns if col not in exclude_columns_global]

    return columns_metrics, columns_global


def _get_data(form: UploadForm) -> dict[str, Any]:
    """Extracts normalized input data from a validated upload form."""
    data = form.cleaned_data

    return {
        "file": data["trace"],
        "distance_threshold": data["distance_threshold"],
        "radius_threshold": data["radius_threshold"],
        "is_geo_coord": data["is_geo_coord"],
        "time_threshold": data["time_threshold"],
        "quadrant_parts": data["quadrant_parts"],
        "name": data["name"],
        "label": data["label"],
        "contact_time_threshold": data["contact_time_threshold"],
        "skip_contact_detection": data["skip_contact_detection"],
    }


def _create_config_model(data):
    """Creates and stores the configuration record for a processed file."""
    required = {
        "name",
        "label",
        "is_geo_coord",
        "distance_threshold",
        "time_threshold",
        "radius_threshold",
        "quadrant_parts",
    }

    missing = required - data.keys()
    if missing:
        raise KeyError(f"Missing keys for ConfigModel: {sorted(missing)}")

    return ConfigModel.objects.create(
        file_name=data["name"],
        label=data["label"],
        is_geo_coord=data["is_geo_coord"],
        distance_threshold=data["distance_threshold"],
        time_threshold=data["time_threshold"],
        radius_threshold=data["radius_threshold"],
        quadrant_parts=data["quadrant_parts"],
    )


def _create_trace_model(df, name):
    """Persists trace points in batches for efficient database insertion."""
    batch_size = 25000

    required_columns = {"uid", "lng", "lat", "datetime"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"DataFrame must contain columns: {required_columns}")

    with transaction.atomic():
        batch = []

        for row in df.itertuples(index=False):
            batch.append(TraceModel(
                file_name=name,
                uid=row.uid,
                lat=row.lat,
                lng=row.lng,
                alt=row.alt,
                datetime=row.datetime,
            ))

            if len(batch) >= batch_size:
                TraceModel.objects.bulk_create(batch, batch_size=batch_size)
                batch.clear()

        if batch:
            TraceModel.objects.bulk_create(batch, batch_size=batch_size)


def _handle_bonnmotion(request):
    """Generates a BonnMotion scenario, converts it, and processes its metrics."""
    mobmetrics_form = BonnmotionMobmetricsForm(request.POST)

    if not mobmetrics_form.is_valid():
        messages.error(request, "Invalid form data.")
        return

    data = request.POST
    scenario_name = data.get("scenario_name")
    model = data.get("model")
    random_seed = data.get("random_seed")
    area_depth = data.get("area_depth")
    use_circular_shape = data.get("use_circular_shape")
    attraction_points = data.get("attraction_points")
    dimension_select = data.get("dimension_select")
    max_speed = data.get("max_speed")
    min_speed = data.get("min_speed")
    max_pause_time = data.get("max_pause_time")

    args = [
        "-f", scenario_name,
        model,
        "-n", data.get("nodes"),
        "-d", data.get("scenario_duration"),
        "-x", data.get("area_width"),
        "-y", data.get("area_height"),
        "-i", data.get("skip_time"),
    ]

    if attraction_points:
        args += ["-a", attraction_points]
    if use_circular_shape:
        args += ["-c"]
    if random_seed:
        args += ["-R", random_seed]
    if area_depth:
        args += ["-z", area_depth]
    if dimension_select:
        args += ["-J", dimension_select]
    if max_speed:
        args += ["-h", max_speed]
    if min_speed:
        args += ["-l", min_speed]
    if max_pause_time:
        args += ["-p", max_pause_time]

    args += [p for p in data.get('parameters').split(' ') if p]

    subprocess.run([settings.BONNMOTION_DIR, *args])
    subprocess.run([settings.BONNMOTION_DIR, "CSVFile", "-f", scenario_name])

    convert(scenario_name)

    with open(f"{scenario_name}.csv", "r") as csv_file:

        output_path = f"{settings.AUX_PATH}/generated_scenarios/{model}/{scenario_name}"
        os.makedirs(output_path, exist_ok=True)
        [
            shutil.move(f, f"{output_path}/{f}")
            for f in [
                f"{scenario_name}.params",
                f"{scenario_name}.movements.gz",
                f"{scenario_name}.csv",
            ]
        ]

        form_data = mobmetrics_form.cleaned_data

        parameters = {
            "file": csv_file,
            "distance_threshold": form_data["distance_threshold"],
            "radius_threshold": form_data["radius_threshold"],
            "is_geo_coord": form_data["geo_coord"],
            "time_threshold": form_data["time_threshold"],
            "quadrant_parts": form_data["quadrant_divisions"],
            "name": scenario_name,
            "label": f"{model}_{scenario_name}",
            "contact_time_threshold": form_data["contact_time_threshold"],
            "skip_contact_detection": form_data.get("skip_contact_detection", False),
        }

        df = _create_data_frame(parameters)
        _create_config_model(parameters)
        _create_trace_model(df, parameters["name"])

        Factory.extract(parameters, df)
