#!/usr/bin/env python

'''
driverTools.py
'''

# **************************************** #


#############
#  IMPORTS  #
#############
# standard python packages
import inspect, os, sys, time

# ------------------------------------------------------ #
# import sibling packages HERE!!!
packagePath  = os.path.abspath( __file__ + "/../.." )
sys.path.append( packagePath )

from dedt           import dedt, dedalusParser
from derivation     import ProvTree
from utils          import parseCommandLineInput, tools
from evaluators     import c4_evaluator, evalTools
from solvers        import EncodedProvTree_CNF, newProgGenerationTools, solverTools
from visualizations import vizTools

# **************************************** #


#############
#  GLOBALS  #
#############
DEBUG                = True
OUTPUT_PROV_TREES_ON = True
OUTPUT_TREE_CNF_ON   = True  # output prov tree renders

##################
#  GET ARG DICT  #
##################
# input nothing
# ouput list of command line arguments
def getArgDic( ) :
  # get list of command line args, except prog name
  argList = sys.argv[1:]

  # print help if no args provided
  if len(argList) < 1 :
    thisFilename = os.path.basename(__file__)     # name of this file
    sys.exit( "No arguments provided. Please run 'python " + sys.argv[0] + " -h' for assistance." )

  # ----------------------------------------------- #

  # pass list to parse args, get dict of args
  argDict = driverTools.parseArgs( )
  print argDict

  # check if EOT is an integer (this better pass!)
  try :
    val = int( argDict[ "EOT" ] )
  except :
    tools.bp( __name__, inspect.stack()[0][3], " Could not convert EOT into integer: EOT = " + str(eot) )


################
#  PARSE ARGS  #
################
# parse arguments from the command line
def parseArgs( ) :
  argDict = {}   # empty dict

  argDict = parseCommandLineInput.parseCommandLineInput( )  # get dictionary of arguments.

  return argDict


########################
#  DEDALUS TO DATALOG  #
########################
# translate all input dedalus files into a single datalog program
def dedalus_to_datalog( argDict, cursor ) :
  return dedt.translateDedalus( argDict, cursor )


##############
#  EVALUATE  #
##############
# evaluate the datalog program using some datalog evaluator
# return some data structure or storage location encompassing the evaluation results.
def evaluate( evaluatorType, datalogProgPath, tableListPath, savepath ) :

  evaluators = [ 'C4_CMDLINE', 'C4_WRAPPER' ]

  # C4_CMDLINE
  if evaluatorType == evaluators[0] :
    return c4_evaluator.runC4_directly( datalogProgPath, tableListPath, savepath )

  # C4_WRAPPER
  elif evaluatorType == evaluators[1] :
    return c4_evaluator.runC4_wrapper( datalogProgPath, tableListPath )

  # WHAAAAA????
  else :
    tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : unrecognized evaluator type '" + evaluatorType + "', currently recognized evaluators are : " + str(evaluators) )


####################
#  CHECK FOR BUGS  #
####################
def checkForBugs( parsedResults, eot ) :

  bugEval     = evalTools.bugConditions( parsedResults, eot )
  isBugFree   = bugEval[0]
  explanation = bugEval[1]

  # case this particular iteration is bug-free
  if isBugFree :
    pass

  # case BUG EXISTS!!! *dalek accent* EXTERMINATE! EXTERMINATE!
  else :
    # place magic post processing and visualization code here. =]

    terminateBool = True # True => stop the LDFI Core loop

    # -------------------------------------------- #
    # generate prov graphs of buggy executions.
    #vizTools.generateBuggyProvGraphs( parsedResults, argDict[ "EOT" ], cursor, ITER_COUNT )

  return [ terminateBool, isBugFree, explanation ]


