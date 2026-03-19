#!/bin/bash
# MobMetrics install script - run this to get everything ready
# Tested on Ubuntu 22.04 / macOS Ventura
# ~5min, needs internet + 2GB disk

set -e  # stop on error

echo "Setting up MobMetrics..."

# helper functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
ok() { green "✓ $1"; }

# check basics
curl -V >/dev/null 2>&1 || { red "Need curl"; exit 1; }
tar -v >/dev/null 2>&1 || { red "Need tar"; exit 1; }

# conda (skip if exists)
if ! command -v conda >/dev/null 2>&1; then
    echo "Getting Miniconda..."
    curl -L "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" -o /tmp/mini.sh
    bash /tmp/mini.sh -b -p $HOME/miniconda3
    rm /tmp/mini.sh
    eval "$HOME/miniconda3/bin/conda shell.bash hook"
    ok "conda ready"
else
    eval "$(conda shell.bash hook 2>/dev/null)"
fi

# env
conda env create -f environment.yml -n MobMetrics || conda env update -f environment.yml -n MobMetrics
conda activate MobMetrics

# jdk for bonnmotion
if ! java -version >/dev/null 2>&1; then
    echo "JDK..."
    conda install -y -c conda-forge openjdk=17
fi

# bonnmotion (only if missing)
if [ ! -x "bonnmotion-3.0.1/bin/bm" ]; then
    echo "BonnMotion..."
    curl -L "https://bonnmotion.sys.cs.uos.de/src/bonnmotion-3.0.1.zip" -o /tmp/bm.zip
    unzip -o /tmp/bm.zip
    rm /tmp/bm.zip
    cd bonnmotion-3.0.1
    ./install
    cd ..
    chmod +x bonnmotion-3.0.1/bin/bm
    ok "BonnMotion at ./bonnmotion-3.0.1/bin/bm"
fi

# django
cd MobMetrics
python manage.py makemigrations metrics
python manage.py migrate
python manage.py collectstatic --noinput
cd ..

echo ""
ok "Done!"
echo "conda activate MobMetrics"
echo "cd MobMetrics && python manage.py runserver"
echo "http://localhost:8000"
