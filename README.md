# ProcessActivitySensor
Application detection sensor within active system processes. This is done with the goal of monitoring the use of productive desktop applications and awarding points for a determined usage time, associating them with the player's bGames profile.

## Prerequisites
* ### **Python**
    Python `3.12` or higher
* ### **bGames account**
    It is necessary to have a bGames profile, as if the user does not exist, they will not have a profile to save points.
* ### **Middleware**
    To use the browser, it is necessary to obtain the list of productive desk apps from an external server once the sensor is started. This approach allows new apps to be added over time without directly modifying the code. The current list of productive apps is obtained from an endpoint available in the following repository:  [Middleware](https://github.com/clmunozm/Middleware-bGames)

## Run with Python
To run the sensor, use the following command in the console within the file directory:
```shell
python processCapture.py
```
