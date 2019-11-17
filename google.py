import os
from datetime import date, timedelta, datetime
from flask import Flask, redirect, url_for, render_template, request
from flask_dance.contrib.google import make_google_blueprint, google
import json
from ruamel.yaml import YAML
import backend.dungeon_time

yaml = YAML(typ='safe')  # default, if not specfied, is 'rt' (round-trip)


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersekrit")
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get(
    "GOOGLE_OAUTH_CLIENT_SECRET")
google_bp = make_google_blueprint(scope=["profile", "email", "https://www.googleapis.com/auth/fitness.activity.read",
                                         "https://www.googleapis.com/auth/fitness.body.read", "https://www.googleapis.com/auth/fitness.location.read"])
app.register_blueprint(google_bp, url_prefix="/login")


def shop(stats):
    resources = {}
    if stats["meditation_mins"] > 0:
        resources["meditation"] = 1
    else:
        resources["meditation"] = 0
    if stats["sleep_hours"] < 6.5:
        resources["sleep"] = 0
    elif stats["sleep_hours"] < 7 or stats["sleep_hours"] > 10:
        resources["sleep"] = 1
    elif stats["sleep_hours"] < 7.15 or stats["sleep_hours"] > 8.5:
        resources["sleep"] = 2
    else:
        resources["sleep"] = 3

    if stats["steps_count"] < 4000:
        resources["steps"] = 0
    elif stats["steps_count"] < 7000:
        resources["steps"] = 1
    elif stats["steps_count"] < 10000:
        resources["steps"] = 2
    else:
        resources["steps"] = 3

    if stats["workout_mins"] < 5:
        resources["exercise"] = 0
    elif stats["workout_mins"] < 25:
        resources["exercise"] = 1
    else:
        resources["exercise"] = 3

    with open("backend/equipment.yaml", "r") as equipment_file:
        items = yaml.load(equipment_file)
    item_dict = {}
    for name, item in items.items():
        res_l = item_dict.get(item["resource"], [])
        res_l.append(item)
        item_dict[item["resource"]] = res_l

    return render_template("shop.html", resources=resources, items=item_dict.encode(encoding='UTF-8'), stats=stats)


@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v1/userinfo")

    # Get stats for past day
    stats = getRecentFitStats()

    # TO-DO: magic stuff with the store using the fit stats
    print(stats)

    #return "You are {email} on Google".format(email=resp.json()["email"])
    return shop(stats)

@app.route("/fitstats")
def fitstats():
    # Url call would look like: fitstats?startDate=2019-11-10&endDate=2019-11-16
    # Can also look like: fitstats?startDate=2019-11-16
    # Or like: fitstats?startDate=2019-11-16&endDate=2019-11-16
    startDate = request.args.get('startDate', None)
    endDate = request.args.get('endDate', None)

    if not startDate:
        return "Please provide a startDate and endDate"

    if startDate == endDate or not endDate:
        # start from one day before
        start_date = datetime.strptime(startDate, '%Y-%m-%d')
        start_date = start_date - timedelta(1)
        if not endDate:
            endDate = startDate
        startDate = start_date.strftime("%Y-%m-%d")

    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v1/userinfo")

    # Get stats for a date range (format: '2019-11-10')
    stats = getFitStats(startDateStr=startDate, endDateStr=endDate)
    
    print(stats)

    #return "You are {email} on Google".format(email=resp.json()["email"])
    return shop(stats)

def getRecentFitStats():
    
    # Define time range
    # For sessions: format as RFC3339 timestamp (example: "2019-11-14T12:00:00.000Z")
    # For steps: format in milliseconds (example: 1573796215000)
    today = date.today()
    yesterday = today - timedelta(1)
    reset_time = "T08:00:00.000Z"
    startTime_ts = yesterday.strftime("%Y-%m-%d") + reset_time
    endTime_ts = today.strftime("%Y-%m-%d") + reset_time
    startTime_millis = unix_time_millis(datetime.strptime(startTime_ts, '%Y-%m-%dT%H:%M:%S.%fZ'))
    endTime_millis = unix_time_millis(datetime.strptime(endTime_ts, '%Y-%m-%dT%H:%M:%S.%fZ'))

    fit_stats = getSessions(startTime_ts, endTime_ts, method="sum")
    steps_count = getSteps(startTime_millis, endTime_millis, method="sum")
    fit_stats["steps_count"] = steps_count
 
    return fit_stats

