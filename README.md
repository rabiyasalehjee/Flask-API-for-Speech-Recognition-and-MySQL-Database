# Flask API for Speech Recognition and MySQL Database

## Overview
This project is a **Flask-based web application** for analyzing and managing speech files. It uses **MySQL** for storing and retrieving data, and integrates libraries like **Librosa** and **SpeechRecognition** for audio processing and speech-to-text conversion.

### Key Features
- **Audio Processing**: Extract speech, pitch, pace, and word count from audio files.
- **Speech Management**: Upload, store, and retrieve speech files with associated metadata.
- **MySQL Database Integration**: Manage users, assignments, interviews, and speech topics.
- **API Endpoints**: 
  - Upload audio files
  - Retrieve user and speech details
  - Manage assignments and interview records

## Technology Stack
- **Backend**: Python, Flask
- **Database**: MySQL
- **Audio Processing**: Librosa, SpeechRecognition
- **API Format**: JSON

## Requirements

To run this project, you need to have the following installed:

- Python 3.7+
- MySQL Database
- Flask
- Librosa
- SpeechRecognition
