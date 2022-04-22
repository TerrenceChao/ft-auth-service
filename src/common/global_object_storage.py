import io
import os
import json
import boto3
import logging


FT_BUCKET = os.getenv("FT_BUCKET", "foreign-teacher")


s3 = boto3.resource("s3")


log = logging.getLogger()
log.setLevel(logging.ERROR)


class GlobalObjectStorage:
    def __init__(self, s3):
        self.s3 = s3

    def init(self, bucket, version):
        err: str = None
        try:
            file = json.dumps({ "version": version })
            key = ''.join([str(bucket), '/email_info.json'])
            object = self.s3.Object(FT_BUCKET, key)
            object.put(Body=file)

            return version, err
        
        except Exception as e:
            err = e.__str__()
            log.error(err)
            
        return version, err
    

    def update(self, bucket, version, newdata):
        err: str = None
        result = None
        try:
            data, err = self.find(bucket)
            if err:
                return result, err
            
            if "version" in data and data["version"] != version:
                return result, "no version there OR invalid version"
            
            data.update(newdata)
            result = json.dumps(data)
            
            key = ''.join([str(bucket), '/email_info.json'])
            object = self.s3.Object(FT_BUCKET, key)
            object.put(Body=result)
        
        except Exception as e:
            err = e.__str__()
            log.error(err)
            
        return result, err
    
    def delete(self, bucket):
        err: str = None
        result = False
        try:
            key = ''.join([str(bucket), '/email_info.json'])
            self.s3.Object(FT_BUCKET, key).delete()
            result = True
        
        except Exception as e:
            err = e.__str__()
            log.error(err)
            
        return result, err

    """
        return {
            "email": "abc@gmail.com",
            "region": "jp",
        }, None
    """
    def find(self, bucket):
        err: str = None
        result = None
        try:
            key = ''.join([str(bucket), '/email_info.json'])
            object = self.s3.Object(FT_BUCKET, key)

            file_stream = io.BytesIO()
            object.download_fileobj(file_stream)
            file_stream.seek(0)
            string = file_stream.read().decode('utf-8')
            result = json.loads(string)
        
        except Exception as e:
            err = e.__str__()
            log.error(err)
            if  "404" in err and "Not Found" in err:
                err = None
            
        return result, err




def get_global_object_storage():
    storage = GlobalObjectStorage(s3)
    try:
        yield storage
    except Exception as e:
        log.error(e.__str__())
        raise
    finally:
        pass
