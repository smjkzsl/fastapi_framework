from typing import Dict

import uuid
import  json 
from fastapi import Request,Response
from cryptography.fernet import Fernet
import hashlib,base64 
class SessionStorage():
    key : str=""

    def __init__(self,k:str="") -> None: 
        self.key = base64.urlsafe_b64encode(hashlib.sha256(k.encode()).digest()) 
        super().__init__()
     
    def get(self, session_id: str) -> Dict:
        raise NotImplementedError
        pass 
    def set(self, session_id: str, data: Dict) -> None:
        raise NotImplementedError 
    def delete(self, session_id: str) -> None:
        raise NotImplementedError
    def _encrypt(self, data: Dict) -> bytes:
        data_str = json.dumps(data).encode()
        f = Fernet(self.key)
        encrypted_data = f.encrypt(data_str)
        return encrypted_data 
    def _decrypt(self, data: bytes) -> Dict:
        f = Fernet(self.key)
        decrypted_data = f.decrypt(data)
        data_str = decrypted_data.decode()
        data_dict = json.loads(data_str)
        return data_dict    

class MemoryStorage(SessionStorage):
    def __init__(self):
        self.sessions = {}

    def get(self, session_id: str) -> Dict:
        return self.sessions.get(session_id, {})

    def set(self, session_id: str, data: Dict) -> None:
        self.sessions[session_id] = data

    def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

import os
class FileStorage(SessionStorage):
    filename:str = ""
    def __init__(self, dir: str, key: str=""):
        
        super().__init__(key)
        self._dir = dir
        
        if not os.path.exists(dir):
            os.mkdir(dir)

    def ensure_file_exists(self,sid ):
        filename = os.path.join(self._dir , sid)
        if not os.path.exists(filename):
            with open(filename,"w") as file:
                file.write("")
        return filename
 
     
    def get(self, session_id: str) -> Dict:
        filename = self.ensure_file_exists(session_id)
        try:
            with open(filename, "rb") as f:
                encrypted_data = f.read()
            data = self._decrypt(encrypted_data)
        except FileNotFoundError:
            data = {}
        except Exception as e:
            print(e)
            data = {}
        return data

    def set(self, session_id: str, data: Dict) -> None:
        filename = self.ensure_file_exists(session_id)
        encrypted_data = self._encrypt(data)
        with open(filename, "wb") as f:
            f.write(encrypted_data)

    def delete(self, session_id: str) -> None:
        filename = self.ensure_file_exists(session_id)
        try:
            os.remove(filename)
        except Exception as e:
            print(e)
        

try:
    import redis
    class RedisStorage(SessionStorage):
        def __init__(self, host: str, port: int, password: str, db: int): 
            self.redis_client = redis.Redis(host=host, port=port, password=password, db=db)

        def get(self, session_id: str) -> Dict:
            data = self.redis_client.get(session_id)
            if data is None:
                return {}
            return json.loads(data)

        def set(self, session_id: str, data: Dict) -> None:
            self.redis_client.set(session_id, json.dumps(data))

        def delete(self, session_id: str) -> None:
            self.redis_client.delete(session_id)
except(ImportError):
    pass

from datetime import datetime
class Session(): 
    _storage:SessionStorage = None
    _sid:str = ""

    _data : Dict[str,object] = {}
    @property
    def sid(self):
        return self._sid
    def __init__(self,sid:str="",storage: SessionStorage=None) -> None:
        self._storage = storage
        self._sid = sid or str(uuid.uuid4())
        self._data = storage.get(self._sid) or {}
        pass
    def __getitem__(self,item):
        if item in self._data :
            value = self._data[item]
        else: 
            value = None

        if not value:
            data = self._storage.get(self._sid)
            if data and hasattr(data,item):
                value = data[item] 
        return value
    def __setitem__(self,item,value):
        self._data[item] = value
        self._storage.set(self._sid,self._data)
    def __len__(self):
        return len(self._data)
    
    def get(self,item):
        return self.__getitem__(item)
    def set(self,item,value):
        return self.__setitem__(item,value)
    def clear(self):
        self._storage.delete(self._sid)
class SessionManager( ):
    #session:Session = None
    def __init__(self , storage: SessionStorage ,expires: int = None,): 
        self.storage = storage
        self.expires = expires  
         
    @property
    def is_expired(self):
        if self.expires is None:
            return False
        return datetime.utcnow() > self.expires
    
    async def delete_session(self, session_id: str):
        self.storage.delete(session_id) 
     
    async def initSession(self, request: Request,response:Response ):  
        print(f"dispatch on SessionManager")
        session:Session=None
        sid = request.cookies.get("session_id")
        session = Session( sid,self.storage) 
        return session
        # response = await call_next(request) 
        connect_stop = await request.is_disconnected() 
        if connect_stop:
            session.clear()
    async def process(self,session:Session,response:Response): 
        response.set_cookie(
                    key="session_id",
                    value=session.sid,
                    max_age=1800,
                    httponly=True,
                    secure=True,
                    samesite="Lax",
                )
        
        

 



 
