import os
import sys
from base64 import b64decode

import vtk
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, pyqtSignal, QResource
from PyQt5.QtNetwork import QHostAddress
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebSockets import QWebSocketServer

from websocketclientwrapper import WebSocketClientWrapper

QResource.registerResource("mpr.rcc")


def parse_data_uri(data_uri, save_file):
    load_filename, url = data_uri.split(",data:", 1)
    header, encoded = url.split("base64,", 1)
    data = b64decode(encoded)
    with open(save_file, "wb") as f:
        f.write(data)
    return load_filename


class Bridge(QObject):
    send_data = pyqtSignal(str)
    status = False
    data = None
    temp_file = "volume.tmp"

    @pyqtSlot(str, result=str)
    def receive_data(self, text):
        load_filename = parse_data_uri(text, self.temp_file)

        if load_filename.endswith('.nii.gz'):
            reader = vtk.vtkNIFTIImageReader()
            reader.SetFileName(self.temp_file)
            reader.Update()
        else:
            raise Exception("Unsupported file format.")

        writer = vtk.vtkXMLImageDataWriter()
        writer.SetInputData(reader.GetOutput())
        writer.WriteToOutputStringOn()
        writer.Update()
        xml = writer.GetOutputString()

        os.remove(self.temp_file)
        return xml

    @pyqtSlot(bool)
    def set_status(self, status):
        self.status = status
        if self.data is not None:
            self.send_data.emit(self.data)


class MPRViewer(object):

    def __init__(self, filename=None, url='qrc:/index.html', port=12345):
        self.server = QWebSocketServer("MPR Viewer", QWebSocketServer.NonSecureMode)
        self.port = port
        if not self.server.listen(QHostAddress.LocalHost, self.port):
            print("Failed to open web socket server.")
            sys.exit(-1)

        self.clientWrapper = WebSocketClientWrapper(self.server)

        self.channel = QWebChannel()
        self.clientWrapper.clientConnected.connect(self.channel.connectTo)
        self.bridge = Bridge()
        if filename is not None:
            self.bridge.data = self.get_string(filename)
        self.channel.registerObject("bridge", self.bridge)

        self.view = QWebEngineView()
        self.url = url
        self.view.load(QUrl(self.url))
        self.view.page().setWebChannel(self.channel)

    def get_widget(self):
        return self.view

    @staticmethod
    def get_string(filename):
        if filename.endswith('.nii.gz'):
            reader = vtk.vtkNIFTIImageReader()
            reader.SetFileName(filename)
            reader.Update()
        else:
            raise Exception("Unsupported file format.")

        writer = vtk.vtkXMLImageDataWriter()
        writer.SetInputData(reader.GetOutput())
        writer.WriteToOutputStringOn()
        writer.Update()
        xml = writer.GetOutputString()
        return xml

    def set_data(self, filename):
        if self.bridge.status:
            self.bridge.send_data.emit(self.get_string(filename))
        else:
            self.bridge.data = self.get_string(filename)