def getFitStats(startDateStr, endDateStr):
    
    # Define time range
    # For sessions: format as RFC3339 timestamp (example: "2019-11-14T12:00:00.000Z")
    # For steps: format in milliseconds (example: 1573796215000)

    reset_time = "T08:00:00.000Z"
    startTime_ts = startDateStr + reset_time
    endTime_ts = endDateStr + reset_time
    startTime_millis = unix_time_millis(datetime.strptime(startTime_ts, '%Y-%m-%dT%H:%M:%S.%fZ'))
    endTime_millis = unix_time_millis(datetime.strptime(endTime_ts, '%Y-%m-%dT%H:%M:%S.%fZ'))

    fit_stats = getSessions(startTime_ts, endTime_ts, method="list")
    steps_count = getSteps(startTime_millis, endTime_millis, method="list")
    
    return mergeDict(steps_count, fit_stats)

def getSteps(startTime_millis, endTime_millis, method="sum"):
    # Return an integer representing count of steps - if method="sum"
    # Return a list representing count of steps per day - if method="list"
    # Note: 1 day in mills is 86400000

    # Prepare json request body
    json_post = {"aggregateBy": [
        {
            "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
        }
    ],
    "bucketByTime": {
        "durationMillis": 86400000,
        "period": {
            "type": "day",
            "value": 1,
            "timeZoneId": "Europe/Helsinki"
        }
    },
    "endTimeMillis": endTime_millis,
    "startTimeMillis": startTime_millis
    }

    # Get data
    resp = google.post("/fitness/v1/users/me/dataset:aggregate", json=json_post)
    #print(resp.json())
    
    # Extract steps value
    #steps_count = resp.json()["bucket"][0]["dataset"][0]["point"][0]["value"][0]["intVal"]

    if "bucket" in resp.json():
        if method == "sum":
            steps_count = 0
            for period in resp.json()["bucket"]:
                for dataset in period["dataset"]:
                    for point in dataset["point"]:
                        steps = point["value"][0]["intVal"]
                        steps_count += steps
            return steps_count
        elif method == "list":
            steps_count_hist = {}
            steps = 0
            for period in resp.json()["bucket"]:
                for dataset in period["dataset"]:
                    for point in dataset["point"]:
                        steps = point["value"][0]["intVal"]
                        steps_date = millis_to_date(int(period["startTimeMillis"]))
                        steps_count_hist[steps_date] = {"steps_count": steps}
            return steps_count_hist
    
    ## Note: The API does not suppport aggregating over a long period of time and will
    ## return an error instead. 'code': 400, 'message': 'aggregate duration too large'
    ## For now, returning an empty dict in this case, so it does not affect the rest
    ## of the application logic. 

    return dict()
    
