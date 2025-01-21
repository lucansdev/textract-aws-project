import os
import boto3
import json

file_name = os.path.abspath("images\cnh.jpg")

def get_document(file_name:str)->bytearray:
    with open(file_name,"rb") as file:
        img = file.read()
        doc_bytes = bytearray(img)

    return doc_bytes

def analyze_document(file_path)->None:
    client = boto3.client("textract")
    doc_bytes = get_document(file_path)
    response = client.analyze_document(Document={"Bytes":doc_bytes},FeatureTypes=["SIM"])

    with open("response.json","w") as response_file:
        response_file.write(json.dumps(response))


def get_kv_map():
    key_map = {}
    value_map = {}
    block_map = {}
    blocks = []

    try:
        with open("response.json","r") as file:
            blocks = json.loads(file.read())["Blocks"]
    except IOError:
        analyze_document(file_name)

    for block in blocks:
        block_id = block["Id"]
        block_map[block_id] = block
        if block["BlockType"] == "KEY_VALUE_SET":
            if "KEY" in block["EntityTypes"]:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    return key_map,value_map,block_map


def get_kv_relationship(key_map,value_map,block_map):
    kvs = {}
    for _,key_block in key_map.items():
        value_block = find_valeu_block(key_block,value_map)
        key = get_text(key_block,block_map)
        value = get_text(value_block,block_map)
        kvs[key] = value
    return kvs

def find_valeu_block(key_block,value_map):
    for relationship in key_block.get("Relationships"):
        if relationship["Type"] == "VALUE":
            for value_id in relationship["Ids"]:
                return value_map[value_id]
    return {}

def get_text(result,block_map):
    text = ""
    if "Relationships" in result:
        for relationship in result["Relationships"]:
            if relationship["Type"] =="CHILD":
                for child_id in relationship["Ids"]:
                    word = block_map[child_id]
                    if word["BlockType"] == "WORD":
                        text += word["Text"] + " "
    return text.rstrip()

if __name__ == "__main__":
    key_map,value_map,block_map = get_kv_map()
    kevs = get_kv_relationship(key_map,value_map,block_map)

    for k,v in kevs.items():
        print(f"{k}:{v}")