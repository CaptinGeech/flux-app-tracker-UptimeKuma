# flux-app-tracker-UptimeKuma
A push monitor script that will check an ip:port of a flux node and store all runnigs application names to allow Uptime Kuma to alert you when one is added or removed via push monitoring.

## How it works.
The script takes in 3 params. the first two being the public/private IP address and port of the node you want to check for running apps. The last param is the UptimeKuma Push Token.

The script will call the flux apps api on the ip:port you specified to get all running applications on the node. It then strips out just the names of the apps and saves it to a file. This is needed so it can compare on the next poll of the api. 

If the file has less names then the current api call, apps were added.
If the file has more names then the current api call, apps were removed.

We can now take this information and push it to UptimeKuma

## Uptime Notifications
Because UptimeKuma monitors for a state change before notifying, we have to specifically push a down state and then a up state.  As of now, this does cause a double ping.

Example: Assume we have been monitoring a node with no applicaiotns, every x minutes the script runs, it continues to push an `up` state to Kuma. This does not result in a ping because everything as been running in the same state.
A new app is added, to be notified, we have to change state. First we push a `down` state with a message of "processing". 2 seconds later, push a `up` state with the name of the app that was added.

## Before you copy the script.
Before you copy the script over, think about where you want it. I like everything living in my UptimeKuma volumn. UptimeKuma only has a sinlge volumn, so i usually set the directory to that location then add a directory for my `push-scripts`.

So if my compose file was:
```
uptime-kuma:
    ...
    volumes:
      - /docker/uptime:/app/data
```
I would set the path to `/docker/uptime/push-scripts/flux-app-tracker`

The data files it uses and saves will then be places in a nested `data/` directory.

## copy the script.
```
wget -P /docker/uptime/push-scripts/flux-app-tracker/ https://raw.githubusercontent.com/CaptinGeech/flux-app-tracker-UptimeKuma/refs/heads/main/flux-app-tracker.py
```

## Update your script
After you copy your script, you need to edit the file so you can update to use your UptimeKuma url..
```
KUMA_DOMAIN = "http://localhost:3001"
```


## Uptime Kuma Monitor
1. When creating a new monitor, change the Monitor Type to `Push`.
2. In the Push URL, not the token that comes after `/api/push/`.
3. Heartbeat is the interval you expect the script to run.
4. Leave Retries and Resends set to 0
5. Save.

This will be in a pending state until you set up a crontab.

## Crontab
Now back in tour terminal, do `crontab -e` and add a line at the bottom to run your script.  For example
```
*/5 * * * * /usr/bin/python3 /docker/uptime/push-scripts/flux-app-tracker/flux-app-tracker.py 192.168.1.10 16127
```