from abc import ABC,abstractmethod
from langchain_community.llms.ollama import Ollama


class Model(ABC):
    
    #Model call abstraction
    @abstractmethod
    def _run(self):
        pass



class OssModel(Model):

    def __init__(self,model="llama3"):
        self.model = Ollama(model=model) 
    

    def _run(self,input) -> str :
        return self.model.invoke(input)


class Openai(Model):

    def __init__(self):
        pass 

    def _run(self,input) -> str:
        pass 