import cv2
import numpy as np
import mediapipe as mp
import time
import winsound



# -----------------------------
class DrowsinessSystem:
    def __init__(self):
        self.is_running = False
        self.last_valid_ear = 0.3
        self.emergency_contact = ""
        self.sound_enabled = True
        self.current_ear = 0.0
        self.cap = None
        self.frame_counter = 0
        self.drowsiness_state = "NORMAL"

        import mediapipe as mp
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
        max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
    )
            
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        self.ear_threshold = 0.25
        self.max_drowsy_frames_warning = 25
        self.max_drowsy_frames_critical = 50
        self.max_drowsy_frames_emergency = 90

        self.emergency_start_time = None
        self.emergency_duration = 5  # seconds countdown

    # -------------------------
    # Camera Control
    # -------------------------
    
    def initialize_camera(self, source):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            self.cap = None
            raise Exception(f"Failed to open camera source: '{source}'. Check that the device is connected or the URL is valid.")

    def release_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows() 

    def get_frame(self):
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    # -------------------------
    # Detection Pipeline
    # -------------------------
    def detect_face(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        if results.multi_face_landmarks:
            return results.multi_face_landmarks[0]
        return None

    def detect_eyes(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return None
        h, w = frame.shape[:2]
        landmarks = results.multi_face_landmarks[0].landmark
        return [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    def calculate_ear(self, eye_points):
        def dist(a, b):
            return np.linalg.norm(np.array(a) - np.array(b))

        p1, p2, p3, p4, p5, p6 = eye_points
        return (dist(p2, p6) + dist(p3, p5)) / (2.0 * dist(p1, p4))

    # -------------------------
    # Drowsiness Logic
    # -------------------------
    def update_drowsiness_state(self, ear_value):
        if ear_value < self.ear_threshold:
            self.frame_counter += 1
        else:
            self.frame_counter = 0

        if self.frame_counter > self.max_drowsy_frames_emergency:
            self.drowsiness_state = "EMERGENCY"
        elif self.frame_counter > self.max_drowsy_frames_critical:
            self.drowsiness_state = "CRITICAL"
        elif self.frame_counter > self.max_drowsy_frames_warning:
            self.drowsiness_state = "WARNING"
        else:
            self.drowsiness_state = "NORMAL"

    def handle_alerts(self):

        if not self.sound_enabled:
            return

        if not hasattr(self, "last_alert_time"):
            self.last_alert_time = 0

        current_time = time.time()

        # cooldown: 1 second
        if current_time - self.last_alert_time < 1:
            return

        if self.drowsiness_state == "WARNING":
            winsound.Beep(800, 200)
            self.last_alert_time = current_time

        elif self.drowsiness_state == "CRITICAL":
            winsound.Beep(1200, 600)
            self.last_alert_time = current_time
            
        elif self.drowsiness_state == "EMERGENCY":
            winsound.Beep(1500, 800)
            self.last_alert_time = current_time

    def handle_emergency(self):
        if self.drowsiness_state == "EMERGENCY":
            if self.emergency_start_time is None:
                self.emergency_start_time = time.time()
            elapsed = time.time() - self.emergency_start_time
            remaining = self.emergency_duration - elapsed
            return remaining if remaining > 0 else 0
        else:
            self.emergency_start_time = None
            return None

    # -------------------------
    # Processing
    # -------------------------
    def process_frame(self, frame):
        if frame is None:
            return None

        landmarks = self.detect_eyes(frame)
        if landmarks is None:
            self.frame_counter = 0
            self.drowsiness_state = "NORMAL"
            return frame

        LEFT  = [33, 160, 158, 133, 153, 144]
        RIGHT = [362, 385, 387, 263, 373, 380]

        left_ear  = self.calculate_ear([landmarks[i] for i in LEFT])
        right_ear = self.calculate_ear([landmarks[i] for i in RIGHT])
        avg_ear   = (left_ear + right_ear) / 2.0
        if avg_ear < 0.1:
            # treat as closed eyes, not ignore
            avg_ear = self.last_valid_ear * 0.5
        else:
            self.last_valid_ear = avg_ear

        self.update_drowsiness_state(avg_ear)
        self.handle_alerts()
        remaining = self.handle_emergency()

        color = (0, 255, 0)  # green
        if self.drowsiness_state == "WARNING":
            color = (0, 255, 255)  # yellow
        elif self.drowsiness_state == "CRITICAL":
            color = (0, 0, 255)  # red
        if self.drowsiness_state == "EMERGENCY":
            if remaining is not None and remaining > 0:
                cv2.putText(frame, f"Calling in {int(remaining)}...",
                            (10, 100), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 0, 255), 2)
            else:
                contact = self.emergency_contact if self.emergency_contact else "EMERGENCY CONTACT"
                cv2.putText(frame, f"CALLING {contact}",
                            (10, 100), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 0, 255), 2)

        cv2.putText(frame, f"EAR: {avg_ear:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"State: {self.drowsiness_state}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        self.current_ear = avg_ear

        return frame

    # -------------------------
    # Main Loop
    # -------------------------
    def run(self):
        while self.is_running:
            frame = self.get_frame()
            if frame is None:
                break

            frame = self.process_frame(frame)
            cv2.imshow("Drowsiness Detection", frame)

            # ESC key exit
            if cv2.waitKey(1) & 0xFF == 27:
                break

            # Detect window closed (IMPORTANT FIX)
            if cv2.getWindowProperty("Drowsiness Detection", cv2.WND_PROP_VISIBLE) < 1:
                break

        self.release_camera()

    def start_system(self):
        if not self.is_running:
            self.initialize_camera(0)
            self.is_running = True

    def stop_system(self):
        if self.is_running:
            self.release_camera()
            self.is_running = False

    def update_settings(self, ear=None, warning=None, critical=None, emergency=None):

        if (warning and critical and warning >= critical) or \
        (critical and emergency and critical >= emergency):
            return

        if ear is not None:
            self.ear_threshold = ear
        if warning is not None:
            self.max_drowsy_frames_warning = warning
        if critical is not None:
            self.max_drowsy_frames_critical = critical
        if emergency is not None:
            self.max_drowsy_frames_emergency = emergency

    def get_status(self):
        return {
            "ear": self.current_ear,
            "state": self.drowsiness_state,
            "running": self.is_running
        }
    
    def set_emergency_contact(self, number):
        self.emergency_contact = number

    def get_emergency_contact(self):
        return self.emergency_contact
    
    def set_sound(self, enabled):
        self.sound_enabled = enabled

# -----------------------------
# API Layer (Flask later)
# -----------------------------
class APIServer:
    def __init__(self, system):
        pass

    def start_server(self):
        pass

    def setup_routes(self):
        pass


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    system = DrowsinessSystem()
    system.start_system()
    system.run()