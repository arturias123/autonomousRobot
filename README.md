# Rewarding the Autonomous Robot
This project simulates our path-planning for an autonomous robot that tries to find a way to reach a goal (target)
in certainly environment differently each time it runs.
Firstly, the 'table' variable in 'Robot_main.py' should be set as 'False', because there is currently no data in the reward table. We chose to save only the inefficient points. In future development, developers should also save the route of each run in order to easily make comparisions.
##### Usage:
``` python Robot_main.py -n <number of run times> -m <map name> -w <worldname> -r vision_range -sx <x> -sy <y> -gx <x> -gy <y> ```

* n: number of run times
    - < 0 or 0: run until meet the given goal
    - n: number of run times
    - default: 1
* m: input map name, default _map.csv
* w: input world model, no default.
* r: robot's vision range.
* sx, sy: start point of (x,y), type = float, default = 0.0, 0.0
* gx, gy: goal point of (x,y), type = float, default = 50.0, 50.0

Example: 
```
python Robot_main.py -n 5 -m _MuchMoreFun.csv -sx 5 -sy 5 -gx 35.0 -gy 50.0
python Robot_main.py -n 0 -m _map.csv -sx 5 -sy 5 -gx 35.0 -gy 50.0
python Robot_main.py -n 0 -w _world.png -sx 5 -sy 10 -gx 250 -gy 310 -r 40
```
When the robot finishes its run, the calculated zero-rewarded points will be logged in the console and will be save into a CSV file that is named after the map, the start and goal coordinates, and the vision range. To use that file, set the 'table' variable to 'True' and run the command again.
