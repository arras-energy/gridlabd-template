import pandas as pd
import datetime

metered_energy = {}
pole_status = {}
objs = {}
wrn_count = 0

def get_info(t, object_class, target_property) : 
    for obj in objs:
        if gridlabd.get_object(obj)['class'] == object_class:
            if t not in data:
                data[t] = {}
            data[t][obj] = gridlabd.get_object(obj)[target_property]
    return data

def dump_csv(data,file_name ) : 
    # Flatten the nested dictionary
    flat_data = []

    for timestamp, item in data.items():
        row = {'timestamp': datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}
        row.update(item)
        flat_data.append(row)

    # Create a DataFrame
    df = pd.DataFrame(flat_data).set_index('timestamp')
    df.to_csv(file_name, index=True)
    return df

def on_init(t) : 
    global objs 
    objs = gridlabd.get('objects')
    return True

def on_commit(t) :
    global pole_status, metered_energy, wrn_count
    pole_status.update(get_info(t,'pole', 'status'))
    # pole_status.update(get_info(t,'pole', 'total_moment'))
    try : 
        metered_energy.update(get_info(t,'meter','measured_real_energy'))
    finally : 
        if wrn_count == 0 : 
            print(f"WARNING [status_log]: meters are not available in the model.")
            wrn_count = 1
    return True 

def on_term(t) : 
    global pole_status, metered_energy

    df_energy = dump_csv(pole_status,'/tmp/output/pole_status.csv')
    dump_csv(metered_energy, '/tmp/output/metered_energy.csv')
    return None