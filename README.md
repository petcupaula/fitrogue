# fitrogue

## Installation of Heroku app

* Get Heroku CLI (https://devcenter.heroku.com/articles/heroku-cli)
* From cmd line:
```
heroku login
git remote add heroku https://git.heroku.com/fit-rogue-app-hack-2019.git
git commit -m "[your commit message"
git push heroku master
git push origin
```
* 

## Example Google Fit data

The most recent data:

```
{'sleep_hours': 0.0, 'meditation_mins': 0, 'workout_mins': 0, 'steps_count': 12302}
```

Historical data:

```
{'2019-11-07': {'steps_count': 703}, '2019-11-08': {'steps_count': 4369}, '2019-11-09': {'steps_count': 28}, '2019-11-10': {'steps_count': 3057}, '2019-11-11': {'steps_count': 12412}, '2019-11-12': {'steps_count': 5320}, '2019-11-13': {'steps_count': 7766}, '2019-11-14': {'steps_count': 14052, 'sleep_hours': 6.0, 'meditation_mins': 12, 'workout_mins': 0}, '2019-11-15': {'steps_count': 10416, 'sleep_hours': 0.0, 'meditation_mins': 10, 'workout_mins': 0}}
```