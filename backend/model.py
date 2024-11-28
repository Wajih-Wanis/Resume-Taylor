from abc import ABC,abstractmethod
from langchain_community.llms.ollama import Ollama
from langchain_openai import ChatOpenAI

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

    def __init__(self,model="gpt-4o"):
        self.model = ChatOpenAI(model)

    def _run(self,input) -> str:
        response = self.model.invoke(input)
        return response["content"]