import json

def json_to_obj(json_str,obj_class):
    data = json.loads(json_str.strip('\t\r\n'))
    obj=obj_class()
    obj.__dict__=data
    return obj

def obj_to_json(obj)->str:
    json_str=json.dumps(obj.__dict__)
    return json_str