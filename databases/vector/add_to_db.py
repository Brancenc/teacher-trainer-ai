import warnings

# Suppress all warnings
warnings.filterwarnings('ignore')

# Library for sqlite database
try:
    import sqlite3
except ImportError as e:
    print(f"Error importing sqlite3: {e}")

# Libraries for file extraction
try:
    import os
    import json
    import csv
    import PyPDF2
except ImportError as e:
    print(f"Error importing file extraction libraries: {e}")

# Libraries for data embeddings and chunking
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    import pickle
except ImportError as e:
    print(f"Error importing data embeddings and chunking libraries: {e}")

# Libraries for GUI window
try:
    from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QInputDialog
    from PyQt5.QtGui import QDragEnterEvent, QDropEvent
    from PyQt5.QtCore import Qt
except ImportError as e:
    print(f"Error importing PyQt5 libraries: {e}")

from viewer import Viewer
viewer = Viewer()

db_name = "vector_db.sqlite"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

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
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    # Files are processed here
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            self.label.setText(f"Processing: {file_path}")
            
            result = self.data_processor._process_file(file_path)
            if result:  # Text to be processed
                # Prompt User for Category
                category, ok1 = QInputDialog.getText(self, "Category Input", "Enter Category (e.g., classroom-management, curriculum, personality):")
                if not ok1 or not category:
                    self.label.setText("Category input cancelled. Process aborted.")
                    return

                # Prompt User For Content Type (in metadata)
                content_type, ok2 = QInputDialog.getText(self, "Content Type Input", "Enter Content Type (e.g., article, video-transcript, assignment):")
                if not ok2 or not content_type:
                    self.label.setText("Content type input cancelled. Process aborted.")
                    return

                metadata = {
                    "source": os.path.basename(file_path),
                    "file_type": os.path.splitext(file_path)[1][1:],
                    "content_type": content_type
                }
                json_string = json.dumps(metadata)

                self.data_processor.store_in_db(result[0], result[1], json_string, category)  # results[0] chunks, results[1] vectorized_chunks
                self.label.setText(f"Added to Database: {os.path.basename(file_path)}\n Drag and drop another file")
                # amount = len(result[1])
                # viewer.show_rows(amount)
                # viewer.count_rows()

            else: # No text extracted, failure
                self.label.setText("Unsupported file format or extraction failed.")
        event.accept()

class Data:
    def __init__(self, path = db_name):
        """Initialize Data Object"""
        self.db_path = path
  

    def _connect(self):
        """Establishes connection to database"""
        return sqlite3.connect(self.db_path, timeout=10)


    def chunk_documents(self, text):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = CHUNK_SIZE, chunk_overlap = CHUNK_OVERLAP)
        chunks = text_splitter.split_text(text)
        return chunks
    
    def _vectorize_text_chunks(self, chunks):
        vectorized_chunks = []
        embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        for chunk in chunks:
            vector = embedder.embed_query(chunk)
            vectorized_chunks.append(vector)

        return vectorized_chunks
    
    def store_in_db(self, chunks, vectorized_chunks, met, cate):
        """Stores text chunks and their embedings into the database"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                for chunk, vector in zip(chunks, vectorized_chunks):
                    cursor.execute('''
                        INSERT INTO chunks (text, metadata, category)
                        VALUES (?, ?, ?)
                        ''', (chunk, met, cate))
                    
                    chunk_id = cursor.lastrowid
                    vector_blob = pickle.dumps(vector)
                    # print(chunk_id)
                    cursor.execute('''
                        INSERT INTO embeddings (chunk_id, vector)
                        VALUES (?, ?)
                        ''', (chunk_id, vector_blob))
                    
                conn.commit()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error: {e}") 

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
    
    def _process_file(self, file_path):
        """Extracts features based on file type and stores embeddings into database"""
        # 1. Extract text from file
        text = self._extract_text_from_file(file_path)
        # 2. 
        if not text: 
            return None
        
        chunks = self.chunk_documents(text)
        vectorized_chunks = self._vectorize_text_chunks(chunks)
        return chunks, vectorized_chunks

def main():
    # Code to launch application
    app = QApplication([])
    window = DragDropWindow()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()