'''
Created on Feb 11, 2016

@author: joro
'''
import json
import sys
from align.ScoreSection import ScoreSection
from MakamRecordingOld import MakamRecordingOld
from scripts.MakamScoreOld import loadMakamScore
import os
from scripts.fetchSymbTrFromGithub10SarkiTestDataset import fetchFileFromURL
# from align.RecordingSegmenter import getURISectionAnnotation

parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0]) ), os.path.pardir, os.path.pardir)) 
pathUtils = os.path.join(parentDir, 'pycompmusic') 
if pathUtils not in sys.path:
    sys.path.append(pathUtils)

import compmusic    
from compmusic import dunya
from compmusic.extractors.makam.lyricsalign import recMBIDs, get_section_metadata_dict

from utilsLyrics.Utilz import  findFileByExtensions
'''
1. take section annotaitons with old section names from annotations for ISTANBUL. match with old section_metadata using MakamRecording to create pointers to sections
2. take section metadaata with new names from dunya. 
3. prove that number of new metadata section names is consistent with number of old section names
4. replace pointers to sections with new section names (if section annotaions from sertan's jnmr dataset present take it else take section annotations from ISTANBUL )
 
'''
pathSectionAnnosSourceJNMR = '/Users/joro/Downloads/turkish_makam_section_dataset-2014_jnmr/audio_metadata/'


URI_datasetSymbTr1 = '/Users/joro/Documents/Phd/UPF/turkish-for_makam-lyrics-2-audio-test-data-synthesis/'

# manually modified note numbers in section.tsv file and with symbTr 2.0 .txt 
URI_datasetSymbTr1_sectionMeta2 = '/Users/joro/Downloads/turkish-for_makam-lyrics-2-audio-test-data-synthesis-symbTr2/'


dunya.set_token("69ed3d824c4c41f59f0bc853f696a7dd80707779")






def create_new_metadata_2nd_lyrics(musicbrainzid, workmbid):
    '''
    generate sections metadata 
    with melodic_struct
    and lyric_struct
    for  lyrics with updated 2nd verse
    '''
    
    URI_datasetSymbTr1_sectionMeta2 = '/Users/joro/Documents/ISTANBULSymbTr2/'
    symbtrtxtURI, symbTrCompositionName  = constructSymbTrTxtURI(URI_datasetSymbTr1_sectionMeta2, musicbrainzid, workmbid)
    workmbid = 'dummy'
    #     segment_note_bound_idx_for_symbTr2  = generateListStartEndNoteNumbers(makamScore_sectionMeta2) ### could not make it work
    segment_note_bound_idx_for_symbTr2 = None
    sectionsMetadataNewLabels, sectionsMetadataNewLabelsDict = generateSectionsMetadata(workmbid, symbTrCompositionName, symbtrtxtURI, segment_note_bound_idx_for_symbTr2)   
    return sectionsMetadataNewLabelsDict



def extendNewMetadata(musicbrainzid, workmbid,  inpuRecordingDir):
    '''
    annotations with score sections names zemin meyan > convert to > annotations with sections names C1, B1. etc
    uses old makamScore and makamRecording (and SymbTrParser old ) because we need the matchSections and its neater to use it form the constructor of MakamRecording
    '''
    
    symbtrtxtURI, symbTrCompositionName  = constructSymbTrTxtURI(URI_datasetSymbTr1_sectionMeta2, workmbid)
    
    #############  0. modify indices   
    raw_input("modify indices to correpond to symbTr v.2 with but same sections as in old section metadata. \n name new file {}/{}.sections.json ".format(URI_datasetSymbTr1_sectionMeta2, symbTrCompositionName) )
    
    ############## 1. create score section Metadata new labels form old annotation with symbTr v.1
    
    compositionPath = URI_datasetSymbTr1_sectionMeta2 + symbTrCompositionName + '/'
    makamScore_sectionMeta2 = loadMakamScore(compositionPath)
    segment_note_bound_idx_for_symbTr2  = generateListStartEndNoteNumbers(makamScore_sectionMeta2)
    sectionsMetadataNewLabels, sectionsMetadataNewLabelsDict = generateSectionsMetadata(workmbid, symbTrCompositionName, symbtrtxtURI, segment_note_bound_idx_for_symbTr2)   

    
    #############  2. load old section annotation 
    #load old score section metadata with meyan etc. names and section annotation in json 
    compositionPath = URI_datasetSymbTr1 + symbTrCompositionName + '/'
    oldMetadataMakamScore = loadMakamScore(compositionPath)
    
    if len(sectionsMetadataNewLabels) != len(oldMetadataMakamScore.sectionToLyricsMap):
        sys.exit("for composition {} text score sections are {} and sectionsMetadata with new labels are {}".format(compositionPath, len(oldMetadataMakamScore.sectionToLyricsMap), len(sectionsMetadataNewLabels)))
        
    ######### 3.   match old score sections to audio annotations (in constructor of for_makam recording)
    pathToAudioFile = 'blah'
    pathToRecording, pathToSectionAnnotations = getURISectionAnnotation(inpuRecordingDir, compositionPath) 
    makamRecording = MakamRecordingOld(oldMetadataMakamScore, pathToAudioFile, pathToSectionAnnotations)
