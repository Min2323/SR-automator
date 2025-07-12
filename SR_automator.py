import sys
from datetime import datetime
from qtpy.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QProgressBar,
    QMessageBox,
)
from qtpy.QtCore import Qt, QThread, Signal, QTimer
from qtpy.QtGui import QDragEnterEvent, QDropEvent


class DragDropLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setText('Drag and Drop File Here')
        self.setStyleSheet("QLabel { background-color : lightgray; }")
        self.setFixedHeight(100)
        self.setAlignment(Qt.AlignCenter)
        self.file_path = None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.accept()
            urls = event.mimeData().urls()
            if urls:
                self.file_path = urls[0].toLocalFile()
                self.setText(self.file_path)
        else:
            event.ignore()


class WorkerThread(QThread):
    progress_changed = Signal(int)
    error_occurred = Signal(str)

    def __init__(self, api_key, file_path):
        super().__init__()
        self.api_key = api_key
        self.file_path = file_path

    def run(self):
        try:
            self.process_file(self.api_key, self.file_path)
        except Exception as e:
            self.error_occurred.emit(str(e))
        
    def process_file(self, api_key, file_path):
        import re
        import pandas as pd
        from openai import OpenAI
        import time
        import os
        from tqdm import tqdm

        # Set up your OpenAI API key
        os.environ['OPENAI_API_KEY']=api_key

        # Instantiation
        client = OpenAI()

        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)  # Replace 'input.csv' with the path to your input CSV file

        title_list = df['title'].tolist()
        authors_list = df['author'].tolist()
        years_list = df['year'].tolist()
        abstract_list = df['abstract'].tolist()

        temp = []
        i = 0
        total = len(title_list)
        for title, authors, year, abst in zip(title_list, authors_list, years_list, abstract_list):
            progress = int((i + 1) * 100 / total)
            self.progress_changed.emit(progress)
            
            # Construct the prompt
            prompt = f"""Please determine whether the following article should be excluded based on the following criteria:

            Exclusion Criteria:

            1) Animal study(research conducted on non-human animals): 
            2) Research category belongs to congress, erratum, letter, note, narrative review meaning that study that is not original study.
            3) Articles related with retraction or belongs to grey literature.
            4) The research is not written in Korean or English (this should be based explicitly on the title or abstract indicating the language is neither Korean nor English). 
            5) Systematic review.
            6) Any case study, and case series.

            Article details:

            Title: {title}
            Authors: {authors}
            Year: {year}
            Abstract: {abst}

           If the abstract is not provided or empty, try to classify the exclusion criteria based on the title. 
           Important notes:
           - Articles that involve **human clinical studies** should not be excluded under criterion 1 unless it is explicitly stated that the research is an animal study.
           - If the abstract is unavailable or empty, it should not automatically result in exclusion under criterion 4. Base the decision on clear evidence from the title indicating that the article is not written in Korean or English.
           - If none of the exclusion criteria explicitly apply, the article should be **included** by default.
           - If the article is to be excluded, specify the exclusion criterion number(s) and copy the relevant sentence(s) from the title or abstract that justify the decision into the <Reason for decision> field.           
           - Even if the abstract is not provided, it does not mean that it may not be writtern in korean or english, make decision based on title.
           - If the article is to be included, put **no reason** in <Reason for decision> field.


            Format your answer according to the following:
            ###
            Reason for exclusion: {{None,1,2,3,4,5,6}}
            Final decision: {{Include,Exclude}}
            Reason for decision:
            ###
            """

            # Generate
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":"You are a research assistant specialized in academic paper selection. "
                        "When given a CSV file containing information about research papers, "
                        "your task is to include or exclude each paper based on specified criteria."},
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            temp.append(completion.choices[0].message)
            i += 1

        reasoning = []
        decision = []
        evidence = []
        for i in temp:
            content = i.content
            # Use regex to match "Reason for exclusion" and "Final decision"
            match = re.search(r"Reason for exclusion:\s*\{*([^\}]*)\}*\sFinal decision:\s*\{*(Include|Exclude)\}*\sReason for decision:\s*(.*)", content, re.DOTALL)
            
            if match:
                # Extract reasoning and decision from the matched groups
                reasoning.append(match.group(1).strip())
                decision.append(match.group(2).strip())
                evidence.append(match.group(3).strip())
            else:
                # Default values if format is not matched
                reasoning.append('Not formatted')
                decision.append('Not formatted')
                evidence.append('None')

        df['exclusion_criteria'] = reasoning
        df['decision'] = decision
        df['evidence'] = evidence

        df.to_csv(f'{file_path[:-4]}_result.csv', index=False, encoding='utf-8')

        # Emit the finished signal when the work is done
        self.finished.emit()


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_elapsed_time)
        self.start_time = None

    def initUI(self):
        # Create widgets
        self.api_key_label = QLabel('API Key:')
        self.api_key_input = QLineEdit()

        self.file_label = DragDropLabel()

        self.submit_button = QPushButton('Submit')

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel('Time Elapsed: 0:00:00')

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.file_label)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.time_label)

        self.setLayout(layout)

        # Connect signals
        self.submit_button.clicked.connect(self.on_submit)

        # Set window properties
        self.setWindowTitle('Systematic Review Automator')
        self.resize(400, 300)
        self.show()

    def on_submit(self):
        api_key = self.api_key_input.text()
        file_path = self.file_label.file_path

        if not api_key or not file_path:
            QMessageBox.critical(self, 'Error', 'Please provide both API key and input file.')
            return

        # Reset progress bar and timer
        self.progress_bar.setValue(0)
        self.time_label.setText('Time Elapsed: 0:00:00')

        # Record start time and start timer
        self.start_time = datetime.now()
        self.timer.start(1000)  # Update every second

        # Disable submit button
        self.submit_button.setEnabled(False)

        # Start a worker thread
        self.worker = WorkerThread(api_key, file_path)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.error_occurred.connect(self.show_error_message)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.start()

    def update_elapsed_time(self):
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
        self.time_label.setText(f'Time Elapsed: {elapsed_str}')


    def show_error_message(self, message):
        QMessageBox.critical(self, 'Error', message)
        self.submit_button.setEnabled(True)
        self.timer.stop()


    def on_processing_finished(self):
        self.submit_button.setEnabled(True)
        self.timer.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())