def getSessions(startTime_ts, endTime_ts, method="sum"):
    # Return a dict with time used per activity - if method="sum"
    # Return a dict with historical data of activities - if method="list"

    # Activity type codes
    # See available activity type codes: https://developers.google.com/fit/rest/v1/reference/activity-types
    # walking = 93, running = 8, biking = 1, other = 108
    sleep_code = 72
    meditation_code = 45
    workout_codes = [8, 1]
    other_code = 108 # using category "other" for digital wellbeing activities
    codes_of_interest = [sleep_code, meditation_code, other_code] + workout_codes

    sleep_millis = 0
    meditation_millis = 0
    workout_millis = 0
    social_media_millis = 0

    # Get data
    get_url = "/fitness/v1/users/me/sessions?startTime="+startTime_ts+"&endTime="+endTime_ts
    resp = google.get(get_url)
    print(resp.json())

    activity_hist = {}

    for activity in resp.json()["session"]:
        code = activity["activityType"]
        if code in codes_of_interest:
            
            # get duration of activity (sometime computed already in activeTimeMillis)
            activity_time = 0
            if "activeTimeMillis" in activity:
                activity_time = int(activity["activeTimeMillis"])
            else:
                activity_time = int(activity["endTimeMillis"]) - int(activity["startTimeMillis"])
            
            # add time to corresponding activity of interest
            if method == "sum":
                # sum up for one day
                if code == sleep_code:
                    sleep_millis += activity_time
                elif code == meditation_code:
                    meditation_millis += activity_time
                elif code in workout_codes:
                    workout_millis += activity_time
                elif code == other_code and "social" in activity["name"].lower():
                    social_media_millis += activity_time
            elif method == "list":
                # sum up per day per activity
                activity_date = millis_to_date(int(activity["startTimeMillis"]))
                if activity_date not in activity_hist: 
                    activity_hist[activity_date] = {"sleep_hours": 0.0, "meditation_mins": 0, "workout_mins": 0, "social_media_hours": 0.0}
                if code == sleep_code:
                    activity_hist[activity_date]["sleep_hours"] += millis_to_hours(activity_time)
                elif code == meditation_code:
                    activity_hist[activity_date]["meditation_mins"] += millis_to_mins(activity_time)
                elif code in workout_codes:
                    activity_hist[activity_date]["workout_mins"] += millis_to_mins(activity_time)
                elif code == other_code and "social" in activity["name"].lower():
                    activity_hist[activity_date]["social_media_hours"] += millis_to_hours(activity_time)

    if method == "sum":
        sleep_hours = millis_to_hours(sleep_millis)
        meditation_mins = millis_to_mins(meditation_millis)
        workout_mins = millis_to_mins(workout_millis)
        social_media_hours = millis_to_hours(social_media_millis)

        return {"sleep_hours": sleep_hours,
                "meditation_mins": meditation_mins,
                "workout_mins": workout_mins,
                "social_media_hours": social_media_hours}

    elif method == "list":
        return activity_hist

def unix_time_millis(dt):
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds() * 1000.0)

def millis_to_date(millis):
    # Returns date (string) from milliseconds (number)
    return datetime.fromtimestamp(millis/1000.0).strftime("%Y-%m-%d")

def millis_to_hours(millis):
    # Return hours (number) from milliseconds (number)
    return (millis/(1000*60*60))%24

def millis_to_mins(millis):
    # Return mins (number) from milliseconds (number)
    return int((millis/(1000*60))%60)

def mergeDict(dict1, dict2):
    dict3 = dict1.copy()
    for key, value in dict3.items():
        if key in dict1 and key in dict2:
            dict3[key] = value.update(dict2[key])
    for key, value in dict2.items():
        if key not in dict1:
            dict3[key] = dict2[key]
    return dict1

@app.route("/login")
def login():
    return redirect(url_for("google.login"))


@app.route("/shop")
def shop2():

    resources = {
        "activity": 2,
        "meditation": 1,
        "sleep": 1
    }

    with open("backend/equipment.yaml", "r") as equipment_file:
        items = yaml.load(equipment_file)
    item_dict = {}
    for name, item in items.items():
        res_l = item_dict.get(item["resource"], [])
        res_l.append(item)
        item_dict[item["resource"]] = res_l

    return render_template("shop.html", resources=resources, items=item_dict)

@app.route('/game', methods=["POST"])
def game():
    data = json.loads(request.form["selecteditems"])
    log = backend.dungeon_time.run_dungeon(data)
    for l in log:
        print(l)
    return render_template('game.html', log=json.dumps(log))

if __name__ == "__main__":
    app.run()
