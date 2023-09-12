import sys
import os
import numpy as np
from seminal_root_angle.extract import extract_all_angles
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QPushButton, QFileDialog, QWidget, QLabel, QMessageBox, QProgressBar
from PyQt6.QtGui import QImage, QPixmap

class SeminalRootAngleExtractor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Seminal Root Angle Extractor")
        self.setGeometry(100, 100, 400, 450)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QGridLayout()
        self.central_widget.setLayout(self.layout)


        # Create a progress bar
        self.progress_label = QLabel("Input required")
        self.layout.addWidget(self.progress_label, 5, 0, 1, 2)
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar, 6, 0, 1, 2)
        self.progress_value = 0


        self.root_seg_dir_label = QLabel("Root Segmentation Directory: None")
        self.seed_seg_dir_label = QLabel("Seed Segmentation Directory: None")
        self.input_photo_dir_label = QLabel("Input Photo Directory: None")
        self.output_dir_label = QLabel("Output Directory: None")

        # Create labels and buttons for input directories
        self.create_input_dir_widgets("Root Segmentation", self.select_root_seg_folder, self.root_seg_dir_label, 0)
        self.create_input_dir_widgets("Seed Segmentation", self.select_seed_seg_folder, self.seed_seg_dir_label, 1)
        self.create_input_dir_widgets("Input Photo", self.select_input_photo_folder, self.input_photo_dir_label, 2)

        # Create a folder selection button and label for the output directory
        self.create_output_dir_widgets("Output", self.select_output_folder, self.output_dir_label, 3)

        # Create a submit button
        self.submit_button = QPushButton("Extract angles")
        self.submit_button.clicked.connect(self.create_output_folder)
        self.layout.addWidget(self.submit_button, 4, 0, 1, 2)

        self.root_seg_dir = ""
        self.seed_seg_dir = ""
        self.input_photo_dir = ""
        self.output_dir = ""

    def create_input_dir_widgets(self, label_text, select_function, dir_label, row):
        label = QLabel(f"{label_text} Directory:")
        dir_label.setText("None")
        button = QPushButton(f"Select {label_text} Folder")
        button.clicked.connect(select_function)

        self.layout.addWidget(label, row, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(dir_label, row, 1, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(button, row, 2, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)

    def create_output_dir_widgets(self, label_text, select_function, dir_label, row):
        label = QLabel(f"{label_text} Directory:")
        dir_label.setText("None")
        button = QPushButton(f"Select {label_text} Folder")
        button.clicked.connect(select_function)

        self.layout.addWidget(label, row, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(dir_label, row, 1, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(button, row, 2, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)

    def select_root_seg_folder(self):
        folder_dialog = QFileDialog(self)
        folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        folder_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)

        if folder_dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.root_seg_dir = folder_dialog.selectedUrls()[0].toLocalFile()
            self.root_seg_dir_label.setText(self.root_seg_dir)

    def select_seed_seg_folder(self):
        folder_dialog = QFileDialog(self)
        folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        folder_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)

        if folder_dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.seed_seg_dir = folder_dialog.selectedUrls()[0].toLocalFile()
            self.seed_seg_dir_label.setText(self.seed_seg_dir)

    def select_input_photo_folder(self):
        folder_dialog = QFileDialog(self)
        folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        folder_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)

        if folder_dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.input_photo_dir = folder_dialog.selectedUrls()[0].toLocalFile()
            self.input_photo_dir_label.setText(self.input_photo_dir)

    def select_output_folder(self):
        folder_dialog = QFileDialog(self)
        folder_dialog.setFileMode(QFileDialog.FileMode.Directory)

        if folder_dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.output_dir = folder_dialog.selectedUrls()[0].toLocalFile()
            self.output_dir_label.setText(self.output_dir)

    def create_output_folder(self):
        missing_directories = []

        if not self.root_seg_dir:
            missing_directories.append("Root Segmentation")
        if not self.seed_seg_dir:
            missing_directories.append("Seed Segmentation")
        if not self.input_photo_dir:
            missing_directories.append("Input Photo")
        if not self.output_dir:
            missing_directories.append("Output")


        if missing_directories and False:
            QMessageBox.critical(
                self,
                "Missing Directories",
                f"The following directories are missing:\n\n{', '.join(missing_directories)}",
                QMessageBox.StandardButton.Ok
            )
        else:
            # Generate a folder name based on current time and 'extracted_root_angles'
            current_time = QDateTime.currentDateTime().toString("yyyyMMddhhmmss")
            folder_name = f"{current_time}_extracted_root_angles"
            output_folder_path = os.path.join(self.output_dir, folder_name)

            # Create the output folder
            os.makedirs(output_folder_path)

            print(f"Output folder created: {output_folder_path}")

            self.extract_angles(output_folder_path)


    def extract_angles(self, output_folder):
        print('extract angles')
        
        extract_all_angles(root_seg_dir=self.root_seg_dir,
                           im_dataset_dir=input_photo_dir,
                           seed_seg_dir=seed_seg_dir,
                           max_seed_points_per_im=2,
                           debug_image_dir=os.path.join(output_folder, 'debug_images'),
                           output_csv_path=os.path.join(output_folder, 'angles.csv')
                           error_csv_path=os.path.join(output_folder, 'errors.csv'))

        #         self.progress_value = 0
        # 
        #         for i in range(100):
        #             self.progress_value += 0.01  # Increase the progress by 1%
        #             self.progress_bar.setValue(int(self.progress_value * 100))  # Set the progress bar value
        #             if self.progress_value >= 1:
        #                 self.progress_label.setText("Extraction complete")
        #             import time
        #             time.sleep(0.01)

def main():
    app = QApplication(sys.argv)
    window = SeminalRootAngleExtractor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

