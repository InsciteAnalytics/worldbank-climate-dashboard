# Starting from base miniconda image
FROM continuumio/miniconda3

# Setting vanilla WORKDIR in destination
WORKDIR /app

# This is the complete set of libraries required
RUN conda install -c pyviz holoviz
RUN conda install -c pyviz geoviews-core
RUN conda install geopandas

# Copy the relevant folder into the container 
COPY ./dep-test/ .
# Note: the above copies all the contents (not the folder itself) of dep-test into app folder of container

# Run panel serve to start the app
CMD panel serve --address="0.0.0.0" --port=$PORT main.py --allow-websocket-origin=worldbank-climate-dashboard.herokuapp.com