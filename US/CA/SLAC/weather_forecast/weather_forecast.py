"""Weather forecast gridlabd-python module

This gridlabd python template implements regional real-time weather forecasts.

    shell% gridlabd config.glm model.glm weather_forecast.glm

where the files contain the following

    config.glm              specifies the timeframe of the analysis using the `clock` directive, 
                            as well as any other needed settings
    model.glm               specifies the system model
    weather_forecast.glm    links and enables the weather forecast module

The weather forecast files may be downloaded from the GridLAB-D template library using the command

    shell% gridlabd template get weather_forecast

"""


#
# GridLAB-D event handlers
#
def on_init(t):
    """GridLAB-D initialization event handler

    Parameter:
        t (int): initial timestamp

    Return:
        bool: success (True) or failure (False)
    """

    # successfully initialized
    return True

def on_sync(t):
    """GridLAB-D synchronization event handler

    Parameter:
        t (int): target timestamp

    Return:
        int: timestamp of next desired sync event call
    """

    return gridlabd.NEVER

def on_term(t):
    """GridLAB-D on_term event handler

     Parameter:
        t (int): target timestamp   
    """
    return
