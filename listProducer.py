from math import *
from dqmjson import *
from ROOT import TFile, gStyle, TCanvas, TH1F, TLegend
from ROOT import kBlue, kGreen
from optparse import OptionParser
from xml.dom.minidom import parseString
#from omsapi import getInfo
import runregistry
import xmlrpc
#import elementtree.ElementTree as ET
import sys, os, os.path, time, re, subprocess
import urllib
import json
from datetime import datetime

##Dataset for GUI query
express = '/StreamExpress/'
prompt  = '/ZeroBias/'
##
yearPattern = "2025" 
##
runlist = {}
dsetExpress={}
dsetPrompt={}

ExpressFile = "cache_Express.txt"
PromptFile = "cache_Prompt.txt"

ExpressFileToTkMaps = "runs_To_TkMaps_Express.txt"
PromptFileToTkMaps = "runs_To_TkMaps_Prompt.txt"

def getInfo(run):
    data=runregistry.get_run(run_number=run)
    lastLS=data["oms_attributes"]["last_lumisection_number"]
    return (lastLS)


def isExpressDoneInGUI(run):
    global dsetExpress
    try:
        dataset = dsetExpress[int(run)]
        info = dqm_get_json(serverurl, run, dataset, "Info/ProvInfo")
        done = info['runIsComplete']['value']
        return done == '1'
    except:
        return False 
    return False

def RRrunsList(minRun,maxRun):
    runs = runregistry.get_datasets(filter={'dataset_name':{'like':'%Express%Collisions%'},'run_number':{'and':[{'>=':minRun},{'<=':maxRun}]}})
    rlist = [r['run_number'] for r in runs]
    return rlist

def main():
    
    ####Cosmics settings are set after loading config options#####
    global groupName,express,prompt,yearPattern,runlist,dsetExpress,dsetPrompt
    parser = OptionParser()
    #parser.add_option("-c", "--cosmics", dest="cosmics", action="store_true",  default=False, help="Check cosmic instead of collision")
#    parser.add_option("-C", "--commissioning", dest="commissioning", action="store_true",  default=False, help="Check commssioning instead of collision")
    parser.add_option("-m", "--min", dest="min", type="int", default=0,      help="Minimum run")
    parser.add_option("-M", "--max", dest="max", type="int", default=999999, help="Maximum run")
    parser.add_option("-y", "--year", dest="year", type="string", default="2025", help="Year")
    parser.add_option("--min-ls",    dest="minls",  type="int", default="10",   help="Ignore runs with less than X lumis (default 10)")
