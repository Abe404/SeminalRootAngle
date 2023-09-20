import sys
import os
from extract import get_angles_from_image
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGridLayout, QPushButton, 
    QFileDialog, QWidget, QLabel, QMessageBox,
    QSpinBox, QCheckBox
)
from progress_widget import BaseProgressWidget
import time
import datetime
import humanize


def ls(dir_path):
    # Don't show hidden files
    # These can happen due to issues like file system 
    # synchonisation technology. RootPainter doesn't use them anywhere
    fnames = os.listdir(dir_path)
    fnames = [f for f in fnames if f[0] != '.']
    return fnames


class ProgressWatchThread(QThread):
    """
    Runs another thread.
    """
    progress_change = pyqtSignal(int, int)
    done = pyqtSignal(list)

    def __init__(self, root_seg_dir,
            im_dataset_dir, seed_seg_dir,
            max_seed_points_per_im, debug_image_dir,
            output_csv_path, error_csv_path,
            radius=300, output_debug_images=True):
        super().__init__()

        self.root_seg_dir = root_seg_dir
        self.im_dataset_dir = im_dataset_dir
        self.seed_seg_dir = seed_seg_dir
        self.max_seed_points_per_im = max_seed_points_per_im
        self.debug_image_dir = debug_image_dir
        self.output_csv_path = output_csv_path
        self.error_csv_path = error_csv_path
        self.radius = radius
        self.output_debug_images = output_debug_images

    def run(self):

        seg_fnames = os.listdir(self.seed_seg_dir)
        seg_fnames = [s for s in seg_fnames if '.png' in s]
        start = time.time()

        csv_file = open(self.output_csv_path, 'w+')
        error_file = open(self.error_csv_path, 'w+')
        print("file_name,angle_degrees,seed_index,seed_x,seed_y,seed_pixels", file=csv_file)
        print("file_name,error_message,seed_index,seed_x,seed_y,seed_pixels", file=error_file)
        errors = []
        for i, fname in enumerate(seg_fnames):
            print(f"Extracting angles:{i + 1}/{len(seg_fnames)}", fname)
            self.progress_change.emit(i+1, len(seg_fnames))
            try:
                get_angles_from_image(self.root_seg_dir, self.im_dataset_dir,
                                      self.seed_seg_dir,
                                      self.max_seed_points_per_im,
                                      fname, self.radius,
                                      csv_file, error_file,
                                      self.debug_image_dir,
                                      save_debug_image=self.output_debug_images)
            except Exception as error:
                print(fname, error)
                print('file_name,{error},NA,NA,NA,NA', file=error_file)
                errors.append(error)
        time_str = humanize.naturaldelta(datetime.timedelta(seconds=time.time() - start))
        print('Extracting angles for', len(seg_fnames), 'images took', time_str)
        self.done.emit(errors)

            
class ProgressWidget(BaseProgressWidget):
    def __init__(self, task):
        super().__init__(task)
        self.watch_thread = None

    def run(self, root_seg_dir,
            im_dataset_dir, seed_seg_dir,
            max_seed_points_per_im, debug_image_dir,
            output_csv_path, error_csv_path,
            radius=300, output_debug_images=True):

        os.makedirs(debug_image_dir)

        self.watch_thread = ProgressWatchThread(root_seg_dir,
            im_dataset_dir, seed_seg_dir,
            max_seed_points_per_im, debug_image_dir,
            output_csv_path, error_csv_path, radius, output_debug_images)

        self.watch_thread.progress_change.connect(self.onCountChanged)
        self.watch_thread.done.connect(self.done)
        self.watch_thread.start()


class SeminalRootAngleExtractor(QMainWindow):
    def __init__(self):
        super().__init__()


        self.progress_widget = None

        self.setWindowTitle("Seminal Root Angle Extractor")
        #self.setGeometry(100, 100, 400, 450)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QGridLayout()
        self.central_widget.setLayout(self.layout)

        self.root_seg_dir_label = QLabel("Root Segmentation Directory: None")
        self.seed_seg_dir_label = QLabel("Seed Segmentation Directory: None")
        self.input_photo_dir_label = QLabel("Input Photo Directory: None")
        self.output_dir_label = QLabel("Output Directory: None")

        # Create labels and buttons for input directories
        self.create_input_dir_widgets("Root Segmentation", self.select_root_seg_folder, self.root_seg_dir_label, 0)
        self.create_input_dir_widgets("Seed Segmentation", self.select_seed_seg_folder, self.seed_seg_dir_label, 1)
        self.create_input_dir_widgets("Input Photo", self.select_input_photo_folder, self.input_photo_dir_label, 2)


        # add widget to specify the number of seed points
        label = QLabel(f"Max seed points per image:")
        self.layout.addWidget(label, 4, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.seed_count_spinbox = QSpinBox()
        self.seed_count_spinbox.setValue(2)
        self.seed_count_spinbox.setMinimum(1)
        self.layout.addWidget(self.seed_count_spinbox, 4, 1, 1, 3)


        # add widget to specify the number of seed points
        label = QLabel(f"Root angle radius:")
        self.layout.addWidget(label, 5, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.radius_spinbox = QSpinBox()
        self.radius_spinbox.setMaximum(9000)
        self.radius_spinbox.setValue(300)
        self.radius_spinbox.setMinimum(3)
        self.layout.addWidget(self.radius_spinbox, 5, 1, 1, 3)

         # add widget to specify the optional image output
        label = QLabel(f"Output debug image (slower):")
        self.layout.addWidget(label, 6, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.debug_image_checkbox = QCheckBox()
        self.debug_image_checkbox.setCheckState(Qt.CheckState.Checked)
        self.layout.addWidget(self.debug_image_checkbox, 6, 1, 1, 3)


        # Create a folder selection button and label for the output directory
        self.create_output_dir_widgets("Output",
            self.select_output_folder, self.output_dir_label, 3)

        # Create a submit button
        self.submit_button = QPushButton("Extract angles")
        self.submit_button.clicked.connect(self.create_output_folder)

        #row: int, column: int, rowSpan: int, columnSpan: int, alignment: Qt.AlignmentFlag = Qt.Alignment()):
        self.layout.addWidget(self.submit_button, 7, 0, 1, 4)

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


        if missing_directories:
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
        print('Extract angles')
        self.progress_widget = ProgressWidget(f'Extracting angles to {output_folder}')
        self.progress_widget.run(root_seg_dir=self.root_seg_dir,
                                 im_dataset_dir=self.input_photo_dir,
                                 seed_seg_dir=self.seed_seg_dir,
                                 max_seed_points_per_im=self.seed_count_spinbox.value(),
                                 radius=self.radius_spinbox.value(),
                                 debug_image_dir=os.path.join(output_folder, 'debug_images'),
                                 output_csv_path=os.path.join(output_folder, 'angles.csv'),
                                 error_csv_path=os.path.join(output_folder, 'errors.csv'),
                                 output_debug_images=self.debug_image_checkbox.checkState())

        self.progress_widget.show()
        self.close()


def main():
    app = QApplication(sys.argv)
    window = SeminalRootAngleExtractor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