#     print makamRecording.sectionIndices
        
    
        ######## ### 4.  load  section annos,  add new labels 
    sectionAnnosSourceURI = pathSectionAnnosSourceJNMR + musicbrainzid + '.json'
    if not os.path.isfile(sectionAnnosSourceURI):
        print 'no section annotaion in JNMR dataset. all fields in final json except for field section_annotaitons will be empty'
        sectionAnnosDict = {}
        sections = replaceSecionsWithNewLabels_GeorgisAnnotations(sectionsMetadataNewLabels, makamRecording)
    else:
        with open(sectionAnnosSourceURI) as f:
             sectionAnnosDict = json.load(f)
        sections = replaceSectionsWIthNewLabesJNMR(sectionsMetadataNewLabels, sectionAnnosSourceURI, sectionAnnosDict, pathToSectionAnnotations, makamRecording)

                 
        
    
    sectionAnnosDict['section_annotations'] = sections
    
    return sectionsMetadataNewLabelsDict, sectionAnnosDict 
    
    


    
    
def replaceSectionsWIthNewLabesJNMR(scoreSectionsNewLables, sectionAnnosSourceURI, sectionAnnosDict, pathToSectionAnnotations, makamRecording):
    '''
    extend sectionsAnnos with JNMR
    '''
    if 'section_annotations' not in sectionAnnosDict:
                     sys.exit('annotation should have key section_annotations')
    sectionsAnnos = sectionAnnosDict['section_annotations']
    
    # sanity check
    if len(sectionsAnnos) != len(makamRecording.sectionIndices):
        sys.exit(" annotation local in \n {} \n has length  {} whereas annotation json \n {} \n has length {}. Rewrite code with only json".format(pathToSectionAnnotations, len(makamRecording.sectionIndices), sectionAnnosSourceURI, len(sectionsAnnos) ))
    
    for sectionAnnoTxt, sectionIdx in zip(sectionsAnnos, makamRecording.sectionIndices):
        if sectionIdx != -1:
            if sectionIdx > len(scoreSectionsNewLables): # done for        '06_Semahat_Ozdenses_-_Aksam_Oldu_Huzunlendim',
                sys.exit('more sectionsAnnos matched that they are in sectiona metadata')
            melStruct = scoreSectionsNewLables[sectionIdx].melodicStructure
            lyricStruct = scoreSectionsNewLables[sectionIdx].lyricStructure
        else:
            melStruct = ''
            lyricStruct = ''
        sectionAnnoTxt['melodicStructure'] = melStruct
        sectionAnnoTxt['lyricStructure'] = lyricStruct
    
    return sectionsAnnos
 
 

def generateSectionsMetadata(workmbid, symbTrCompositionName, symbtrtxtURI, segment_note_bound_idx):
    ###### 2. load score sections metadata new C1,C2 etc.
    
#     sectionMetadataAllDict = dunya.docserver.get_document_as_json(workmbid, "metadata", "metadata", 1, version="0.1") #     print sectionMetadataAllDict
    
        
    ####### INSTEAD: for sections with no second verse section metadata is wrong, so generate it with symbtr with correct lyrics 
    from symbtrdataextractor.SymbTrDataExtractor import SymbTrDataExtractor
    
    extractor = SymbTrDataExtractor(extract_all_labels=False, melody_sim_thres=0.75, 
                                lyrics_sim_thres=0.75, get_recording_rels=False,
                                print_warnings=True)
 
    
    sectionMetadataAllDict, isDataValid = extractor.extract(symbtrtxtURI, segment_note_bound_idx=segment_note_bound_idx)

    
    
    ##### use sertans scoreMetadata directly
#     sectionMetadataAllDict = get_section_metadata_dict(workmbid, 'dummy', '/Users/joro/Downloads/', 0)
    
    if  'segmentations' in sectionMetadataAllDict: # use segmentations instead of sections, if no segmentations, use sections 
         scoreSectionAnnos = sectionMetadataAllDict['segmentations'] # if with_section_annotations, it is called segmentations because of symbtrdataextractor
    elif 'sections' in sectionMetadataAllDict:
        scoreSectionAnnos = sectionMetadataAllDict['sections']
    else:
        sys.exit("cannot find neither key sections nor segmentations in score metadata" )    
    
    sectionsMetadataNewLabels = []
    for section in scoreSectionAnnos:
