'''
Created on Dec 8, 2014
@author: joro
'''


import sys
from doitOneRecording import doitOneRecording
from datetime import datetime
import os
from Decoder import logger
from Utilz import getMeanAndStDevError

def doit(argv):
    if len(argv) != 7 and len(argv) != 8:
        print ("usage: {}  <pathRoot <withDurations> <withSynthesis> <ALPHA> <ONLY_MIDDLE_STATE> <evalLevel> <usePersistentFiles=True>".format(argv[0]) )
        sys.exit();
    
    pathRoot = argv[1]
    TEST_DATA = '/turkish-makam-lyrics-2-audio-test-data-synthesis/' 
    pathToScores = pathRoot + TEST_DATA

    
    
    withDuration = argv[2]
    withSynthesis = argv[3]
    
    if withSynthesis=='True':
         pathRecordings = pathRoot + TEST_DATA
    elif withSynthesis == 'False':
        pathRecordings = pathRoot + '/ISTANBUL/'
          
        
    
    ALPHA = argv[4]
    
    
    ONLY_MIDDLE_STATE = argv[5]
    evalLevel = int(argv[6])
    
    usePersistentFiles = 'True'
        
    if len(argv) == 8:
        usePersistentFiles = argv[7]
        

    totalErrors  = [] 

    # old list. with no acapella equivalent.
#         compositionNames = ['nihavent--sarki--curcuna--kimseye_etmem--kemani_sarkis_efendi', \
#         'nihavent--sarki--aksak--gel_guzelim--faiz_kapanci/', \
#         'nihavent--sarki--aksak--gel_guzelim--faiz_kapanci/', \
#         'nihavent--sarki--aksak--koklasam_saclarini--artaki_candan/', \
#         'ussak--sarki--duyek--aksam_oldu_huzunlendim--semahat_ozdenses',\
#         'nihavent--sarki--aksak--bakmiyor_cesm-i--haci_arif_bey',\
#         'ussak--sarki--duyek--aksam_oldu_huzunlendim--semahat_ozdenses', \
#         'segah--sarki--curcuna--olmaz_ilac--haci_arif_bey'
#         ]
#         
#         subpaths = ['/goekhan/', '/goekhan/', '/barbaros/', '/barbaros/', '/safiye/', '/safiye/', '/guelen/', '/guelen/' ]
#         patterns = ['02_Kimseye', '02_Gel', '02_Gel', '02_Koklasam',   '01_Aksam' ,    '01_Bakmiyor', '01_Aksam', '01_Olmaz' ]
#         
    
    
       #############################
#     for a-capella ISTANBUL data 
    compositionNames = [ 
                            'nihavent--sarki--curcuna--kimseye_etmem--kemani_sarkis_efendi', 
                        'nihavent--sarki--duyek--bir_ihtimal--osman_nihat_akin',
                        'ussak--sarki--aksak--bu_aksam_gun--tatyos_efendi', 
                        'segah--sarki--curcuna--olmaz_ilac--haci_arif_bey',
                                'ussak--sarki--duyek--aksam_oldu_huzunlendim--semahat_ozdenses',
                            'nihavent--sarki--aksak--gel_guzelim--faiz_kapanci',
                                'nihavent--sarki--aksak--bakmiyor_cesm-i--haci_arif_bey',
                                'nihavent--sarki--aksak--koklasam_saclarini--artaki_candan',
                        'nihavent--sarki--curcuna--kimseye_etmem--kemani_sarkis_efendi'
                    
                    ]
    
    recordingDirs =  [ 
                       'Melihat_Gulses',
                      '05_Semahat_Ozdenses_-_Bir_Ihtimal_Daha_Var',
                                            'Sakin--Gec--Kalma', 
                      '21_Recep_Birgit_-_Olmaz_Ilac_Sine-i_Sad_Pareme',
                      '06_Semahat_Ozdenses_-_Aksam_Oldu_Huzunlendim',
                      '18_Munir_Nurettin_Selcuk_-_Gel_Guzelim_Camlicaya',
                      '04_Hamiyet_Yuceses_-_Bakmiyor_Cesm-i_Siyah_Feryade',
                      '2-15_Nihavend_Aksak_Sarki',
                      '03_Bekir_Unluataer_-_Kimseye_Etmem_Sikayet_Aglarim_Ben_Halime'
                    
                      ]                          
                     
    
    subpaths = [
                '/idil/', '/idil/', '/idil/', 
                '/guelen/', '/guelen/', '/barbaros/',  '/safiye/','/barbaros/','/goekhan/'    ]
    patterns = [  
                'Melihat_Gulses', '05_Semahat_Ozdenses_-_Bir_Ihtimal_Daha_Var',  'Sakin--Gec--Kalma', 
                '01_Olmaz', '01_Aksam',  '02_Gel', '01_Bakmiyor', '02_Koklasam','02_Kimseye']

             
          
    resultSet = []    

