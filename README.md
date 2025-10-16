# TkMapsCronjob
Cronjob script to launch production of TkMaps on vocms

Steps of the script:
- Search for runs in Run Registry 
- For those runs, search for their datasets in DQM GUI
- Rerieve the number of LS (from OMS) and Tracks (from DQM GUI)
- If the run is not in the cache:
  - Saves its properties (Run, LS, Tracks, Time) in the cache
  - Add the run in the run list: runs_to_* 
  - Launch TkMaps production for Express (from the list)
  - Launch TkMaps production for Prompt (from the list)


## Setup on vocms

1) Go to top folder 
```
cd /data/users/event_display/dpgtkdqm/cronjobs/ 
```

2) Create main folder 
```
mkdir TkMapsCronjob 
cd TkMapsCronjob 
``` 

3) Setup CMS environment 
```
source /cvmfs/cms.cern.ch/cmsset_default.sh 
```
 
4) Download and compile CMSSW 
```
scram project CMSSW_14_0_14 
cd CMSSW_14_0_14/src/ 
cmsenv 
scram b -j 10 
``` 

5) Go to main folder 
```
cd /data/users/event_display/dpgtkdqm/cronjobs/TkMapsCronjob 
```
 
6) Get the code from GitHub
```
git clone https://github.com/CMSTrackerDPG/TkMapsCronjob 
cd TkMapsCronjob 
```
 
7) Modify the secret codes (not stored on git online) for new SSO authenticatiom 
```
emacs cronTkMaps.sh 
```

8) Fix the year & minimum run number  
```
emacs cronTkMaps.sh 
#Change 2025 and 398080
python3 listProducer.py -y 2025 --min 398080
```

9) Eventually import (or clean) the cache 
Cache is stored in cache_Express.txt and _Prompt.txt files

10) Test execution 
```
source cronTkMaps.sh
```

11) Edit the cronjob list
```
crontab -e
```

12) Add the cronjob details (every hour, at minute 20)

```
20 * * * * /data/users/event_display/dpgtkdqm/cronjobs/TkMapProducer/TkMapProducer/cronTkMaps.sh > /data/users/event_display/dpgtkdqm/cronjobs/cronlogs/TkMapProducer_cron.log 2>&1
```