#####################
#  BUILD PROV TREE  #
#####################
# use the evaluation execution results to build a provenance tree of the evaluation execution.
# return a provenance tree instance
def buildProvTree( parsedResults, eot, iter_count, irCursor ) :

  if parsedResults :
    # 000000000000000000000000000000000000000000000000000000000000000000 #
    # grab the set of post records at EOT.
    # assume the right-most attribute/variable/field of the post schema
    # represents the last send time (aka EOT).
    # should be true b/c of the dedalus rewriter reqs for deductive rules.
    postrecords_all = parsedResults[ "post" ]
    postrecords_eot = []
  
    if DEBUG :
      print "postrecords_all = " + str(postrecords_all)
  
    for rec in postrecords_all :
  
      if DEBUG :
        print "rec     = " + str(rec)
        print "rec[-1] = " + str(rec[-1])
        print "eot     = " + str(eot)
  
      # collect eot post records only
      if int( rec[-1] ) == int( eot ) :
        postrecords_eot.append( rec )
  
    if DEBUG :
      print "postrecords_eot = " + str(postrecords_eot)
  
    # !!! RETURN EARLY IF POST CONTAINS NO EOT RECORDS !!!
    if len( postrecords_eot ) < 1 :
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : attempting to build a provenance tree when no post eot records exist. Aborting..." )
 
    # 000000000000000000000000000000000000000000000000000000000000000000 #

  # abort execution if evaluation results not accessible
  else :
    sys.exit( "ERROR: No access to evaluation results.\nAborting..." ) # sanity check

  # ------------------------------------------------------------- #
  # there exist results and eot post records.
  if DEBUG :
    print "\n~~~~ BUILDING PROV TREE ~~~~"

  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #
  # initialize provenance tree structure
  provTreeComplete = ProvTree.ProvTree( "FinalState", parsedResults, irCursor )

  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #
  # populate prov tree
  for seedRecord in postrecords_eot :
    if DEBUG :
      print " ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
      print "           NEW POST RECORD "
      print "seedRecord = " + str( seedRecord )
    newProvTree = provTreeComplete.generateProvTree( "post", seedRecord )
    provTreeComplete.subtrees.append( newProvTree )
  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #

  if OUTPUT_PROV_TREES_ON :
    provTreeComplete.createGraph( None, iter_count )
  # ------------------------------------------------------------- #

  return provTreeComplete


#################
#  TREE TO CNF  #
#################
# input a provenance tree instance
# output a cnf formula instance
def tree_to_CNF( provTreeComplete ) :

  if DEBUG :
    print "\n~~~~ CONVERTING PROV TREE TO CNF ~~~~"

  provTree_fmla = EncodedProvTree_CNF.EncodedProvTree_CNF( provTreeComplete )

  if provTree_fmla.rawformula :
    print ">>> provTree_fmla.rawformula = " + str( provTree_fmla.rawformula )
    print
    print ">>> provTree_fmla.rawformula.display() = " + str( provTree_fmla.rawformula.display() )
    print
    print ">>> provTree_fmla.cnfformula = " + str( provTree_fmla.cnfformula )
    print

    if OUTPUT_TREE_CNF_ON :
      provTree_fmla.rawformula.graph()

  else :
    tools.bp( __name__, inspect.stack()[0][3], "ERROR: provTree_fmla.rawformula is empty. Aborting execution..." )

  return provTree_fmla


###############
#  SOLVE CNF  #
###############
# input a cnf formula instance
# output a list of fault hypotheses to try during the next LDFI iteration
def solveCNF( provTree_fmla ) :

  finalSolnList = []

  # create a Solver_PYCOSAT insance
  solns = solverTools.solveCNF( "PYCOSAT", provTree_fmla.cnfformula )

  if DEBUG :
    print "***************************"
    print "*    PRINTING ALL SOLNS    "
    print "***************************"

  if solns :
    if DEBUG :
      numid    = 1   # for tracking the current soln number

    # iterate over all solns
    for aSoln in solns.solutions() :

      finalStr = []  # stores the legible version of the soln.
      # make pretty
      for var in aSoln :
        finalStr.append( solverTools.toggle_format_str( var, "legible" ) )

      if DEBUG :
        print "SOLN : " + str(numid) + "\n" + str( finalStr )
        numid += 1

      # add soln to soln list and clear temporary save list for the next iteration
      finalSolnList.append( finalStr )

    # remove duplicates
    tmp = []
    for s in finalSolnList :
      if s : # skip empties
        if not s in tmp :
          tmp.append( s )
    finalSolnList = tmp

  else :
    tools.bp( __name__, inspect.stack()[0][3], "Congratulations! No solutions exist, meaning the solver could not find a counterexample, which means your program is pyLDFI certified. =D\nAborting..." )

  return finalSolnList


##########################
#  GET NEW DATALOG PROG  #
##########################
# input a list of fault hypotheses
# output the path to the new datalog program
def getNewDatalogProg( faultHypoList, irCursor, iter_count ) :

  if len( faultHypoList ) > 0 :
    executionInfo   = newProgGenerationTools.buildNewProg( faultHypoList, irCursor, iter_count )
    newProgSavePath = executionInfo[0]

    return newProgSavePath

  else :
    tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : attempted to build a new datalog program, but no fault hypotheses exist." )


#########
#  EOF  #
#########
