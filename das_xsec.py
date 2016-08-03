#!/usr/bin/env python

import subprocess
import sys
import os
import json
import optparse


def queryDAS(queryString, verbose=False):

    command = "das_client --query=\"{queryString}\" --format=json --limit=0".format(queryString=queryString)
    if verbose:
        print command
    subProcess = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output = subProcess.communicate()
    if verbose:
        print output
    jsonOutput = json.loads(output[0])
    if (jsonOutput["status"] != "ok"):
        print "Failure in query: %s" % command
        sys.exit()
    return jsonOutput


def printXsec(xsecOutput):

    # print last parameter in list in case there are several defined
    genParams = xsecOutput["data"][0]["mcm"][0]["generator_parameters"][-1]
    print "Cross-section [pb]: %f" % genParams["cross_section"]
    print "Filter efficiency: %f +/- %f" % (genParams["filter_efficiency"], genParams["filter_efficiency_error"])
    print "Matching efficiency: %f +/- %f" % (genParams["match_efficiency"], genParams["match_efficiency_error"])



def main():

    # some example queries
    # dataset = "/WJetsToLNu_HT-100to200_Tune4C_13TeV-madgraph-tauola/Fall13-POSTLS162_V1-v1/GEN-SIM"
    # dataset = "/WJetsToLNu_HT-100to200_Tune4C_13TeV-madgraph-tauola/*/*"
    # dataset = "/QCD*Pt*13TeV*/*/*"
    # dataset = "/QCDddbar_Pt-15to3000_TuneZ2star_Flat_13TeV_pythia6/RunIISpring15DR74-AsymptNoPU_MCRUN2_74_V9A-v1/MINIAODSIM"

    parser = optparse.OptionParser(usage="%prog -d DATASET")
    parser.add_option("-d", "--dataset", dest="dataset",
                      action="store",
                      help="dataset pattern to look for")
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true", default=False,
                      help="print out all the query results")
    (options, args) = parser.parse_args()
    if not options.dataset:   # if dataset is not given
        parser.error('dataset not given')
    dataset = options.dataset
    verbose = options.verbose

    nResults = 1
    if (("?" in dataset) or ("*" in dataset)):
        print "Looking for datasets of pattern: %s" % dataset
        queryString = 'dataset=%s' % (dataset)
        jsonOutput = queryDAS(queryString, verbose)

        nResults = jsonOutput["nresults"]
        print "Found %i datasets" % (nResults)

    print "Will loop over datasets found to find MINIAODs and/or GEN"

    for i in range(nResults):
        thisDataset = dataset
        if (nResults > 1):
            thisDataset = jsonOutput["data"][i]["dataset"][0]["name"]

        if ((thisDataset.find("MINIAOD") >= 0) or (thisDataset.find("/GEN") >= 0)):
            print "Investigating %s" % thisDataset
            parentDataset = thisDataset
            maxSteps = 5
            currentStep = 0
            while ((parentDataset.find("/GEN") < 0) and (currentStep < maxSteps)):
                print "Finding parent of:", parentDataset
                queryString = 'parent dataset=%s' % (parentDataset)
                parentOutput = queryDAS(queryString, verbose)
                print "Found:", parentOutput["data"][0]["parent"][0]["name"]
                parentDataset = parentOutput["data"][0]["parent"][0]["name"]
                currentStep += 1
            if (currentStep == maxSteps):
                print "ERROR: Couldn't find parent of type GEN for %s" % thisDataset
                continue
            queryString = 'mcm dataset=%s | grep mcm.generator_parameters' % (parentDataset)
            xsecOutput = queryDAS(queryString, verbose)
            printXsec(xsecOutput)

    # number of events from MINIAOD
    # xsec for GEN-SIM

    # os.system('python das_client.py --query=\"parent dataset=%s\" --format=json' %(dataset))

if __name__ == "__main__":
    main()
