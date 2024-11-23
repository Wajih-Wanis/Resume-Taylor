from pypdf import PdfReader


class ResumeReader:

    def __init__(self,resume_path):
        self.resume_path = resume_path

    
    def read_resume_pdf(self) -> str:
        reader = PdfReader(self.resume_path)
        content = ""
        for page in reader.pages:
            content+=page.extract_text()
        return content
    