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
#pp
datasetExpress = '/StreamExpress/'
datasetPrompt  = '/ZeroBias/'
#HI
datasetExpress = '/StreamHIExpressRawPrime/'
datasetPrompt  = '/HIPhysicsRawPrime0/'
#Cosmics
datasetExpressCosmics = '/StreamExpressCosmics/'
datasetPromptCosmics  = '/Cosmics/'


yearPattern = "2025" 

runlist = {}
dsetExpress={}
dsetPrompt={}
dsetExpressCosmics={}
dsetPromptCosmics={}

ExpressFile = "cache_Express.txt"
PromptFile = "cache_Prompt.txt"

ExpressFileToTkMaps = "runs_To_TkMaps_Express.txt"
PromptFileToTkMaps = "runs_To_TkMaps_Prompt.txt"

ExpressCosmicsFile = "cache_ExpressCosmics.txt"
PromptCosmicsFile = "cache_PromptCosmics.txt"

ExpressCosmicsFileToTkMaps = "runs_To_TkMaps_ExpressCosmics.txt"
PromptCosmicsFileToTkMaps = "runs_To_TkMaps_PromptCosmics.txt"

def getInfo(run):
    data=runregistry.get_run(run_number=run)
    lastLS=data["oms_attributes"]["last_lumisection_number"]
    return (lastLS)

def wasExpressDoneInGUI(run):
    global dsetExpress
    try:
        dataset = dsetExpress[int(run)]
        info = dqm_get_json(serverurl, run, dataset, "Info/ProvInfo")
        done = info['runIsComplete']['value']
        return done == '1'
    except:
        return False 
    return False

def isExpressDoneInGUI(run,dataset):
    try:
        info = dqm_get_json(serverurl, run, dataset, "Info/ProvInfo")
        done = info['runIsComplete']['value']
        return done == '1'
    except:
        return False 
    return False

def RRrunsList(minRun,maxRun):
    runs = runregistry.get_datasets(filter={'dataset_name':{'like':'%Express%Co%s20%'},'run_number':{'and':[{'>=':minRun},{'<=':maxRun}]}})
    #Express%Co%s20% valid for both Collisions202X and Cosmics 202X (but not for Commissioning202X)
    rlist = [r['run_number'] for r in runs]
    return rlist

