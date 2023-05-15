import sys

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout

from mpr import MPRViewer


if __name__ == '__main__':
    app = QApplication(sys.argv)

    view = MPRViewer(r'D:\datasets\3D_DDH\all\K1_IM_0001.nii.gz')
    # view = MPRViewer()
    # view.set_data(r'D:\datasets\3D_DDH\all\K1_IM_0001.nii.gz')

    win = QWidget()
    win.setWindowTitle('MPR Viewer')
    win.resize(1200, 600)
    layout = QVBoxLayout()
    layout.addWidget(view.get_widget())
    win.setLayout(layout)
    win.show()

    sys.exit(app.exec_())