#                     print section
        sectionNew = ScoreSection(section['name'], int(section['start_note']), int(section['end_note']), section['melodic_structure'], section['lyric_structure'])
        sectionsMetadataNewLabels.append(sectionNew)
    
    return sectionsMetadataNewLabels, sectionMetadataAllDict
   
  
def generateListStartEndNoteNumbers(makamScore_sectionMeta2):
    segment_note_bound_idx  = []
    for e in makamScore_sectionMeta2.sectionToLyricsMap:
        segment_note_bound_idx.append( e[1] )
    segment_note_bound_idx = segment_note_bound_idx[1:]
    
    return segment_note_bound_idx
    
def constructSymbTrTxtURI(URI_dataset, workMBID):
    '''
    URI on local machine of symbTr queried by workMBID 
    '''
    symbtr = compmusic.dunya.makam.get_symbtr(workMBID)
    symbTrCompositionName = symbtr['name']
    
    compositionPath = URI_dataset + symbTrCompositionName + '/'
    symbtrtxtURI = compositionPath + symbTrCompositionName + '.txt'
    
    return symbtrtxtURI,  symbTrCompositionName


def getURISectionAnnotation(recordingDir, pathToComposition):
    pathToRecording = os.path.join(pathToComposition, recordingDir)
    os.chdir(pathToRecording)
#         pathToSectionAnnotations = os.path.join(pathToRecording, glob.glob('*.sectionAnno.txt')[0]) #             pathToAudio =  os.path.join(pathToRecording, glob.glob('*.wav')[0])
    listExtensions = ["sectionAnno.json", "sectionAnno.txt", "sectionAnno.tsv"]
    sectionAnnoFiles = findFileByExtensions(pathToRecording, listExtensions)
    if len(sectionAnnoFiles) == 0:
        sys.exit("no sectionAnno file in dir {}".format(pathToRecording))
    pathToSectionAnnotations = os.path.join(pathToRecording, sectionAnnoFiles[0])
    return pathToRecording, pathToSectionAnnotations


def replaceSecionsWithNewLabels_GeorgisAnnotations(sectionsMetadataNewLabels, makamRecording):
    # if no section annos in pathSectionAnnosSourceJNMR. because for some recordings there are no annotations in JNMR dataset
    sections = []
    for i, idx in enumerate(makamRecording.sectionIndices):
        currSection = {}
        currSection['time'] = [makamRecording.beginTs[i], makamRecording.endTs[i]]
        currSection['time_unit'] = 'sec'
        currSection['name'] = makamRecording.sectionNamesSequence[i]
        if idx != -1:
            melStruct = sectionsMetadataNewLabels[idx].melodicStructure
            lyrStruct = sectionsMetadataNewLabels[idx].lyricStructure
        else:
            melStruct = ''
            lyrStruct = ''
        currSection['melodicStructure'] = melStruct
        currSection['lyricStructure'] = lyrStruct
        sections.append(currSection)
    
    return sections

def write_results_as_json(sectionsMetadataNewLabelsDict, workid, sectionAnnosDict, musicbrainzid, pathSectionAnnosDestination):
    

    URI =  pathSectionAnnosDestination + '/scores/metadata/' + workid  + '.json'
    print "wirting file \n {} \n dont forget to upload it to http://githubusercontent.com/georgid/turkish_makam_section_dataset/master/scores/metadata".format( URI)

    with open(URI, 'w') as f: 
        json.dump(sectionsMetadataNewLabelsDict, f, indent=4)
    
    ##### OUTPUT 2: write edited sectionAnnos
    sectionAnnosURIEdited = pathSectionAnnosDestination + '/audio_metadata/' + musicbrainzid  + '.json'
    print "wirting file \n{} \n dont forget to upload it to http://githubusercontent.com/georgid/turkish_makam_section_dataset/master/audio_metadata/".format( sectionAnnosURIEdited)
    with open(sectionAnnosURIEdited, 'w') as f8:
        json.dump( sectionAnnosDict, f8, indent=4)
        
        


if __name__ == '__main__':
    
    pathSectionAnnosDestination = '/Users/joro/Documents/Phd/UPF/turkish_makam_section_dataset/'
    

    for musicbrainzid in recMBIDs:
        rec_data = dunya.makam.get_recording(musicbrainzid )
        workmbid = rec_data['works'][0]['mbid']
        recordingDir = recMBIDs[musicbrainzid][0]
        sectionsMetadataNewLabelsDict, sectionAnnosDict = extendNewMetadata(musicbrainzid, workmbid, recordingDir )
        write_results_as_json(sectionsMetadataNewLabelsDict, workmbid, sectionAnnosDict, musicbrainzid, pathSectionAnnosDestination) 
        raw_input("press for next piece...")
