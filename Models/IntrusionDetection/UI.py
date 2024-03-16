import cv2
import numpy as np
import streamlit as st
from time import sleep
import torch 
import numpy as np
import cv2
from time import time
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
import face_recognition
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class ObjectDetection:
    def __init__(self, capture_index):
        self.capture_index = capture_index
        self.model = YOLO("yolov8n.pt")
        self.annotator = None
        self.start_time = 0
        self.end_time = 0
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # Load known faces
        self.known_faces = {}
        known_people = ["nishant.jpg", "nitesh.jpg", "devang.jpg"]
        for person in known_people:
            name = person.split('.')[0]
            image = face_recognition.load_image_file(person)
            encoding = face_recognition.face_encodings(image)[0]
            self.known_faces[name] = encoding

        # Email configuration
        self.password = "gnpi egai czue lohr"
        self.from_email = "niteshbrathod14@gmail.com"
        self.to_email = "niteshbrathod1432003@gmail.com"
        self.server = smtplib.SMTP('smtp.gmail.com:587')
        self.server.starttls()
        self.server.login(self.from_email, self.password)

    def predict(self, im0):
        results = self.model(im0)
        return results

    def display_fps(self, im0):
        self.end_time = time()
        fps = 1 / np.round(self.end_time - self.start_time, 2)
        text = f'FPS: {int(fps)}'
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        gap = 10
        cv2.rectangle(im0, (20 - gap, 70 - text_size[1] - gap), (20 + text_size[0] + gap, 70 + gap), (255, 255, 255), -1)
        cv2.putText(im0, text, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

    def plot_bboxes(self, results, im0):
        class_ids = []
        self.annotator = Annotator(im0, 3, results[0].names)
        boxes = results[0].boxes.xyxy.cpu()
        clss = results[0].boxes.cls.cpu().tolist()
        names = results[0].names
        for box, cls in zip(boxes, clss):
            class_ids.append(cls)
            self.annotator.box_label(box, label=names[int(cls)], color=colors(int(cls), True))
        return im0, class_ids

    def recognize_face(self, face_encoding):
        for name, known_encoding in self.known_faces.items():
            # Compare the face encoding with known encodings
            match = face_recognition.compare_faces([known_encoding], face_encoding)
            if match[0]:
                return name
        return "Unknown"

    def send_email(self, object_detected):
        message = MIMEMultipart()
        message['From'] = self.from_email
        message['To'] = self.to_email
        message['Subject'] = "Security Alert"
        message_body = f'ALERT - {object_detected} unknown person detected!!'
        message.attach(MIMEText(message_body, 'plain'))
        self.server.sendmail(self.from_email, self.to_email, message.as_string())

    def __call__(self):
        cap = cv2.VideoCapture(self.capture_index)
        assert cap.isOpened()
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        frame_count = 0
        email_sent = False
        while True:
            self.start_time = time()
            ret, im0 = cap.read()
            assert ret
            results = self.predict(im0)
            im0, _ = self.plot_bboxes(results, im0)

            # Find face locations in the frame
            face_locations = face_recognition.face_locations(im0)
        
            # Encode faces in the frame
            face_encodings = face_recognition.face_encodings(im0, face_locations)

            # Recognize faces
            unknown_persons = 0
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                name = self.recognize_face(face_encoding)
                # Draw square around the face
                cv2.rectangle(im0, (left, top), (right, bottom), (0, 255, 0), 2)
                # Draw name on the square
                cv2.rectangle(im0, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(im0, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
                if name == "Unknown":
                    unknown_persons += 1

            if unknown_persons > 0 and not email_sent:
                self.send_email(unknown_persons)
                email_sent = True
            elif unknown_persons == 0:
                email_sent = False

            self.display_fps(im0)
            cv2.imshow('YOLOv8 Detection', im0)
            frame_count += 1
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        self.server.quit()

def capture_video(detector):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Error: Unable to open camera.")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("Error: Unable to read frame.")
            break

        # Perform object detection
        frame = detector.predict(frame)

        # Display the frame
        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="BGR")

        # Wait for a short time to limit frame rate
        sleep(0.1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def main():
    st.title("Object Detection with Streamlit and OpenCV")

    # Initialize object detector
    detector = ObjectDetection(capture_index=0)

    # Display the camera feed with object detection
    st.header("Camera Feed")
    capture_video(detector)

    st.sidebar.title("Object Detection Settings")


if __name__ == "__main__":
    main()