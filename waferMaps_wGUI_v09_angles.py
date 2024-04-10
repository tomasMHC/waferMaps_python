# -*- coding: utf-8 -*-
# Kompilácia:
# python -m PyInstaller --noconfirm --noconsole --icon=icon_wafr.ico --onedir --upx-dir=C:\Users\zbnj4y\Documents\Programming\python-matfile\upx-4.0.1-win64 waferMaps_v08.py

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QListWidget
import tkinter as tk
import tkinter.filedialog as fd
import os
from scipy.io import loadmat
import numpy as np
import matplotlib.pyplot as plt
import sys
from configparser import ConfigParser
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
import matplotlib as mpl
from datetime import datetime
import matplotlib.font_manager as font_manager
import re
import pandas as pd
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredDrawingArea
from matplotlib.patches import Circle, FancyArrow

def crop_list_EE(ee_size, list):
    new_List=[]
    counter=1
    i=1
    for element in list:
        if (counter<=(ee_size*2) or np.isnan(element)==False):
            new_List.append(element)
            counter=counter+1
    while i <= ee_size*2:
        i=i+1
        new_List.append(np.nan)
    return np.array(new_List)
    
def point_on_circle_x(radius, angle_degrees, center_x):
    # Convert angle to radians
    angle_radians = np.deg2rad(angle_degrees)
    # Calculate x-coordinate
    x = center_x + radius * np.cos(angle_radians)
    return x
def point_on_circle_y(radius, angle_degrees, center_x):
    # Convert angle to radians
    angle_radians = np.deg2rad(angle_degrees)
    # Calculate x-coordinate
    x = center_x + radius * np.sin(angle_radians)
    return x

def draw_arrow(ax): # circle in the canvas coordinate                   
        ada = AnchoredDrawingArea(20,20, 0, 0,loc=4, pad=0., frameon=False)
        p = Circle((10,10),10,color="lightblue", alpha=0.4)
        arrow=FancyArrow(2,18,16,-16,color="red",head_width=2,alpha=0.5)
        ada.da.add_artist(p)
        ada.da.add_artist(arrow)
        ax.add_artist(ada)

def stamp(str):
    current_time = datetime.now()
    time_stamp = current_time.timestamp()
    date_time = datetime.fromtimestamp(time_stamp)
    str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
    return(str_date_time+": " + str)

def coll(lisst):
    global column
    a=len(lisst)
    if 5<a<= 10:
        column=2
    elif 20>a>10:
        column=3
    elif a>=20:
        column=4
    else:
        column=1

def regex_laser(zoznam):
    lasery=[]
    for i in zoznam:
        x=re.findall("[A-Z]{4}\d{3}-\d{2}",i)
        x=str(x).replace("'","")
        x=x.replace("[","")
        x=x.replace("]","")    
        lasery.append(x)
    seen=set()
    for i in range(len(zoznam)):
        n=1
        if lasery[i] not in seen:
            seen.add(lasery[i])
        else:
            lasery[i]="{laser}_{n}".format(laser=lasery[i],n=n)
            n=+1
    return lasery

def get_creation_date(file_path):
    print(file_path)
    return os.path.getmtime(file_path)

def get_creation_sorted_dict(dictionary):
    file_dates=[(key, dictionary.get(key), datetime.fromtimestamp(get_creation_date(key)).strftime("%Y%m%d%H%M%SPD")) for key in dictionary.keys()]
    sorted_file_dates=sorted(file_dates, key=lambda x: x[2])
    dates=list(zip(*sorted_file_dates))[2]
    sorted_list=regex_laser(list(zip(*sorted_file_dates))[0])
    sorted_values=list(zip(*sorted_file_dates))[1]
    return dict(zip(sorted_list, sorted_values)),dict(zip(sorted_list, dates))

mpl.use("PS")
parser = ConfigParser()
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(os.path.realpath(sys.executable))
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

savepath = app_path+"\output"
parser.read(app_path +"/config.ini")
saved_address = parser.get("savedirectory", "directoryOut")
ftypes = [("MAT files", "*.mat"), ("all files","*")]

#font import and charts font adjust
font_dirs = app_path+"\Barlow"
font_files = font_manager.findSystemFonts(fontpaths=font_dirs)

for font_file in font_files:
    font_manager.fontManager.addfont(font_file)

plt.rcParams['font.family'] = 'Barlow'
plt.rcParams['font.sans-serif'] = "Barlow"
plt.rcParams.update({"axes.linewidth":0.6,"axes.labelpad":3, "axes.titlepad":5,
                     "axes.titlesize":8,"axes.labelsize":6,"figure.titlesize":5,
                     "xtick.labelsize": 6, "xtick.major.size":2.5,
                     "ytick.labelsize": 6,"ytick.major.width":0.5, "ytick.direction":"out","ytick.major.size":2.5,
                     "font.weight": "normal","axes.labelweight":"bold"})