#     for synthesis data 
    for compositionName, recordingDir, pattern, subpath in zip(compositionNames, recordingDirs, patterns, subpaths):
        
        URI_Composition = os.path.join(pathToScores, compositionName)
        
        if withSynthesis=='True':
            URI_Recording =  os.path.join(URI_Composition, recordingDir)
            pattern = recordingDir + '_'
        elif withSynthesis=='False': 
            URI_Recording = pathRecordings + subpath
            pattern = pattern + '_'
        else:
            sys.exit('param WITHSynthesis can be only True or False')

# end of synthesis data

        command = [ 'python', '/Users/joro/Documents/Phd/UPF/voxforge/myScripts/AlignmentDuration/doitOneRecording.py', URI_Composition, URI_Recording, pattern, withDuration, withSynthesis, str(ALPHA), ONLY_MIDDLE_STATE, str(evalLevel), usePersistentFiles]
        commandStr = " ".join(command)
        logger.info("{} ".format(commandStr ))
        
#         continue
        mean, stDev, errorsForRecording  = doitOneRecording([ 'dummy', URI_Composition, URI_Recording, pattern, withDuration, withSynthesis,  ALPHA, ONLY_MIDDLE_STATE, evalLevel, usePersistentFiles])
        totalErrors.extend(errorsForRecording)
        

        
        listLine = " ".join(['\n', str(mean), str(stDev), URI_Recording,  pattern])
        resultSet.append((mean,listLine))
        
        
    sortedResultSet = sortResultSet(resultSet)
    for entry in sortedResultSet:
        print str(entry[0]) +", "
    writeResultToFile(sortedResultSet,  totalErrors, ALPHA)
        
    
def sortResultSet(resultSet):
    from operator import itemgetter
    return sorted(resultSet,key=itemgetter(0))

def writeResultToFile(resultSet,  totalErrors, ALPHA):
    
    currTime = datetime.now().strftime('%Y-%m-%d--%H-%M-%S')    
    filename = os.path.join(os.getcwdu(),   'alignError_' + currTime + '.out') 
    outputFileHandle = open(filename, 'a')
    
    logger.info("\n Output file is: " + filename )
    
    
    outputFileHandle.write('\n'  + str(ALPHA) )
    
    for mean, listLine in resultSet:
        if outputFileHandle.closed:
            outputFileHandle = open(filename, 'a')
        outputFileHandle.write(listLine)
        outputFileHandle.close()
    
         
    # total mean    
    mean, stDev, median  = getMeanAndStDevError(totalErrors)
    result = '\n' + 'total mean: ' + str(mean) + '\n'
    
    logger.info( result  )
    
    if outputFileHandle.closed:
        outputFileHandle = open(filename, 'a')
    outputFileHandle.write(result)
    
    outputFileHandle.close()
    print 'written to file ' + filename 
    
    
    
if __name__ == '__main__':
    doit(sys.argv)