# MobMetricsV2

MobMetrics is a web-based tool for computing, storing, and visualizing a comprehensive set of mobility metrics from spatiotemporal traces. It supports uploading real-world trajectory data (CSV/GeoJSON) or generating synthetic traces using BonnMotion mobility models, making it ideal for researchers in mobile computing and networking.

The tool was presented at SBRC 2025 as "MobMetrics: A Modular Architecture for Computing and Visualizing Mobility Metrics", and now we expand upon it by adding the possibility to use BonnMotion in the same workflow.

## Features

- **Trace Processing**: Detects stay points, journeys, visits, and contacts using configurable thresholds (distance, time, radius).
- **Kinematic Metrics**: Average speeds, speed variation coefficients, travel distances, and direction changes.
- **Spatial Metrics**: Radius of gyration, spatial coverage, quadrant entropy, stay point entropy.
- **Social Metrics**: Contact detection, total/average contact times, number of contacts.
- **Visualizations**: Interactive plots including trace scatters, radar charts, PCA/t-SNE reductions, DBSCAN clustering, histograms, and entity comparisons.
- **Synthetic Data**: Supports 20 BonnMotion models (e.g., Random Waypoint, Gauss-Markov, RPGM) with built-in workflow.
- **Dimensionality Reduction**: PCA, t-SNE with DBSCAN clustering for metric analysis.

## Installation

1. Install [Python](https://www.python.org/downloads/).

2. Install [Git](https://git-scm.com/install/)

3. Clone the repository:
```
git clone https://github.com/mpsfranca/MobMetrics-SBRC-2026.git
```
4. Navigate to the project folder:
```
cd MobMetrics-SBRC-2026
```
5. Run the install script:
```
chmod +x install.sh && ./install.sh
```
6. Activate the virtual environment:
```
conda activate MobMetrics
```
7. Start the server:
```
python MobMetrics/manage.py runserver
```
8. Access at `http://localhost:8000`


**Note**: What the `install.sh` does automatically:
 - Installs Miniconda (if missing)
 - Creates the `MobMetrics` environment from `environment.yml`
 - Installs OpenJDK
 - Downloads and compiles **BonnMotion v3.0.1**
 - Runs Django migrations

## Usage

1. **Upload Trace**: Provide CSV with columns `time|x|y|z(opt)|id`. Set thresholds and run processing.
2. **View Results**: Switch to "Results" tab for plots and tables (stay points, journeys, metrics).
3. **Generate Synthetic**: Use "Generate Data" tab, select model (e.g., RandomWaypoint), configure parameters.
4. **Manage Files**: Download/delete processed traces from "Manage Files".
5. **Analytics**: Generate PCA/t-SNE plots under dashboard.

Example input CSV:

time,x,y,id  
0.0,58.36951,7.859572,1.0  
1.0,58.369566,7.859756,1.0  
2.0,58.369623,7.85994,1.0  
3.0,58.36968,7.860124,1.0


## Architecture

- **Django Backend**: Models for traces, metrics, stay points, etc. Views handle upload/processing/visualization.
- **skmob Integration**: Uses **skmob's TrajDataFrame** for standardized trajectory data handling and manipulation.
- **Metrics Pipeline**: Modular `AbsMetric` classes for extensibility (kinematic, social, spatial).
- **Frontend**: Bootstrap + Plotly for interactive dashboards and tooltips.
- **Data Analytics**: scikit-learn for PCA/t-SNE/DBSCAN.

## BonnMotion Models
### Supported:
- Boundless • Chain • Column • DisasterArea • GaussMarkov
- ManhattanGrid • Nomadic • OriginalGaussMarkov • ProbRandomWalk • Pursue
- RandomDirection • RandomWalk • RandomWaypoint • RPGM • SLAW
- SMOOTH • Static • SteadyStateRandomWaypoint • SWIM • TLW


### Not Supported:
- MSLAW • RandomStreet • TIMM • StaticDrift
