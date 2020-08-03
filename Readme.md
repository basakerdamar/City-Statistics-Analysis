## City Statistics Analysis

This repository includes first aggregations and visualisations of various video detection algoritm outputs. These aggregations and plots are then implemented into an interactive dashboard made with Dash library.

app.py includes the dashboard for interactive visualizations of the final results. For the data preparation and analysis, refer to the notebooks.

### Dashboard
To set-up

```
docker build -t dashboard .
```

To run 

```
docker run -p 8080:8080 dashboard 
```
