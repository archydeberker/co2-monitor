import dash
from dash.dependencies import Input, Output
import dash_table
import dash_html_components as html
import dash_core_components as dcc

import pandas as pd
import numpy as np


def assemble_co2_df():
    mauna_data = 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/weekly/weekly_in_situ_co2_mlo.csv'
    alert_data = 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/flask_co2/daily/daily_flask_co2_alt.csv'
    south_pole_data = 'http://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/merged_in_situ_and_flask/daily/daily_merge_co2_spo.csv'

    df_manua = pd.read_csv(mauna_data, skiprows=44, names=['date', 'CO2 in ppm'], parse_dates=['date'])
    df_manua['location'] = 'Manua Loa'

    df_alert = pd.read_csv(alert_data, skiprows=69, usecols=[0, 6], names=['date', 'CO2 in ppm'], parse_dates=['date'])
    df_alert['location'] = 'Alert'
    df_alert.tail()

    df_south_pole = pd.read_csv(south_pole_data, skiprows=71, usecols=[0, 6], names=['date', 'CO2 in ppm'],
                                parse_dates=['date'])
    df_south_pole['location'] = 'South Pole'

    combined_df = pd.concat((df_manua, df_south_pole, df_alert))

    combined_df['CO2 in ppm'] = combined_df['CO2 in ppm'].astype(np.float64)

    combined_df['year'] = combined_df.date.apply(lambda x: x.year)
    combined_df['day'] = combined_df.date.apply(lambda x: x.day)
    combined_df['month'] = combined_df.date.apply(lambda x: x.month)

    return combined_df


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = assemble_co2_df()

df_reduced = df[['year', 'month', 'day', 'CO2 in ppm', 'location']]

app.layout = html.Div([html.Div(className='row',
                                children=[html.Div(className='six columns',
                                                   children=
                                                   dash_table.DataTable(
                                                       id='datatable-filtering-be',
                                                       columns=[
                                                           {"name": i, "id": i, "deletable": True} for i in df_reduced.columns
                                                       ],
                                                       data=df_reduced.to_dict("rows"),
                                                       filtering='be',
                                                       style_table={
                                                           'maxHeight': '300',
                                                           'overflowY': 'scroll'
                                                       }
                                                   )),
                                          html.Div(id='datatable-year-container',
                                                   className='six columns')]
                                ),
                       html.Div(html.Div(id='datatable-filter-container',
                                         className='twelve columns'),
                                className='row')])



@app.callback(
    [Output('datatable-filter-container', "children"),
     Output('datatable-year-container', "children")],
    [Input('datatable-filtering-be', "filtering_settings")])
def update_year_graph(filtering_settings):
    # When the table is first rendered, `derived_virtual_data` and
    # `derived_virtual_selected_rows` will be `None`. This is due to an
    # idiosyncracy in Dash (unsupplied properties are always None and Dash
    # calls the dependent callbacks when the component is first rendered).
    # So, if `rows` is `None`, then the component was just rendered
    # and its value will be the same as the component's dataframe.
    # Instead of setting `None` in here, you could also set
    # `derived_virtual_data=df.to_rows('dict')` when you initialize
    # the component.
    print(filtering_settings)
    dff = df.copy()

    try:
        filtering_expressions = filtering_settings.split(' && ')
        for filter in filtering_expressions:
            if ' eq ' in filter:
                col_name = filter.split(' eq ')[0].strip('\"')
                filter_value = filter.split(' eq ')[1]
                dff = dff.loc[dff[col_name] == filter_value]
            if ' > ' in filter:
                col_name = filter.split(' > ')[0].strip('\"')
                filter_value = float(filter.split(' > ')[1])
                dff = dff.loc[dff[col_name] > filter_value]
            if ' < ' in filter:
                col_name = filter.split(' < ')[0].strip('\"')
                filter_value = float(filter.split(' < ')[1])
                dff = dff.loc[dff[col_name] < filter_value]
    except:
        pass
    print(dff.location.unique())

    return [html.Div(
        dcc.Graph(
            id='ppm',
            figure={
                "data": [
                    {
                        "x": dff.loc[dff['location'] == location, "date"],
                        # check if column exists - user may have deleted it
                        # If `column.deletable=False`, then you don't
                        # need to do this check.
                        "y": dff.loc[dff['location'] == location, 'CO2 in ppm'],
                        "type": "line",
                        "name": location,
                    }
                    for location in dff.location.unique()],
                "layout": {
                    "xaxis": {"automargin": True},
                    "yaxis": {"automargin": True},
                    "height": 350,
                    "margin": {"t": 30, "l": 10, "r": 10, "b": 0},
                    "title": "All data for selected period",
                },
            },
        )

    ),
        html.Div(
            dcc.Graph(
                id='ppm2',
                figure={
                    "data": [
                        {
                            "x": dff.loc[dff['location'] == location].groupby('month').mean().index,
                            # check if column exists - user may have deleted it
                            # If `column.deletable=False`, then you don't
                            # need to do this check.
                            "y": dff.loc[dff['location'] == location].groupby('month').mean()['CO2 in ppm'],
                            "type": "line",
                            "name": location,
                        }
                        for location in dff.location.unique()],
                    "layout": {
                        "xaxis": {"automargin": True},
                        "yaxis": {"automargin": True},
                        "height": 250,
                        "margin": {"t": 100, "l": 10, "r": 10, "b": 0},
                        "title": "Monthly average for selected range",

                    },
                },
            )

        )]


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
