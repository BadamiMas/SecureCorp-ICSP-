# save_face_encode.py
import face_recognition
import cv2
import numpy as np
import base64
import dlib




# Load an image of yourself (make sure it's clear and shows your face)
image = face_recognition.load_image_file(r"e:\PSB\Degree Cyber\ICSP\me.jpg")

# Get encodings
encodings = face_recognition.face_encodings(image)

if len(encodings) == 0:
    print("No face detected. Try another image.")
else:
    encoding = encodings[0]  # take the first face
    # Convert to base64 so it matches your DB format
    encoding_bytes = encoding.tobytes()
    encoding_b64 = base64.b64encode(encoding_bytes).decode("utf-8")
    print("Copy this string into your DB face_encode column:\n")
    print(encoding_b64)
