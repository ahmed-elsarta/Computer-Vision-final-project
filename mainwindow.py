import cv2
import sys
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from functions import detect_faces,get_reference_images,apply_pca

# Get the reference images and the their labels
references = get_reference_images()

# Get the weights, eigen vectors and eigen values of the vector
pca_params = apply_pca(references[2])


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("PCA Face Recognition")
        self.resize(800,600)

        # Create a QTabWidget
        tab_widget = QTabWidget()

        # First tab (Webcam detection)
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()

        self.VideoFeed = QLabel()

        self.StartBtn = QPushButton("Start")
        self.StartBtn.clicked.connect(self.start_webcam)

        self.StopBtn = QPushButton("Stop")
        self.StopBtn.clicked.connect(self.stop_webcam)

        tab1_layout.addWidget(self.VideoFeed)
        tab1_layout.addWidget(self.StartBtn)
        tab1_layout.addWidget(self.StopBtn)

        tab1.setLayout(tab1_layout)

        # Second tab (input image detection)
        tab2 = QWidget()
        tab2_layout = QVBoxLayout()

        self.BrowseBtn = QPushButton("Browse Image")
        self.BrowseBtn.clicked.connect(self.browse_image)

        self.inputImage = QLabel()

        tab2_layout.addWidget(self.inputImage)
        tab2_layout.addWidget(self.BrowseBtn)

        tab2.setLayout(tab2_layout)

        tab_widget.addTab(tab1, "Webcam Detection")
        tab_widget.addTab(tab2, "Image Detection")

        # Set the QTabWidget as the central widget of the main window
        self.setCentralWidget(tab_widget)


# ---------------------- Webcam tab functions ---------------------- #
    def start_webcam(self):
        # Create a video capture object
        self.camera = cv2.VideoCapture(0,cv2.CAP_DSHOW)

        # Set the frame size to match the label size
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.VideoFeed.width())
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.VideoFeed.height())
    
        # Create a timer to update the video stream
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(5)  # 5 milliseconds

    def stop_webcam(self):
        self.camera.release()

    def update_frame(self):
        if self.camera.isOpened():
            # Read the frame
            stream, frame = self.camera.read()
            flipped_frame = cv2.flip(frame, 1)

            flipped_frame = detect_faces(flipped_frame,references,pca_params)

            # Convert the frame to RGB format
            flipped_frame = cv2.cvtColor(flipped_frame, cv2.COLOR_BGR2RGB)

            # Create a QImage from the frame data
            img = QImage(flipped_frame, flipped_frame.shape[1], flipped_frame.shape[0], QImage.Format_RGB888)

            # Create a QPixmap from the QImage
            pix = QPixmap.fromImage(img)

            # Set the pixmap on the label to display the video stream
            self.VideoFeed.setPixmap(pix)

# ---------------------- Input Image tab functions ---------------------- #
    def browse_image(self):
        fileName = QFileDialog.getOpenFileName(self,"Select Image",filter="Image File (*.png *.jpg *.jpeg)")
        self.inputImagePath = fileName[0]
        input_image = cv2.imread(self.inputImagePath)
        
        detected_input_image = detect_faces(input_image,references,pca_params)

        cv2.imwrite("detected_faces_image.jpg",detected_input_image)

        self.inputImage.setPixmap(QPixmap("detected_faces_image.jpg").scaled(self.inputImage.size(), Qt.KeepAspectRatio))
