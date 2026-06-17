#!/bin/bash

source /cvmfs/cms.cern.ch/cmsset_default.sh

#2025 : setup 2025
RELEASE=CMSSW_15_0_7

echo $RELEASE

EXECDIR=/data/users/event_display/dpgtkdqm/cronjobs/TkMapsCronjob/$RELEASE/src/DQM/SiStripMonitorClient/scripts/
echo $EXECDIR

cd $EXECDIR
eval `scramv1 runtime -sh`

export SSO_CLIENT_ID=AskToTkDQMConveners
export SSO_CLIENT_SECRET=AskToTkDQMConveners
export ENVIRONMENT=qa

echo $*
python3 TkMap_script_2026.py $*

cd /data/users/event_display/dpgtkdqm/cronjobs/TkMapsCronjob/TkMapsCronjob/
