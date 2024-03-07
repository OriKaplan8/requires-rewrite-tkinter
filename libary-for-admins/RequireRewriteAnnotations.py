from pymongo import MongoClient
import pandas as pd
connection_string = "mongodb+srv://orik:Ori121322@cluster0.tyiy3mk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(connection_string)
db = client.require_rewrite

#For checking if stuff exists
def checkAnnotatorNameExists(annotatorName):
    collection = db.annotators
    query = {"username":annotatorName}
    if collection.find_one(query):
        return True
    else:
        return False
    
def getAnnotatorUserCode(annotatorName):

    if not checkAnnotatorNameExists(annotatorName):
        raise Exception(f"Cannot get UserCode because Annotator {annotatorName} not found in database")
    
    else:
        collection = db.annotators
        query = {"username":annotatorName}
        response = collection.find_one(query)
        return response['usercode']

#Commands to get other stuff from the Database
def getAllAnnotatorsNames():
    collection = db.annotators
    annotatorNames = []
    
    documents = collection.find()
    
    for document in documents:
        annotatorName = document.get("username")
        if annotatorName:
            annotatorNames.append(annotatorName)
            
    if (len(annotatorNames) == 0):
        raise Exception("No annotators in collection or field 'username' doesnt exists") 
            
    return annotatorNames

def getAllAnnotatorsCodes():
    collection = db.annotators
    annotatorCodes = []
    
    documents = collection.find()
    
    for document in documents:
        annotatorCode = document.get("usercode")
        if annotatorCode:
            annotatorCodes.append(annotatorCode)
            
    if (len(annotatorCodes) == 0):
        raise Exception("No annotators in collection or field 'username' doesnt exists") 
            
    return annotatorCodes

#Commands to get annotations from the Database
def getBatchByAnnotatorNameAndBatchNum(annotatorName, batchNum):

    if not checkAnnotatorNameExists(annotatorName):
        raise Exception(f"Annotator {annotatorName} not found in database")

    collection = db.json_annotations
    response = collection.find_one({ "usercode":getAnnotatorUserCode(annotatorName), "batch_id": batchNum})
    if response == None:
        raise Exception(f"Found user {annotatorName}, But cannot find his Batch_{batchNum}")
    else:
        return response['json_string']

def getBatchByAnnotatorNameAndBatchNumDataframe(annotatorName, batchNum):

    if not checkAnnotatorNameExists(annotatorName):
        raise Exception(f"Annotator {annotatorName} not found in database")

    collection = db.json_annotations
    response = collection.find_one({ "usercode":getAnnotatorUserCode(annotatorName), "batch_id": batchNum})
    if response == None:
        raise Exception(f"Found user {annotatorName}, But cannot find his Batch_{batchNum}")
    else:
        return jsonToDataframe(response['json_string'])
    
def getAllBatchesByAnnotator(annotatorName):

    if not checkAnnotatorNameExists(annotatorName):
        raise Exception(f"Annotator {annotatorName} not found in database")

    collection = db.json_annotations

    response = collection.find({ "usercode":getAnnotatorUserCode(annotatorName)})
    if response == None:
        raise Exception(f"0 Batches under the annotator {annotatorName} were found")
    else:
        annotatorBatches =  list(response)
        return annotatorBatches
    
def getAllBatchesByAnnotatorCode(annotatorCode):

    collection = db.json_annotations

    response = collection.find({ "usercode": annotatorCode})
    if response == None:
        raise Exception(f"0 Batches under the annotator {annotatorCode} were found")
    else:
        annotatorBatches =  list(response)
        return annotatorBatches
    
def getAllBatchesByAnnotatorNameDataFrame(annotatorName):

    if not checkAnnotatorNameExists(annotatorName):
        raise Exception(f"Annotator {annotatorName} not found in database")

    collection = db.json_annotations

    response = collection.find({ "usercode":getAnnotatorUserCode(annotatorName)})
    if response == None:
        raise Exception(f"0 Batches under the annotator {annotatorName} were found")
    else:
        annotatorBatches =  list(response)
        BatchesDataframe = pd.DataFrame()
        for batch in annotatorBatches:
            BatchesDataframe = pd.concat([BatchesDataframe, jsonToDataframe(batch['json_string'])])
        return BatchesDataframe

def getAllAnnotations():
    annotatorCodes = getAllAnnotatorsCodes()
    allAnnotatorsBatches = []
    
    for annotatorCode in annotatorCodes:
        annotatorBatches = getAllBatchesByAnnotatorCode(annotatorCode)
        if annotatorBatches:
            allAnnotatorsBatches.extend(annotatorBatches)
            
    if (len(allAnnotatorsBatches) == 0):
        raise Exception("There are no batches.")
            
    return allAnnotatorsBatches
        
def getAllAnnotationsDataframe():
    annotatorCodes = getAllAnnotatorsCodes()
    allAnnotatorsBatches = []
    
    for annotatorCode in annotatorCodes:
        annotatorBatches = getAllBatchesByAnnotatorCode(annotatorCode)
        if annotatorBatches:
            allAnnotatorsBatches.extend(annotatorBatches)
            
    if (len(allAnnotatorsBatches) == 0):
        raise Exception("There are no batches.")
            
    BatchesDataframe = pd.DataFrame()
    for batch in allAnnotatorsBatches:
        BatchesDataframe = pd.concat([BatchesDataframe, jsonToDataframe(batch['json_string'])])
            
    return BatchesDataframe
        
#Coverts a Json to a Dataframe
def jsonToDataframe(json_string):
    rows = []
    
    for dialog_id, dialog_data in json_string.items():
        for turn_index, turn_data in enumerate(dialog_data['dialog']):
            if (turn_index == 0): continue

            row = {
                "AnnotatorName": dialog_data['annotator_name'],
                "DialogID": dialog_id,
                "TurnNum": turn_index,
                "OgQuestion": turn_data['original_question'],
                "RequiresRewrite": dialog_data['annotations'][turn_index-1]['requires rewrite']
            }

            # Append the row to the list
            rows.append(row)

     # Convert the list of rows to a DataFrame
    AnnotationDF = pd.DataFrame(rows, columns=["AnnotatorName", "DialogID", "TurnNum", "OgQuestion", "RequiresRewrite"])
    
    return AnnotationDF

