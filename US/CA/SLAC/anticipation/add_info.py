import pandas as pd
csv_input = pd.read_csv('path_vege.csv')
wind_speed = 10
width = 5
csv_input['wind_speed'] = wind_speed
csv_input['width'] = width
csv_input.to_csv('path_vege.csv', index=False)