#!/bin/sh
#kerberos authentication
kdestroy
kinit -k -t /data/users/event_display/dpgtkdqm/dpgtkdqm.keytab dpgtkdqm
klist 
eosfusebind 
aklog CERN.CH

##Only update the CMSSW release
CMSSW_REL=CMSSW_14_0_14
source /cvmfs/cms.cern.ch/cmsset_default.sh

PARENT_PATH=/data/users/event_display/dpgtkdqm/cronjobs/TkMapsCronjob
echo "Parent path:"$PARENT_PATH

WORK_DIR=$PARENT_PATH/TkMapsCronjob/
CMSSW_DIR=$PARENT_PATH/$CMSSW_REL/src/
echo $CMSSW_DIR
cd $CMSSW_DIR
eval `scramv1 ru -sh`

cd $WORK_DIR
echo "Inside work dir:"$WORK_DIR

#needed for new SSO authenticatiom
export SSO_CLIENT_ID="AskToTkDQMConveners"
export SSO_CLIENT_SECRET="AskToTkDQMConveners"
export ENVIRONMENT=production

echo "Clean run lists"
rm runs_To_*

echo "Create new run lists"
python3 listProducer.py -y 2025 --min 398080


echo "Launching TkMaps Express"

Express_file="runs_To_TkMaps_Express.txt"
while read -r number; do
  source /data/users/event_display/dpgtkdqm/remotescripts/TkMapGeneration/tkmapsFromCronjob.sh "StreamExpress $number"
done < "$Express_file"

echo "Launching TkMaps Prompt"

Prompt_file="runs_To_TkMaps_Prompt.txt"
while read -r number; do
  source /data/users/event_display/dpgtkdqm/remotescripts/TkMapGeneration/tkmapsFromCronjob.sh "ZeroBias $number"
done < "$Prompt_file"