#    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",  default=False, help="Print more info")
#    parser.add_option("-p", "--pretend", dest="pretend", action="store_true",  default=False, help="Use cached RR result")
#    parser.add_option("-f", "--force", dest="force", action="store_true",  default=False, help="Never cached RR result")
#    parser.add_option("-n", "--notes", dest="notes", type="string", default="notes.txt", help="Text file with notes")
    (options, args) = parser.parse_args()
    
    if len(options.year)!=4:
        print("Insert the year in the 4-digit format (i.e 2018)")
        return
    yearPattern=".*"+options.year[2:4]
    groupName = "Collisions"+options.year[2:4] #TO_BE_CHANGED_EACH_YEAR
    
    print(yearPattern)
    print(groupName)


    #-------------------------------------------------------------------------
    print("List runs from Run Registry")
    ed = express
    pd = prompt
    RRruns=RRrunsList(options.min, options.max) 

    print("List of Runs from Run Registry")
    print(RRruns)
    
    #-------------------------------------------------------------------------
    print("List runs & dataset from GUI")
    for n,d in (('Express',ed), ('Prompt',pd)):
        samples = dqm_get_samples(serverurl, d+yearPattern)
        print("SAMPLES")
        #print(samples)
        
        for (r, d2) in samples:
          if int(r) >= options.min:
            if "DQMIO" in d2 : 
                if r in RRruns:
                    if 'Express' in n:
                        dsetExpress[int(r)]=d2
                    if 'Prompt' in n:  #CHANGED n in d
                        dsetPrompt[int(r)]=d2
                    runlist.update({str(r):{str(n)}})

    print("List of Runs with dataset in the GUI")
    print(runlist)

    #-------------------------------------------------------------------------
    lumiCacheExpress = {}; 
    lumiCacheExpressName = ExpressFile
    lumiCachePrompt = {}; 
    lumiCachePromptName = PromptFile
    
    #Check the caches
    
    print("Cache Express : {0}".format(lumiCacheExpressName))
    try:
        lumiFileExpress = open(lumiCacheExpressName, "r")
        for l in lumiFileExpress:
            m = re.match(r"(\d+)\s+(\d+)\s+([0-9.]+).*", l)
            if m:
                cols = l.split()
                #print(cols)
                lumiCacheExpress[str(cols[0])] = [ int(cols[1]), int(cols[2]), str(cols[3]) ] 
        print("LumiCache Express" , lumiCacheExpress)
        lumiFileExpress.close()
    except IOError:
        print("Express Cache not readable or not present!")
        pass 

    print("Cache Prompt : {0}".format(lumiCachePromptName))
    try:
        lumiFilePrompt = open(lumiCachePromptName, "r")
        for l in lumiFilePrompt:
            m = re.match(r"(\d+)\s+(\d+)\s+([0-9.]+).*", l)
            if m:
                cols = l.split()
                #print(cols)
                lumiCachePrompt[str(cols[0])] = [ int(cols[1]), int(cols[2]), str(cols[3]) ] 
        print("LumiCache Prompt" , lumiCachePrompt)
        lumiFilePrompt.close()
    except IOError:
        print("Prompt Cache not readable or not present!")
        pass 
    
    #-------------------------------------------------------------------------
    print("Getting tracks from GUI")

    newcacheExpress = open(ExpressFile, "w");
    newcacheExpress.write("run\tls\ttracks\ttime\n");

    newcachePrompt = open(PromptFile, "w");
    newcachePrompt.write("run\tls\ttracks\ttime\n");

    ExpressToTkMaps = open(ExpressFileToTkMaps, "w");
    PromptToTkMaps = open(PromptFileToTkMaps, "w");

    now = datetime.now().strftime("%d-%b-%Y_%H:%M")

    for run in runlist.keys():
          print(" -------------------------------------------------")
          print(" ------ ",run)
          lslumi = (-1, -1, "time")

          print(" - Express")
          if run not in lumiCacheExpress.keys():
            if isExpressDoneInGUI(run):
          
                try:
                    dataset = dsetExpress[int(run)]
                    nlumis=getInfo(int(run))
                    print("DATASET " , dataset)
                    #print("Number of LS: %d " % (nlumis))
                    at = dqm_get_json(serverurl, run, dataset, "/Tracking/TrackParameters/generalTracks/HitProperties",True)
                    ei = dqm_get_json(serverurl, run, dataset, "Info/ProvInfo")
                    ntracks = at['NumberOfRecHitsPerTrack_GenTk']['rootobj'].GetEntries()
                    lslumi = (nlumis, ntracks)
                    print("Adding to cache")
                    lumiCacheExpress[str(run)] = lslumi
                    print("%d\t%d\t%d\n" % (int(run), int(lumiCacheExpress[run][0]), int(lumiCacheExpress[run][1])))
                    newcacheExpress.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCacheExpress[run][0], lumiCacheExpress[run][1], now))
                    ExpressToTkMaps.write("%d\n" % (int(run)))
                except:
                    pass
            else:
                print("Not yet Completed on GUI")
                continue
          else:
            print("Already on Express Cache")
            newcacheExpress.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCacheExpress[run][0], lumiCacheExpress[run][1], lumiCacheExpress[run][2]))
          
          lslumi = (-1, -1, "time")
          print(" - Prompt")

          if run not in lumiCachePrompt.keys():
            try:
                dataset = dsetPrompt[int(run)]
                nlumis=getInfo(int(run))
                print("DATASET " , dataset)
                #print("Number of LS: %d " % (nlumis))
                at = dqm_get_json(serverurl, run, dataset, "/Tracking/TrackParameters/generalTracks/HitProperties",True)
                ei = dqm_get_json(serverurl, run, dataset, "Info/ProvInfo")
                ntracks = at['NumberOfRecHitsPerTrack_GenTk']['rootobj'].GetEntries()
                lslumi = (nlumis, ntracks)
                print("Adding to cache")
                lumiCachePrompt[str(run)] = lslumi
                print("%d\t%d\t%d\n" % (int(run), int(lumiCachePrompt[run][0]), int(lumiCachePrompt[run][1])))
                newcachePrompt.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCachePrompt[run][0], lumiCachePrompt[run][1], now))
                PromptToTkMaps.write("%d\n" % (int(run)))
            except:
                print("Not yet Available on GUI")
                pass
          else:
            print("Already on Prompt Cache")
            newcachePrompt.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCachePrompt[run][0], lumiCachePrompt[run][1], lumiCachePrompt[run][2]))
            
    newcacheExpress.close()
    newcachePrompt.close()
    ExpressToTkMaps.close()
    PromptToTkMaps.close()

    print("--------------------------------------------")
    print("Done. Lists are ready!")
    
if __name__ == '__main__':
    main()
