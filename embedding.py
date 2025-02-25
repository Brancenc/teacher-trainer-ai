# Instructions for Use

# 1. Open Terminal
# 2. If python is not installed, install python
# 3. Install pip (required for packages)    
# 4. Using pip install tiktoken PyPDF2 PyQt5
    # - Type $ pip3 install pdfplumber tiktoken PyPDF2 PyQt5 or 
    # $ pip install pdfplumber tiktoken PyPDF2 PyQt5
# 5. Once all installed, change directory to where this script exists on computer
# 6. Type $ python3 embedding.py
# 7. Drag files into box to generate vector embedding

# NOTE: Current script does not do anything with the vector embeddings. 



import os
import json
import csv
import PyPDF2
import numpy as np      
import tiktoken         # Token library developed by OpenAI


# Libraries for GUI window
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt

TOKEN_SIZE = 512    # Token size for embedding
                    # NOTE: Small files will not use 512 token shape

class DragDropWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag and Drop File Input")
        self.resize(400, 200)
        self.setAcceptDrops(True)
        
        self.label = QLabel("Drag and drop a file here", self)
        self.label.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.data_processor = Data()
        self.vector_store = []

    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # Files are processed here
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            self.label.setText(f"Processing: {file_path}")
            embedding = self.data_processor.extract_features_from_file(file_path)

            if embedding is not None:
                self.label.setText(f"{file_path} Embedding shape: {embedding.shape}")
                self.vector_store.append(embedding)
                print("NEW FILE\n")
                print(self.vector_store)
            else:
                self.label.setText("Unsupported file format or extraction failed.")
        




class Data:
    def __init__(self):
        pass

    def _get_text_embedding(self, text):
        """Convert text into token-based embedding using tiktoken."""
        # Tiktoken is a tokenizer library developed by open AI
        # "cl100k_base" is a specific tokenizer model used by OpenAI’s latest GPT models
        encoder = tiktoken.get_encoding("cl100k_base")  
        tokens = encoder.encode(text)
        return np.array(tokens[:TOKEN_SIZE])  

    def _extract_text_from_pdf(self, pdf_file):
        with open(pdf_file, 'rb') as pdf:
            reader = PyPDF2.PdfReader(pdf, strict = False)
            pdf_text = ""
            
            for page in reader.pages:
                content = page.extract_text()
                pdf_text += content
            return pdf_text

    def _extract_text_from_file(self, file_path):
        """Extract text from various file formats."""
        ext = os.path.splitext(file_path)[-1].lower()
        
        if ext in ['.txt', '.html']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                return '\n'.join([', '.join(row) for row in reader])
        
        elif ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.dumps(json.load(f))
        
        elif ext == '.pdf':
            return self._extract_text_from_pdf(file_path)
            
        return None


    def extract_features_from_file(self, file_path):
        """Extract features based on file type and return an embedding."""
        text = self._extract_text_from_file(file_path)
        if text:
            return self._get_text_embedding(text)
        
        return None

def main():
    app = QApplication([])
    window = DragDropWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()

