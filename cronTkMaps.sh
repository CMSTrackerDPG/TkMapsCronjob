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
python3 listProducer.py -y 2025 --min 399200

#pp or HI
collision_mode="HI"

#Standard for pp
datasetExpress="StreamExpress"
datasetPrompt="ZeroBias"
#Change if HI
if [[ "$collision_mode" == "HI" ]]; then
    datasetExpress="StreamHIExpressRawPrime"
    datasetPrompt="HIPhysicsRawPrime0"
fi

# Starting with Collisions runs TkMaps

echo "Launching TkMaps Express - Collisions"

Express_file="runs_To_TkMaps_Express.txt"
while read -r number; do
  source /data/users/event_display/dpgtkdqm/remotescripts/TkMapGeneration/tkmapsFromCronjob.sh "$datasetExpress $number"
done < "$Express_file"

echo "Launching TkMaps Prompt - Collisions"

Prompt_file="runs_To_TkMaps_Prompt.txt"
while read -r number; do
  source /data/users/event_display/dpgtkdqm/remotescripts/TkMapGeneration/tkmapsFromCronjob.sh "$datasetPrompt $number"
done < "$Prompt_file"

# Moving to Cosmics runs TkMaps

datasetExpressCosmics="StreamExpressCosmics"
datasetPromptCosmics="Cosmics"

echo "Launching TkMaps Express - Cosmics"

Express_file="runs_To_TkMaps_ExpressCosmics.txt"
while read -r number; do
  source /data/users/event_display/dpgtkdqm/remotescripts/TkMapGeneration/tkmapsFromCronjob.sh "$datasetExpressCosmics $number"
done < "$Express_file"

echo "Launching TkMaps Prompt - Cosmics"

Prompt_file="runs_To_TkMaps_PromptCosmics.txt"
while read -r number; do
  source /data/users/event_display/dpgtkdqm/remotescripts/TkMapGeneration/tkmapsFromCronjob.sh "$datasetPromptCosmics $number"
done < "$Prompt_file"