class ListboxWidget(QListWidget):
    zoznamPrdLen=0
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMovement(QListWidget.Free)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    def dragMoveEvent(self,event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
    def dropEvent(self,event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.clear()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    Ui_MainWindow.zoznamPrd.append(str(url.toLocalFile()))
                else:
                    Ui_MainWindow.zoznamPrd.append(str(url.toString()))
            Ui_MainWindow.zoznamPrd.sort()
            for i in range(len(Ui_MainWindow.zoznamPrd)):
                self.addItem((os.path.basename(str(Ui_MainWindow.zoznamPrd[i]))).split(".")[0])
        else:
            event.ignore()
        
        ui.count1.setText(str(len(Ui_MainWindow.zoznamPrd)))
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self._del_item()
            Ui_MainWindow.cou=len(Ui_MainWindow.zoznamPrd)
            Ui_MainWindow().update_label1(Ui_MainWindow.cou)
        if event.key() == Qt.Key_Up:
            current_row = self.currentRow()
            if current_row > 0:
                self.setCurrentRow(current_row - 1)
        elif event.key() == Qt.Key_Down:
            current_row = self.currentRow()
            if current_row < self.count() - 1:
                self.setCurrentRow(current_row + 1)
        else:
            super().keyPressEvent(event)
    
    def _del_item(self):
        Ui_MainWindow.cou=len(Ui_MainWindow.zoznamPrd)
        for item in self.selectedItems():
            ind=(self.row(item))
            del Ui_MainWindow.zoznamPrd[ind]
            self.takeItem(self.row(item))
            
class ListboxWidgetAfter(QListWidget):
    zoznamPoLen=0
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMovement(QListWidget.Free)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    def dragMoveEvent(self,event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
    def dropEvent(self,event):
        Ui_MainWindow.fileList=[]
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.clear()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    Ui_MainWindow.zoznamPo.append(str(url.toLocalFile()))
                else:
                    Ui_MainWindow.zoznamPo.append(str(url.toString()))
        Ui_MainWindow.zoznamPo.sort()
        print("zoznamPo drop: "+ str(Ui_MainWindow.zoznamPo))
        for i in range(len(Ui_MainWindow.zoznamPo)):

            self.addItem((os.path.basename(str(Ui_MainWindow.zoznamPo[i]))).split(".")[0])
            Ui_MainWindow.fileList.append(str(os.path.basename(Ui_MainWindow.zoznamPo[i])).rsplit(".",1)[0])
        else:
            event.ignore()
        print("fileList: "+str(len(Ui_MainWindow.fileList))+"----"+str(Ui_MainWindow.fileList))       
        ui.count2.setText(str(len(Ui_MainWindow.zoznamPo)))
        for i in Ui_MainWindow.fileList:
            if len(i.split("_"))>3:
                Ui_MainWindow.odraty.append(i.split("_")[-3])
            else:
                Ui_MainWindow.odraty.append(i)
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self._del_item()
            Ui_MainWindow.coua=len(Ui_MainWindow.zoznamPo)
            Ui_MainWindow().update_label2(Ui_MainWindow.coua)
        if event.key() == Qt.Key_Up:
            current_row = self.currentRow()
            if current_row > 0:
                self.setCurrentRow(current_row - 1)
        elif event.key() == Qt.Key_Down:
            current_row = self.currentRow()
            if current_row < self.count() - 1:
                self.setCurrentRow(current_row + 1)
        else:
            super().keyPressEvent(event)
    
    def _del_item(self):
        Ui_MainWindow.coua=len(Ui_MainWindow.zoznamPo)
        for item in self.selectedItems():
            ind=(self.row(item))
            del Ui_MainWindow.zoznamPo[ind]
            del Ui_MainWindow.fileList[ind]
            self.takeItem(self.row(item))
class Worker(QObject):
    progress = pyqtSignal(int)

class WorkerThread(QThread):
    progress_signal=pyqtSignal(int)
    run_finished=pyqtSignal()
    def run(self):
        Ui_MainWindow.runit(self)

class Ui_MainWindow(object):
    progress_signal=pyqtSignal(int)
    run_finished=pyqtSignal()
    regex=[]
    zoznamPrd=[]
    zoznamPo=[]
    cou=0
    coua=0
    fileList=[]
    odraty=[]
    def update_label1(self,s):
        ui.count1.setText(str(s))
    def update_label2(self,s):
        ui.count2.setText(str(s))

    def setupUi(self, MainWindow):
            MainWindow.setObjectName("MainWindow")
            MainWindow.resize(690, 459)
            self.centralwidget = QtWidgets.QWidget(MainWindow)
            self.centralwidget.setObjectName("centralwidget")
            self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
            self.gridLayout_2.setObjectName("gridLayout_2")
            self.gridLayout = QtWidgets.QGridLayout()
            self.gridLayout.setObjectName("gridLayout")
            self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
            self.tabWidget.setObjectName("tabWidget")
            self.tab = QtWidgets.QWidget()
            self.tab.setObjectName("tab")
            self.gridLayout_3 = QtWidgets.QGridLayout(self.tab)
            self.gridLayout_3.setObjectName("gridLayout_3")
            self.gridLayout_6 = QtWidgets.QGridLayout()
            self.gridLayout_6.setObjectName("gridLayout_6")
            self.logWindow = QtWidgets.QTextBrowser(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.logWindow.sizePolicy().hasHeightForWidth())
            self.logWindow.setSizePolicy(sizePolicy)
            self.logWindow.setMinimumSize(QtCore.QSize(0, 50))
            self.logWindow.setObjectName("logWindow")
            self.gridLayout_6.addWidget(self.logWindow, 1, 0, 1, 1)
            self.logWindowLabel = QtWidgets.QLabel(self.tab)
            self.logWindowLabel.setObjectName("logWindowLabel")
            self.gridLayout_6.addWidget(self.logWindowLabel, 0, 0, 1, 1)
            self.progressBar = QtWidgets.QProgressBar(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
            self.progressBar.setSizePolicy(sizePolicy)
            self.progressBar.setMinimumSize(QtCore.QSize(0, 10))
            self.progressBar.setProperty("value", 0)
            self.progressBar.setObjectName("progressBar")
            self.gridLayout_6.addWidget(self.progressBar, 2, 0, 1, 1)
            self.gridLayout_3.addLayout(self.gridLayout_6, 4, 1, 1, 3)
            self.verticalLayout_2 = QtWidgets.QVBoxLayout()
            self.verticalLayout_2.setObjectName("verticalLayout_2")
            self.headingLabel = QtWidgets.QLabel(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.headingLabel.sizePolicy().hasHeightForWidth())
            self.headingLabel.setSizePolicy(sizePolicy)
            font = QtGui.QFont()
            font.setPointSize(10)
            font.setBold(True)
            font.setWeight(75)
            self.headingLabel.setFont(font)
            self.headingLabel.setObjectName("headingLabel")
            self.verticalLayout_2.addWidget(self.headingLabel)
            self.remMapLabel = QtWidgets.QCheckBox(self.tab)
            font = QtGui.QFont()
            font.setPointSize(9)
            self.remMapLabel.setFont(font)
            self.remMapLabel.setChecked(True)
            self.remMapLabel.setObjectName("remMapLabel")
            self.verticalLayout_2.addWidget(self.remMapLabel)
            self.remProfsCheckBox = QtWidgets.QCheckBox(self.tab)
            font = QtGui.QFont()
            font.setPointSize(9)
            self.remProfsCheckBox.setFont(font)
            self.remProfsCheckBox.setObjectName("remProfsCheckBox")
            self.verticalLayout_2.addWidget(self.remProfsCheckBox)
            self.csvDataLabel = QtWidgets.QCheckBox(self.tab)
            font = QtGui.QFont()
            font.setPointSize(9)
            self.csvDataLabel.setFont(font)
            self.csvDataLabel.setObjectName("csvDataLabel")
            self.verticalLayout_2.addWidget(self.csvDataLabel)
            self.gridLayout_3.addLayout(self.verticalLayout_2, 1, 1, 1, 1)
            self.gridLayout_5 = QtWidgets.QGridLayout()
            self.gridLayout_5.setObjectName("gridLayout_5")
            self.label = QtWidgets.QLabel(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
            self.label.setSizePolicy(sizePolicy)
            self.label.setObjectName("label")
            self.gridLayout_5.addWidget(self.label, 4, 0, 1, 1)
            self.uloziskoLabel = QtWidgets.QLabel(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.uloziskoLabel.sizePolicy().hasHeightForWidth())
            self.uloziskoLabel.setSizePolicy(sizePolicy)
            self.uloziskoLabel.setObjectName("uloziskoLabel")
            self.gridLayout_5.addWidget(self.uloziskoLabel, 0, 0, 1, 1)
            self.chartRange = QtWidgets.QLineEdit(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.chartRange.sizePolicy().hasHeightForWidth())
            self.chartRange.setSizePolicy(sizePolicy)
            self.chartRange.setObjectName("chartRange")
            self.chartRange.setText("3.5")
            self.gridLayout_5.addWidget(self.chartRange, 4, 1, 1, 1)
            spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.gridLayout_5.addItem(spacerItem, 6, 0, 1, 1)
            self.otvoriskoLabel = QtWidgets.QLabel(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.otvoriskoLabel.sizePolicy().hasHeightForWidth())
            self.otvoriskoLabel.setSizePolicy(sizePolicy)
            self.otvoriskoLabel.setObjectName("otvoriskoLabel")
            self.gridLayout_5.addWidget(self.otvoriskoLabel, 1, 0, 1, 1)
            self.checkBox_range = QtWidgets.QCheckBox(self.tab,clicked = lambda: self.update_check())
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.checkBox_range.sizePolicy().hasHeightForWidth())
            self.checkBox_range.setSizePolicy(sizePolicy)
            self.checkBox_range.setObjectName("checkBox_range")
            self.gridLayout_5.addWidget(self.checkBox_range, 4, 2, 1, 1)
            self.run_it = QtWidgets.QPushButton(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.run_it.sizePolicy().hasHeightForWidth())
            self.run_it.setSizePolicy(sizePolicy)
            self.run_it.setMinimumSize(QtCore.QSize(0, 50))
            self.run_it.setAutoFillBackground(False)
            self.run_it.setStyleSheet("background-color: \"lightgreen\"; font: bold 14px")
            self.run_it.setObjectName("run_it")
            self.run_it.clicked.connect(self.startWorkInAThread)
            self.gridLayout_5.addWidget(self.run_it, 5, 0, 1, 3)
            self.ulozisko = QtWidgets.QToolButton(self.tab,clicked = lambda: self.save_it())
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.ulozisko.sizePolicy().hasHeightForWidth())
            self.ulozisko.setSizePolicy(sizePolicy)
            self.ulozisko.setMinimumSize(QtCore.QSize(20, 23))
            self.ulozisko.setObjectName("ulozisko")
            self.gridLayout_5.addWidget(self.ulozisko, 0, 1, 1, 1)
            self.otvorisko = QtWidgets.QPushButton(self.tab,clicked=lambda: self.otvor())
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.otvorisko.sizePolicy().hasHeightForWidth())
            self.otvorisko.setSizePolicy(sizePolicy)
            self.otvorisko.setMinimumSize(QtCore.QSize(20, 23))
            self.otvorisko.setObjectName("otvorisko")
            self.gridLayout_5.addWidget(self.otvorisko, 1, 1, 1, 1)
            self.gridLayout_3.addLayout(self.gridLayout_5, 2, 1, 1, 1)
            self.gridLayout_4 = QtWidgets.QGridLayout()
            self.gridLayout_4.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
            self.gridLayout_4.setObjectName("gridLayout_4")
            self.flipBox2 = QtWidgets.QCheckBox(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.flipBox2.sizePolicy().hasHeightForWidth())
            self.flipBox2.setSizePolicy(sizePolicy)
            self.flipBox2.setObjectName("flipBox2")
            self.gridLayout_4.addWidget(self.flipBox2, 0, 4, 1, 3)
            self.loadDataAft = QtWidgets.QPushButton(self.tab,clicked= lambda: self.open_it2())
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.loadDataAft.sizePolicy().hasHeightForWidth())
            self.loadDataAft.setSizePolicy(sizePolicy)
            self.loadDataAft.setObjectName("loadDataAft")
            self.gridLayout_4.addWidget(self.loadDataAft, 3, 4, 1, 3)
            self.loadDataBef = QtWidgets.QPushButton(self.tab,clicked= lambda: self.open_it1())
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.loadDataBef.sizePolicy().hasHeightForWidth())
            self.loadDataBef.setSizePolicy(sizePolicy)
            self.loadDataBef.setObjectName("loadDataBef")
            self.gridLayout_4.addWidget(self.loadDataBef, 3, 0, 1, 2)
            self.count2 = QtWidgets.QLabel(self.tab)
            self.count2.setObjectName("count2")
            self.gridLayout_4.addWidget(self.count2, 1, 8, 1, 1)
            self.countLabel2 = QtWidgets.QLabel(self.tab)
            self.countLabel2.setObjectName("countLabel2")
            self.gridLayout_4.addWidget(self.countLabel2, 1, 7, 1, 1)
            self.flipBox1 = QtWidgets.QCheckBox(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.flipBox1.sizePolicy().hasHeightForWidth())
            self.flipBox1.setSizePolicy(sizePolicy)
            self.flipBox1.setObjectName("flipBox1")
            self.gridLayout_4.addWidget(self.flipBox1, 0, 0, 1, 2)
            self.reset2 = QtWidgets.QPushButton(self.tab,clicked= lambda: self.reset_it2())
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.reset2.sizePolicy().hasHeightForWidth())
            self.reset2.setSizePolicy(sizePolicy)
            self.reset2.setObjectName("reset2")
            self.gridLayout_4.addWidget(self.reset2, 3, 7, 1, 2)
            self.filesAftLabel = QtWidgets.QLabel(self.tab)
            self.filesAftLabel.setObjectName("filesAftLabel")
            self.gridLayout_4.addWidget(self.filesAftLabel, 1, 4, 1, 2)
            self.listAfter = ListboxWidgetAfter(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(2)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.listAfter.sizePolicy().hasHeightForWidth())
            self.listAfter.setSizePolicy(sizePolicy)
            self.listAfter.setMinimumSize(QtCore.QSize(0, 180))
            self.listAfter.setObjectName("listAfter")
            self.listAfter.setFont(QtGui.QFont("Arial",8))
            self.gridLayout_4.addWidget(self.listAfter, 2, 4, 1, 5)
            self.countLabel1 = QtWidgets.QLabel(self.tab)
            self.countLabel1.setObjectName("countLabel1")
            self.gridLayout_4.addWidget(self.countLabel1, 1, 2, 1, 1)
            self.filesBefLabel = QtWidgets.QLabel(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.filesBefLabel.sizePolicy().hasHeightForWidth())
            self.filesBefLabel.setSizePolicy(sizePolicy)
            self.filesBefLabel.setObjectName("filesBefLabel")
            self.gridLayout_4.addWidget(self.filesBefLabel, 1, 0, 1, 1)
            self.reset1 = QtWidgets.QPushButton(self.tab,clicked= lambda: self.reset_it1())
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.reset1.sizePolicy().hasHeightForWidth())
            self.reset1.setSizePolicy(sizePolicy)
            self.reset1.setObjectName("reset1")
            self.gridLayout_4.addWidget(self.reset1, 3, 2, 1, 2)
            self.count1 = QtWidgets.QLabel(self.tab)
            self.count1.setObjectName("count1")
            self.gridLayout_4.addWidget(self.count1, 1, 3, 1, 1)
            self.listBefore = ListboxWidget(self.tab)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(2)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.listBefore.sizePolicy().hasHeightForWidth())
            self.listBefore.setSizePolicy(sizePolicy)
            self.listBefore.setMinimumSize(QtCore.QSize(0, 180))
            self.listBefore.setObjectName("listBefore")
            self.listBefore.setFont(QtGui.QFont("Arial",8))
            self.gridLayout_4.addWidget(self.listBefore, 2, 0, 1, 4)
            self.gridLayout_3.addLayout(self.gridLayout_4, 1, 2, 2, 2)
            self.tabWidget.addTab(self.tab, "")
            self.ResultsPlots = QtWidgets.QWidget()
            self.ResultsPlots.setObjectName("ResultsPlots")
            self.tableView = QtWidgets.QTableView(self.ResultsPlots)
            self.tableView.setGeometry(QtCore.QRect(10, 10, 731, 391))
            self.tableView.setObjectName("tableView")
            self.tabWidget.addTab(self.ResultsPlots, "")
            self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
            self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
            MainWindow.setCentralWidget(self.centralwidget)
            self.menubar = QtWidgets.QMenuBar(MainWindow)
            self.menubar.setGeometry(QtCore.QRect(0, 0, 792, 26))
            self.menubar.setObjectName("menubar")
            self.menukjkj = QtWidgets.QMenu(self.menubar)
            self.menukjkj.setObjectName("menukjkj")
            MainWindow.setMenuBar(self.menubar)
            self.statusbar = QtWidgets.QStatusBar(MainWindow)
            self.statusbar.setObjectName("statusbar")
            MainWindow.setStatusBar(self.statusbar)
            # self.actionSettings = QtWidgets.QAction(MainWindow)
            # self.actionSettings.setObjectName("actionSettings")
            # self.actionExit = QtWidgets.QAction(MainWindow)
            # self.actionExit.setObjectName("actionExit")
            # self.menukjkj.addSeparator()
            # self.menukjkj.addAction(self.actionSettings)
            # self.menukjkj.addSeparator()
            # self.menukjkj.addAction(self.actionExit)
            # self.menubar.addAction(self.menukjkj.menuAction())

            self.retranslateUi(MainWindow)
            self.tabWidget.setCurrentIndex(0)
            QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def update_progress(self,progress):
        self.progressBar.setValue(progress)
    
    def finishedRun(self):
        self.run_it.setEnabled(True)
    
    def update_check(self):
        if ui.checkBox_range.isChecked():
            ui.chartRange.setEnabled(False)
        else:
            ui.chartRange.setEnabled(True)

    def startWorkInAThread(self):
        self.worker=WorkerThread()
        self.worker.progress_signal.connect(self.update_progress)
        ui.run_it.setEnabled(False)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.finishedRun)
        self.worker.start()
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Key_Delete:
            self._del_item()

    def _del_item(self):
        for item in self.selectedItems():
            QtWidgets.QListWidget.takeItem(self.row(item))
    
    def otvor(self):
        isExist = os.path.exists(savepath)
        if not isExist:
            os.makedirs(savepath)
        os.startfile(directoryOut)

    def save_it(self):
        root = tk.Tk()
        root.withdraw()
        global directoryOut
        directoryOut = fd.askdirectory(parent=root, title="Choose a directory")
        parser=ConfigParser()
        parser.read(app_path +"/config.ini")
        parser.set("savedirectory", "directoryOut",directoryOut)
        with open(app_path+"/config.ini", "w") as configfile:
            parser.write(configfile)

    def open_it1(self):
        root = tk.Tk()
        root.withdraw()
    
        pridaj = fd.askopenfilenames(parent=root, title='Select MAT files BEFORE',filetypes = ftypes)
        Ui_MainWindow.zoznamPrd += pridaj
        Ui_MainWindow.zoznamPrd.sort()
        self.listBefore.clear()
        for i in range(len( Ui_MainWindow.zoznamPrd)):
            self.listBefore.addItem((os.path.basename(str(Ui_MainWindow.zoznamPrd[i]))).rsplit(".",1)[0])
        self.count1.setText(str(len( Ui_MainWindow.zoznamPrd)))

    def open_it2(self):
        global odraty
        odraty=[]
        root = tk.Tk()
        root.withdraw()
        Ui_MainWindow.fileList=[]
        pridajPo = fd.askopenfilenames(parent=root, title='Select MAT files AFTER',filetypes = ftypes)
        Ui_MainWindow.zoznamPo += pridajPo
        Ui_MainWindow.zoznamPo.sort()
        self.listAfter.clear()
        for i in range(len(Ui_MainWindow.zoznamPo)):
            self.listAfter.addItem(str(os.path.basename(Ui_MainWindow.zoznamPo[i])).rsplit(".",1)[0])
            Ui_MainWindow.fileList.append(str(os.path.basename(Ui_MainWindow.zoznamPo[i])).rsplit(".",1)[0])
        self.count2.setText(str(len(Ui_MainWindow.zoznamPo)))

        for i in Ui_MainWindow.fileList:
            if len(i.split("_"))>3:
                odraty.append(i.split("_")[-3])
            else:
                odraty.append(i)
   
    def reset_it1(self):
        self.listBefore.clear()
        Ui_MainWindow.zoznamPrd=[]
        
        self.count1.setText("0")
        
    def reset_it2(self):
        self.listAfter.clear()        
        Ui_MainWindow.zoznamPo=[]
        Ui_MainWindow.fileList=[]
        self.count2.setText("0")
    
    def rege(zoznam):
            Ui_MainWindow.regex=[]
            for i in zoznam:
                legend=[]
                x=re.findall("[A-Z]{4}\d{3}-\d{2}",i)
                x=str(x).replace("'","")
                x=x.replace("[","")
                x=x.replace("]","")    
                Ui_MainWindow.regex.append(x)
            return Ui_MainWindow.regex
            
    def runit(self):
        
        ranger=ui.chartRange.displayText()
        ranger=ranger.replace(",",".")
        isExist = os.path.exists(savepath)
        if not isExist:
            os.makedirs(savepath)
        legendList=[]
        alla=[]
        alla=Ui_MainWindow.rege(Ui_MainWindow.fileList)
        print("Alla list: " + str(alla))
        print(Ui_MainWindow.fileList)
        print("zoznamPo: "+str(Ui_MainWindow.zoznamPo))
        if len(Ui_MainWindow.zoznamPo)==len(Ui_MainWindow.zoznamPrd) and (len(Ui_MainWindow.zoznamPo)>0):
            ui.logWindow.append(stamp("File processing has started."))
            avg_thk_bef=[]
            avg_thk_af=[]
            
            before={}
            for i in Ui_MainWindow.zoznamPrd:
                mat=loadmat(i)
                before[i]=mat["TF"]
            valuesBefore=list(before.values())
            before_sorted,dates_bef=(get_creation_sorted_dict(before))
            
            after={}
            for i in Ui_MainWindow.zoznamPo:
                mat = loadmat(i) 
                after[i]= mat["TF"]
            valuesAfter=list(after.values())
            after_sorted,dates_aft=(get_creation_sorted_dict(after))
            print("dates_aft:")
            print(dates_aft)

            total_steps=len(after_sorted)
            removal=[]
            removal_sorted_dict={}
            print(f"After keys: {after_sorted.keys()}")
            print(f"Before keys: {before_sorted.keys()}")
            for key in after_sorted.keys():
                removal_sorted_dict[key]=before_sorted[key]-after_sorted[key]
            print("Removal sorted:")
            print(removal_sorted_dict)

            deltaTTV=[]
            for key in after_sorted.keys():
                if (ui.flipBox1.isChecked()):
                    VB=np.fliplr(before_sorted[key])
                else: 
                    VB=before_sorted[key]
                if(ui.flipBox2.isChecked()):
                    VA=np.fliplr(after_sorted[key])
                else:
                    VA=after_sorted[key]
                removal.append(VB-VA)
                removal_sorted_dict[key]=(VB-VA)
                
            lotName=Ui_MainWindow.fileList[0].rsplit("_",3)[0] #nazov testu

            if ui.remMapLabel.isChecked():
                counter=0
                for key in after_sorted:
                    
                    fig, ((ax1,ax2),(ax3,ax4)) = plt.subplots(ncols=2,nrows=2)
                    axlist1=[ax1,ax2,ax3]
                    ax4.set_axis_off()
                    # fig, axes = plt.subplots(nrows=1, ncols=3)
                    Z=removal_sorted_dict[key]
                    print("Z: "+key)
                    print(Z)

                    if (ui.flipBox1.isChecked()):
                        VB=np.fliplr(before_sorted[key])
                    else: 
                        VB=before_sorted[key]
                    if(ui.flipBox2.isChecked()):
                        VA=np.fliplr(after_sorted[key])
                    else:
                        VA=after_sorted[key]

                    if (len(valuesAfter[0])<350):
                        print(len(valuesAfter[0]))
                        Z[280:290,110:190]="NaN"
                        VB[280:290,110:190]="NaN"
                        VA[280:290,110:190]="NaN"
                        ext=[-160,160,-160,160]
                        print("Je to 6inch")
                    else:
                        ext=[-210,210,-210,210]
                        print("Je to 8 inch")

                    wiwnu = np.nanstd(Z)/np.nanmean(Z)*100
                    deltaTTV = (np.nanmax(VA)-np.nanmin(VA))-(np.nanmax(VB)-np.nanmin(VB))
                    avg_thk_bef.append(np.nanmean(VB))
                    avg_thk_af.append(np.nanmean(VA))

                    # plt.contourf(X,Y,Z,scaleLevels,cmap="jet",alpha=1)
                    im1=ax1.imshow(VB, cmap="jet",interpolation='none', extent=ext)
                    im2=ax2.imshow(VA,cmap="jet",interpolation='none', extent=ext)
                    im3=ax3.imshow(Z,cmap="jet",interpolation='none', extent=ext)
                    for axis in axlist1:
                        axis.set_ylabel("y [mm]")
                        axis.set_xlabel("x [mm]")
                    # ax1.set_title("title")
                    plt.suptitle(f"WaferID: {key}_{dates_aft[key]}", fontsize="10")
                    ax1.set_title("Before")
                    ax2.set_title("After")
                    ax3.set_title("Removal")
                    im1.norm.autoscale([np.nanmin(VB), np.nanmax(VB)])
                    im2.norm.autoscale([np.nanmin(VA), np.nanmax(VA)])
                    im3.norm.autoscale([np.nanmin(Z), np.nanmax(Z)])
                    fig.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.35)
                    ax4.text(-0.2,0.90,"TTV1: %1.2f um" % (np.nanmax(VB)-np.nanmin(VB)),fontsize=6)
                    ax4.text(-0.2,0.85,"TTV2: %1.2f um" % (np.nanmax(VA)-np.nanmin(VA)),fontsize=6)
                    ax4.text(-0.2,0.8,"dTTV: %1.2f um" % deltaTTV, fontsize=6)
                    ax4.text(-0.2,0.75,"Avg removal: %1.2f um" % np.nanmean(Z), fontsize=6)
                    ax4.text(-0.2,0.70,"Min removal: %1.2f um" % np.nanmin(Z), fontsize=6)
                    ax4.text(-0.2,0.65,"Max removal: %1.2f um" % np.nanmax(Z), fontsize=6)
                    ax4.text(-0.2,0.6,"WIWNU: %1.2f %%" % wiwnu, fontsize=6)
                    fig.colorbar(im2).set_label("Thickness (um)",rotation=90)
                    fig.colorbar(im1)
                    cb=fig.colorbar(im3).set_label("Material removal (um)",rotation=90)
                    plt.figure(figsize=(10,10))
                    plt.tight_layout()
                    # cbar = plt.colorbar(format="%1.2f",ticks=ticks,pad=0.02).set_label("Removal (um)",rotation=90)
                    fig.savefig(directoryOut+"\\"+key+"_"+dates_aft[key]+".jpg", bbox_inches='tight', dpi=300)
                    plt.clf()
                    counter=counter+1
                    self.progress_signal.emit(int((counter)*100/total_steps))
                ui.logWindow.append(stamp("Removal maps are finished."))
                self.run_finished.emit()

                if ui.checkBox_range.isChecked()==True:
                    ranger=max(np.nanmax(array) for array in removal_sorted_dict.values())
                    goodCount=len(list(removal_sorted_dict.keys()))
                else:
                    goodCount=0
                    for key in removal_sorted_dict.keys():
                        polka=int((removal_sorted_dict[key].shape[0])/2)
                        print(f"Polka: {polka}")

                        if -5<np.nanmax(removal_sorted_dict[key][polka])<float(ranger)*2 and np.nanmin(removal_sorted_dict[key][polka])>-2.5:
                            goodCount=goodCount+1
                            print(f"Correct: {key}")
                            print(f"Polka: {key}: {removal_sorted_dict[key][polka]}")
                        else:
                            print(f"Incorrect: {key}")
                            print(f"Polka: {key}: {removal_sorted_dict[key][polka]}")
                        
                #farebne krivky v removal profile grafe - vytorenie palety farieb
                num_plots=goodCount
                print(f"Len removal {len(removal)}") 
                
            if ui.remProfsCheckBox.isChecked():
                custom_cycler=plt.cycler('color', plt.cm.jet(np.linspace(0, 1, num_plots)))
                plt.rcParams["axes.prop_cycle"]=custom_cycler
                fig,(ax1,ax2,ax3)=plt.subplots(ncols=1,nrows=3, figsize=(6,8), sharex=True)
            
                for key in after_sorted.keys():
                    if len(valuesBefore[0])>350:
                        if -5<np.nanmax(removal_sorted_dict[key][200])<float(ranger)*2 and np.nanmin(removal_sorted_dict[key][200])>-2.5:
                            print(removal_sorted_dict[key][200])
                            wafer_map=removal_sorted_dict[key]
                            legendList.append(key)
                            l=wafer_map[200]
                            k=np.linspace(-100,100,len(l))
                            m=np.diagonal(wafer_map)
                            # m=m[57:344]
                            m=crop_list_EE(3,m)
                            n=np.linspace(-100,100.5,len(m))  
                            p=wafer_map[:,200]
                            o=np.arange(-100,100.5,0.5)
                            
                            ax1.plot(k, l, linewidth=0.5)
                            ax2.plot(n,m,linewidth=0.5)
                            ax3.plot(o,p,linewidth=0.5)
                            print(f"len diag: {len(m)}")
                            print(f"Print diagonal: {m}")
                            print(f"Print horizontal: {l}")
                            print(f"print vertical: {p}")
                    else:
                        if -5<np.nanmax(removal_sorted_dict[key][150])<float(ranger)*2 and np.nanmin(removal_sorted_dict[key][150])>-2.5:
                            legendList.append(key)
                            wafer_map=removal_sorted_dict[key]
                            l=wafer_map[150]
                            k=np.linspace(-75,75,len(l))
                            # print(f"removal sorted dict {list(removal_sorted_dict.keys())[i]}")
                            print(f"Removal key: {key}")
                            m=np.diagonal(wafer_map)
                            m=crop_list_EE(3,m)
                            n=np.linspace(-75,75.5,len(m))  
                            p=wafer_map[:,150]
                            o=np.arange(-75,75.5,0.5)                                            
                            print(f"len diag: {len(m)}")
                            print(f"Print diagonal: {m}")
                            print(f"Print horizontal: {l}")
                            print(f"print vertical: {p}")
                            # plt.xlim(-75, 75)

                            ax1.plot(k, l, linewidth=0.5)
                            ax2.plot(n,m,linewidth=0.5)
                            ax3.plot(o,p,linewidth=0.5)

                if ui.checkBox_range.isChecked()==False:
                    ax1.set_ylim(0, float(ranger))
                    ax2.set_ylim(0, float(ranger))
                    ax3.set_ylim(0, float(ranger))
                else:
                    ranger=np.nanmax(removal_sorted_dict.values())

                coll(legendList)

                ax1.grid(True, linewidth=0.2, linestyle="--")
                ax2.grid(True, linewidth=0.2, linestyle="--")
                ax3.grid(True, linewidth=0.2, linestyle="--")

                ada1 = AnchoredDrawingArea(20,20, 0, 0,loc=4, pad=0., frameon=False)
                p1 = Circle((10,10),10,color="lightblue",alpha=0.4)
                arrow1=FancyArrow(0,10,18,0,color="red",head_width=2,alpha=0.6)
                ada1.da.add_artist(p1)
                ada1.da.add_artist(arrow1)
                ax1.add_artist(ada1)

                ada2 = AnchoredDrawingArea(20,20, 0, 0,loc=4, pad=0., frameon=False)
                p2 = Circle((10,10),10,color="lightblue",alpha=0.4)
                arrow2=FancyArrow(3,17,12,-12,color="red",head_width=2,alpha=0.6)
                ada2.da.add_artist(p2)
                ada2.da.add_artist(arrow2)
                ax2.add_artist(ada2)

                ada3 = AnchoredDrawingArea(20,20, 0, 0,loc=4, pad=0., frameon=False)
                p3 = Circle((10,10),10,color="lightblue",alpha=0.4)
                arrow3=FancyArrow(10,20,0,-18,color="red",head_width=2,alpha=0.6)
                ada3.da.add_artist(p3)
                ada3.da.add_artist(arrow3)
                ax3.add_artist(ada3)

                ax1.set_title("Removal profiles: "+lotName,fontsize=8,loc='left')
                ax1.set_ylabel("Removal (um)")
                ax1.legend(legendList,ncol=column,fancybox=True,shadow=True,loc="upper right",fontsize="4")
               
                ax2.set_ylabel("Removal (um)")
                
                ax3.set_ylabel("Removal (um)")
                
                ax3.set_xlabel("x (mm)")

                fig.subplots_adjust(hspace=0)
                plt.text(.01,.03,"Correct measurement count: "+str(goodCount), ha='left',va="bottom",fontsize=3, transform = ax1.transAxes,color="grey")
                plt.text(.01,.05,"Incorrect measurement count: "+str(len(removal)-goodCount), ha='left', va="bottom", fontsize=3, transform = ax1.transAxes,color="grey")
                plt.savefig(directoryOut+"\\"+"removalProfileChart_"+lotName+".jpg", bbox_inches='tight',dpi=600)
                plt.tight_layout(pad=0)
                plt.clf()
                ui.logWindow.append(stamp("Removal profile chart is finished."))
            else:
                custom_cycler=plt.cycler('color', plt.cm.jet(np.linspace(0, 1, num_plots)))
                plt.rcParams["axes.prop_cycle"]=custom_cycler
                fig,ax1=plt.subplots(ncols=1,nrows=1, figsize=(4.85,3.5))
                
                if ui.checkBox_range.isChecked()==False:
                    ax1.set_ylim(0, float(ranger))

                for key in after_sorted.keys():
                    if len(valuesBefore[0])>350:
                        if -5<np.nanmax(removal_sorted_dict[key][200])<float(ranger)*2 and np.nanmin(removal_sorted_dict[key][200])>-2.5:
                            wafer_map=removal_sorted_dict[key]
                            l=wafer_map[200]
                            k=np.linspace(-100,100,len(l))
                            legendList.append(key)

            
                            ax1.plot(k, l, linewidth=0.5)
                            print(f"Print horizontal: {l}")
                    else:
                        if -5<np.nanmax(removal_sorted_dict[key])<float(ranger)*2 and np.nanmin(removal_sorted_dict[key])>-2.5:
                            wafer_map=removal_sorted_dict[key]
                            l=wafer_map[150]
                            k=np.linspace(-75,75,len(l))
                            legendList.append(key)

                            print(f"Removal key: {key}")                                     
                            print(f"Print horizontal: {l}")
                            
                            ax1.plot(k, l, linewidth=0.5)

                coll(removal_sorted_dict)

                ax1.grid(True, linewidth=0.2, linestyle="--")

                ada1 = AnchoredDrawingArea(20,20, 0, 0,loc=4, pad=0., frameon=False)
                p1 = Circle((10,10),10,color="lightblue",alpha=0.4)
                arrow1=FancyArrow(0,10,18,0,color="red",head_width=2,alpha=0.6)
                ada1.da.add_artist(p1)
                ada1.da.add_artist(arrow1)
                ax1.add_artist(ada1)

                ax1.set_title("Removal profiles: "+lotName,fontsize=8,loc='left')
                ax1.set_ylabel("Removal (um)")
                ax1.legend(legendList,ncol=column,fancybox=True,shadow=True,loc="upper right",fontsize="4")
                ax1.set_xlabel("x (mm)")

                fig.subplots_adjust(hspace=0)
                plt.text(.01,.03,"Correct measurement count: "+str(goodCount), ha='left',va="bottom",fontsize=3, transform = ax1.transAxes,color="grey")
                plt.text(.01,.05,"Incorrect measurement count: "+str(len(removal)-goodCount), ha='left', va="bottom", fontsize=3, transform = ax1.transAxes,color="grey")
                plt.savefig(directoryOut+"\\"+"removalProfileChart_"+lotName+".jpg", bbox_inches='tight',dpi=600)
                plt.tight_layout(pad=0)
                plt.clf()
                ui.logWindow.append(stamp("Removal profile chart is finished."))
            
            if ui.csvDataLabel.isChecked():
                rem_csv=[]
                avg_csv=[]
                avg_thk_bef_csv=[]
                avg_thk_af_csv=[]
                variance_csv=[]
                ttv_csv=[]
                ttv_po_csv=[]
                deltaTTV_csv=[]
                wiwnu_csv=[]
                for key in removal_sorted_dict:
                    rem_csv.append(removal_sorted_dict[key][150])
                    Z=removal_sorted_dict[key]
                    Z[280:290,110:190]="NaN"
                    M=before_sorted[key]
                    A=after_sorted[key]
                    avg_thk_bef_csv.append(str(round((np.nanmean(M)),2)))
                    avg_thk_af_csv.append(str(round((np.nanmean(A)),2)))
                    if (np.nanmean(Z))<0.05:
                        wiwnu_csv.append("N/A")
                    else:
                        wiwnu_csv.append(str(round((np.nanstd(Z)/np.nanmean(Z)*100),2)))
                    ttv_csv.append(str(round((np.nanmax(M)-np.nanmin(M)),2)))
                    ttv_po_csv.append(str(round(np.nanmax(A)-np.nanmin(A),2)))
                    deltaTTV_csv.append(str(round((np.nanmax(A)-np.nanmin(A))-(np.nanmax(M)-np.nanmin(M)),2)))
                    avg_csv.append(str(round((np.nanmean(Z)),3)))
                    variance_csv.append(str(round(((np.nanmax(Z)-np.nanmin(Z))/(np.nanmean(Z))*100),2)))        
                d={"Name":list(removal_sorted_dict.keys()),"Date": list(dates_aft.values()),"THK_BF":avg_thk_bef_csv,"THK_AFT": avg_thk_af_csv,"REM(um)":avg_csv,"WIWNU(%)":wiwnu_csv,"Variance":variance_csv,"dTTV":deltaTTV_csv}
                df=pd.DataFrame(data=d)
                df["Date"]=df["Date"].astype(str)
                df.to_csv(directoryOut + "\\" + "Datafile_"+lotName+".csv",sep=',', index=False, encoding='utf-8')

                ui.logWindow.append(stamp("CSV file was generated."))
            ui.logWindow.append("Saved in: %s" % (directoryOut))
        else:
            ui.logWindow.append("No file or not equal file count!!!!!!")
        
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "WaferMaps tool"))
        self.logWindowLabel.setText(_translate("MainWindow", "Log Window"))
        self.headingLabel.setText(_translate("MainWindow", "Map export settings"))
        self.remMapLabel.setText(_translate("MainWindow", "Removal map"))
        self.remProfsCheckBox.setText(_translate("MainWindow", "Removal profiles at 45°, 90°"))
        self.csvDataLabel.setText(_translate("MainWindow", ".csv file - removal profile data"))
        self.label.setText(_translate("MainWindow", "Y-axis scale (um)"))
        self.uloziskoLabel.setText(_translate("MainWindow", "Map export directory"))
        self.otvoriskoLabel.setText(_translate("MainWindow", "Open output directory"))
        self.checkBox_range.setText(_translate("MainWindow", "Auto"))
        self.run_it.setText(_translate("MainWindow", "Start processing"))
        self.ulozisko.setText(_translate("MainWindow", "Save to..."))
        self.otvorisko.setText(_translate("MainWindow", "Output directory"))
        self.flipBox2.setText(_translate("MainWindow", "Si-face to H-bar"))
        self.loadDataAft.setText(_translate("MainWindow", "Load data AFTER"))
        self.loadDataBef.setText(_translate("MainWindow", "Load data BEFORE"))
        self.count2.setText(_translate("MainWindow", "0"))
        self.countLabel2.setText(_translate("MainWindow", "File count:"))
        self.flipBox1.setText(_translate("MainWindow", "Si-face to H-bar"))
        self.reset2.setText(_translate("MainWindow", "Reset"))
        self.filesAftLabel.setText(_translate("MainWindow", ".mat files After"))
        self.countLabel1.setText(_translate("MainWindow", "File count:"))
        self.filesBefLabel.setText(_translate("MainWindow", ".mat files Before"))
        self.reset1.setText(_translate("MainWindow", "Reset"))
        self.count1.setText(_translate("MainWindow", "0"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Main view"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.ResultsPlots), _translate("MainWindow", "Results&Plots"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.setWindowIcon(QtGui.QIcon(("icon_wafr.ico")))
    zoznamPo=[]
    zoznamPred=[]
    
    # ulozenie aplikacie, 2 pripady: python exe a direct scritp
    if getattr(sys, 'frozen', False):
        global application_path
        application_path = os.path.dirname(os.path.realpath(sys.executable))
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    parser.read(app_path +"/config.ini")
    directoryOut=parser.get("savedirectory", "directoryOut")
    chart_range=parser.get("chartrange","chart_range")
    if directoryOut == "":
        directoryOut=(application_path+"\output")
    MainWindow.show()
    sys.exit(app.exec())