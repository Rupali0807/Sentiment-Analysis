import openai
import sqlite3
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt

# OpenAI API Key
OPENAI_API_KEY = "OPENAI_API_KEY"

# SQLite database folder and file
DB_FOLDER = "database"
DB_FILE = os.path.join(DB_FOLDER, "sentiment_analysis.db")

### DATABASE FUNCTIONS ###
def initialize_database():
    """Create the database folder and the SQLite database/tables if they don't exist."""
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)  # Create the folder if it doesn't exist
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_sentiment_to_db(input_text, sentiment):
    """Save the input text, sentiment, and timestamp into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sentiment_analysis (input_text, sentiment, timestamp)
        VALUES (?, ?, ?)
    """, (input_text, sentiment, datetime.now()))
    conn.commit()
    conn.close()

def fetch_all_results():
    """Retrieve all sentiment analysis results from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT input_text, sentiment, timestamp FROM sentiment_analysis
    """)
    results = cursor.fetchall()
    conn.close()
    return [{"input_text": row[0], "sentiment": row[1], "timestamp": row[2]} for row in results]

### SENTIMENT ANALYSIS FUNCTION ###
def analyze_sentiment(input_text):
    """Use OpenAI to analyze sentiment of the given text."""
    if not input_text.strip():
        return "Error: Input text cannot be empty."

    prompt = f"Analyze the sentiment of the following text and classify it as Positive, Negative, or Neutral: {input_text}"
    try:
        response = openai.Completion.create(
            engine="o1-mini",
            prompt=prompt,
            max_tokens=60,
            n=1,
            stop=None
        )
        return response.choices[0].text.strip()
    except openai.OpenAIError as e:  # Catch OpenAI-specific errors
        return f"OpenAI API Error: {e}"
    except Exception as e:  # Catch other general errors
        return f"An unexpected error occurred: {e}"

### PyQt5 GUI ###
class SentimentAnalysisApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sentiment Analysis")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Input label and text field
        self.label_input = QLabel("Enter text to analyze:")
        self.layout.addWidget(self.label_input)

        self.text_input = QLineEdit()
        self.layout.addWidget(self.text_input)

        # Analyze button
        self.analyze_button = QPushButton("Analyze Sentiment")
        self.analyze_button.clicked.connect(self.analyze_sentiment)
        self.layout.addWidget(self.analyze_button)

        # Sentiment result label
        self.result_label = QLabel("Sentiment: ")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.layout.addWidget(self.result_label)

        # View all results button
        self.view_results_button = QPushButton("View All Results")
        self.view_results_button.clicked.connect(self.view_results)
        self.layout.addWidget(self.view_results_button)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Input Text", "Sentiment", "Timestamp"])
        self.layout.addWidget(self.results_table)

    def analyze_sentiment(self):
        """Handle the sentiment analysis process."""
        input_text = self.text_input.text()
        if not input_text:
            QMessageBox.warning(self, "Error", "Please enter text to analyze!")
            return

        # Analyze sentiment using OpenAI
        sentiment = analyze_sentiment(input_text)
        if "Error" in sentiment:
            QMessageBox.critical(self, "Error", sentiment)
            return

        # Save to database
        save_sentiment_to_db(input_text, sentiment)

        # Display the sentiment
        self.result_label.setText(f"Sentiment: {sentiment}")

    def view_results(self):
        """Fetch and display all results from the database."""
        # Fetch results
        results = fetch_all_results()

        # Update table
        self.results_table.setRowCount(len(results))
        for row_idx, row in enumerate(results):
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(row["input_text"]))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(row["sentiment"]))
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(row["timestamp"]))

### MAIN FUNCTION ###
if __name__ == "__main__":
    # Initialize the database
    initialize_database()

    # Start the PyQt5 app
    app = QApplication([])
    window = SentimentAnalysisApp()
    window.show()
    app.exec_()