def main():
    
    global express,prompt,yearPattern,runlist,dsetExpress,dsetPrompt,dsetExpressCosmics,dsetPromptCosmics
    parser = OptionParser()
    parser.add_option("-m", "--min", dest="min", type="int", default=0,      help="Minimum run")
    parser.add_option("-M", "--max", dest="max", type="int", default=999999, help="Maximum run")
    parser.add_option("-y", "--year", dest="year", type="string", default="2025", help="Year")
    #parser.add_option("--min-ls",    dest="minls",  type="int", default="10",   help="Ignore runs with less than X lumis (default 10)")
    (options, args) = parser.parse_args()
    
    if len(options.year)!=4:
        print("Insert the year in the 4-digit format (i.e 2018)")
        return
    yearPattern=".*"+options.year[2:4]
    
    print(yearPattern)

    #-------------------------------------------------------------------------
    print("List runs from Run Registry")
    RRruns=RRrunsList(options.min, options.max) 

    print("List of Runs from Run Registry")
    print(RRruns)
    
    #-------------------------------------------------------------------------
    print("List runs & dataset from GUI")
    for n,d in (('Express',datasetExpress), ('Prompt',datasetPrompt), ('ExpressCosmics',datasetExpressCosmics), ('PromptCosmics',datasetPromptCosmics)):
        samples = dqm_get_samples(serverurl, d+yearPattern)
        print("SAMPLES")
        #print(samples)
        
        for (r, d2) in samples:
          if int(r) >= options.min:
            if "DQMIO" in d2 : 
                if r in RRruns:
                    if n == 'Express':
                        dsetExpress[int(r)]=d2
                    elif n == 'Prompt': 
                        dsetPrompt[int(r)]=d2
                    elif n == 'ExpressCosmics':
                        dsetExpressCosmics[int(r)]=d2
                    elif n == 'PromptCosmics': 
                        dsetPromptCosmics[int(r)]=d2
                    runlist.update({str(r):{str(n)}})

    print("List of Runs with dataset in the GUI")
    print(runlist)

    #-------------------------------------------- Collisions
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
    
    #-------------------------------------------- Collisions
    lumiCacheExpressCosmics = {}
    lumiCacheExpressCosmicsName = ExpressCosmicsFile
    lumiCachePromptCosmics = {} 
    lumiCachePromptCosmicsName = PromptCosmicsFile
    
    #Check the caches
    
    print("Cache Express Cosmics: {0}".format(lumiCacheExpressCosmicsName))
    try:
        lumiFileExpressCosmics = open(lumiCacheExpressCosmicsName, "r")
        for l in lumiFileExpressCosmics:
            m = re.match(r"(\d+)\s+(\d+)\s+([0-9.]+).*", l)
            if m:
                cols = l.split()
                #print(cols)
                lumiCacheExpressCosmics[str(cols[0])] = [ int(cols[1]), int(cols[2]), str(cols[3]) ] 
        print("LumiCache ExpressCosmics" , lumiCacheExpressCosmics)
        lumiFileExpressCosmics.close()
    except IOError:
        print("Express Cosmics Cache not readable or not present!")
        pass 

    print("Cache Prompt Cosmics: {0}".format(lumiCachePromptCosmicsName))
    try:
        lumiFilePromptCosmics = open(lumiCachePromptCosmicsName, "r")
        for l in lumiFilePromptCosmics:
            m = re.match(r"(\d+)\s+(\d+)\s+([0-9.]+).*", l)
            if m:
                cols = l.split()
                #print(cols)
                lumiCachePromptCosmics[str(cols[0])] = [ int(cols[1]), int(cols[2]), str(cols[3]) ] 
        print("LumiCache PromptCosmics" , lumiCachePromptCosmics)
        lumiFilePromptCosmics.close()
    except IOError:
        print("Prompt Cosmics Cache not readable or not present!")
        pass 
    
    #------------------------------------------- Collisions

    print("Getting tracks from GUI")

    newcacheExpress = open(ExpressFile, "w");
    newcacheExpress.write("run\tls\ttracks\ttime\n");

    newcachePrompt = open(PromptFile, "w");
    newcachePrompt.write("run\tls\ttracks\ttime\n");

    ExpressToTkMaps = open(ExpressFileToTkMaps, "w");
    PromptToTkMaps = open(PromptFileToTkMaps, "w");

    now = datetime.now().strftime("%d-%b-%Y_%H:%M")

    for run in runlist.keys():
        
          if run not in lumiCacheExpress.keys():
            if int(run) in dsetExpress:
                dataset = dsetExpress[int(run)]
            else:
                continue

            print(" -------------------------------------------------")
            print(" ------ ",run)
            lslumi = (-1, -1, "time")
            
            print(" - Express")

            if isExpressDoneInGUI(run,dataset):
          
                try:
                    nlumis=getInfo(int(run))
                    print("DATASET " , dataset)
                    #print("Number of LS: %d " % (nlumis))
                    at = dqm_get_json(serverurl, run, dataset, "/Tracking/TrackParameters/generalTracks/HitProperties",True)
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
            print(" -------------------------------------------------")
            print(" ------ ",run)
            print("Already on Express Cache")
            newcacheExpress.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCacheExpress[run][0], lumiCacheExpress[run][1], lumiCacheExpress[run][2]))
          

          if run not in lumiCachePrompt.keys():
            if int(run) in dsetPrompt:
                dataset = dsetPrompt[int(run)]
            else:
                continue

            lslumi = (-1, -1, "time")
            print(" - Prompt")
            
            try:
                nlumis=getInfo(int(run))
                print("DATASET " , dataset)
                #print("Number of LS: %d " % (nlumis))
                at = dqm_get_json(serverurl, run, dataset, "/Tracking/TrackParameters/generalTracks/HitProperties",True)
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
    print("Collisions Done. Moving to Cosmics!")

    #------------------------------------------- Cosmics

    print("Getting tracks from GUI")

    newcacheExpress = open(ExpressCosmicsFile, "w");
    newcacheExpress.write("run\tls\ttracks\ttime\n");

    newcachePrompt = open(PromptCosmicsFile, "w");
    newcachePrompt.write("run\tls\ttracks\ttime\n");

    ExpressToTkMaps = open(ExpressCosmicsFileToTkMaps, "w");
    PromptToTkMaps = open(PromptCosmicsFileToTkMaps, "w");

    now = datetime.now().strftime("%d-%b-%Y_%H:%M")

    for run in runlist.keys():
        
          if run not in lumiCacheExpressCosmics.keys():
            if int(run) in dsetExpressCosmics:
                dataset = dsetExpressCosmics[int(run)]
            else:
                continue

            print(" -------------------------------------------------")
            print(" ------ ",run)
            lslumi = (-1, -1, "time")
            
            print(" - Express")

            if isExpressDoneInGUI(run,dataset):
          
                try:
                    nlumis=getInfo(int(run))
                    print("DATASET " , dataset)
                    #print("Number of LS: %d " % (nlumis))
                    at = dqm_get_json(serverurl, run, dataset, "/Tracking/TrackParameters/HitProperties",True)
                    ntracks = at['NumberOfRecHitsPerTrack_CKFTk']['rootobj'].GetEntries()
                    lslumi = (nlumis, ntracks)
                    print("Adding to cache")
                    lumiCacheExpressCosmics[str(run)] = lslumi
                    print("%d\t%d\t%d\n" % (int(run), int(lumiCacheExpressCosmics[run][0]), int(lumiCacheExpressCosmics[run][1])))
                    newcacheExpress.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCacheExpressCosmics[run][0], lumiCacheExpressCosmics[run][1], now))
                    if  lumiCacheExpressCosmics[run][0] > 50:
                        ExpressToTkMaps.write("%d\n" % (int(run)))
                    else:
                        print("Cosmics run < 50 LS --> Not generating TkMaps")
                except:
                    pass
            else:
                print("Not yet Completed on GUI")
                continue
          else:
            print(" -------------------------------------------------")
            print(" ------ ",run)
            print("Already on Express Cosmics Cache")
            newcacheExpress.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCacheExpressCosmics[run][0], lumiCacheExpressCosmics[run][1], lumiCacheExpressCosmics[run][2]))
          

          if run not in lumiCachePromptCosmics.keys():
            if int(run) in dsetPromptCosmics:
                dataset = dsetPromptCosmics[int(run)]
            else:
                continue

            lslumi = (-1, -1, "time")
            print(" - Prompt")

            try:
                nlumis=getInfo(int(run))
                print("DATASET " , dataset)
                #print("Number of LS: %d " % (nlumis))
                at = dqm_get_json(serverurl, run, dataset, "/Tracking/TrackParameters/HitProperties",True)
                ntracks = at['NumberOfRecHitsPerTrack_CKFTk']['rootobj'].GetEntries()
                lslumi = (nlumis, ntracks)
                print("Adding to cache")
                lumiCachePromptCosmics[str(run)] = lslumi
                print("%d\t%d\t%d\n" % (int(run), int(lumiCachePromptCosmics[run][0]), int(lumiCachePromptCosmics[run][1])))
                newcachePrompt.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCachePromptCosmics[run][0], lumiCachePromptCosmics[run][1], now))
                if  lumiCachePromptCosmics[run][0] > 50:
                    PromptToTkMaps.write("%d\n" % (int(run)))
                else:
                    print("Cosmics run < 50 LS --> Not generating TkMaps")
            except:
                print("Not yet Available on GUI")
                pass
          else:
            print("Already on Prompt Cosmics Cache")
            newcachePrompt.write("%d\t%d\t%d\t%s\n" % (int(run), lumiCachePromptCosmics[run][0], lumiCachePromptCosmics[run][1], lumiCachePromptCosmics[run][2]))
            
    newcacheExpress.close()
    newcachePrompt.close()
    ExpressToTkMaps.close()
    PromptToTkMaps.close()

    print("--------------------------------------------")
    print("Collisions and Cosmics Done. Lists are ready!")
    
if __name__ == '__main__':
    main()
