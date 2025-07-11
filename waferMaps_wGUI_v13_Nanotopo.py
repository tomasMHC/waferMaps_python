# -*- coding: utf-8 -*-
# Kompilácia:
# python -m PyInstaller --noconfirm --noconsole --icon=icon_wafr.ico --onedir --upx-dir=C:\Users\zbnj4y\Documents\Programming\python-matfile\upx-4.0.1-win64 waferMaps_v08.py
# UI --> Py: python -m PyQt5.uic.pyuic -x xxxyyy.ui -o newPy.py
# EASY KOMPILACIA EXE: auto-py-to-exe
# Aktivacia virtual env: .\myenv_wafermap\Scripts\activate 

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QListWidget, QMainWindow
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
from ui_main_grid import Ui_MainWindow as Ui_main
from ui_side import Ui_MainWindow as Ui_side

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.fft import fft, fftfreq, fftshift
import scipy.stats as stats
from scipy.signal import medfilt2d
# idstructure refers to laserID: 
# onsemi: "SSSSddd-dd" ; 
# Ne-onsemi: "wdddddddSSSd"
# ID_STRUCTURE="wdddddddSSSd" # w - any character from a-Z or 1-9 or "_" ; d - digit, s - small letter, S - capital letter

mpl.use("PS")
plt.rcParams['font.family'] = 'Aptos'
plt.rcParams['font.sans-serif'] = "Aptos"
plt.rcParams.update({"axes.linewidth":0.6,"axes.labelpad":3, "axes.titlepad":5,
                     "axes.titlesize":8,"axes.labelsize":6,"figure.titlesize":5,
                     "xtick.labelsize": 6, "xtick.major.size":2.5,
                     "ytick.labelsize": 6,"ytick.major.width":0.5, "ytick.direction":"out","ytick.major.size":2.5,
                     "font.weight": "normal","axes.labelweight":"bold"})

class Backend(object):
    def __init__(self):
        self.pattern=config["idstructure"]["id_structure"]
    def crop_list_EE(self, ee_size, list):
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

    def point_on_circle_x(self, radius, angle_degrees, center_x):
        # Convert angle to radians
        angle_radians = np.deg2rad(angle_degrees)
        # Calculate x-coordinate
        x = center_x + radius * np.cos(angle_radians)
        return x
    def point_on_circle_y(self, radius, angle_degrees, center_x):
        # Convert angle to radians
        angle_radians = np.deg2rad(angle_degrees)
        # Calculate x-coordinate
        x = center_x + radius * np.sin(angle_radians)
        return x

    def draw_arrow(self, ax): # circle in the canvas coordinate                   
            ada = AnchoredDrawingArea(20,20, 0, 0,loc=4, pad=0., frameon=False)
            p = Circle((10,10),10,color="lightblue", alpha=0.4)
            arrow=FancyArrow(2,18,16,-16,color="red",head_width=2,alpha=0.5)
            ada.da.add_artist(p)
            ada.da.add_artist(arrow)
            ax.add_artist(ada)

    def stamp(self, str):
        current_time = datetime.now()
        time_stamp = current_time.timestamp()
        date_time = datetime.fromtimestamp(time_stamp)
        str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
        return(str_date_time+": " + str)

    def coll(self, lisst):
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

    def convert_to_regex(self, id_structure):
        regex_pattern=""
        # Initialize an empty regex pattern
        
        # Dictionary to map structure characters to regex patterns
        mapping = {
            'd': r'\d',  # digit
            's': r'[a-z]',  # letter
            '-': r'-',  # hyphen
            "S": r"[A-Z]",
            "w": r"\w",
            "_": r"_" }
        # Iterate over each character in the ID structure
        for char in id_structure:
            if char in mapping:
                regex_pattern += mapping[char]
            else:
                raise ValueError(f"Unsupported character '{char}' in ID structure")
       
        print(regex_pattern)
        # Return the complete regex pattern
        return regex_pattern

    def regex_laser(self, zoznam):
        lasery=[]
        chars_to_replace=["'","[","]","_"]
        for i in zoznam:
            i=i.split("/")[-1]
            print(i)
            x=re.findall(self.convert_to_regex(self.pattern),i)
            for char in chars_to_replace:
                x=str(x).replace(char,"")
            lasery.append(x) 
        seen=set()

        n=1
        for i in range(len(zoznam)):
            if lasery[i] not in seen:
                seen.add(lasery[i])
            else:
                lasery[i]="{laser}_{n}".format(laser=lasery[i],n=n)
                seen.add(lasery[i])
                n=n+1
        return lasery

    def text_date(self, filepath):
        y=filepath.rsplit("/",1)[1]
        x=re.findall("\d{14}PD",y)
        print(f"rsplit: {y}")
        x=str(x).replace("'","")
        x=x.replace("[","")
        x=x.replace("]","") 
        print(f"Datum z nazvu: {x}, length {len(x)}")
        if len(x)==16:
            return x
        else:
            return datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y%m%d%H%M%SPD")

    def get_creation_sorted_dict(self, dictionary):
        file_dates=[(key, dictionary.get(key), self.text_date(key)) for key in dictionary.keys()]
        sorted_file_dates=sorted(file_dates, key=lambda x: x[2])
        dates=list(zip(*sorted_file_dates))[2]
        print(f"dates in method: {dates}")
        sorted_list=self.regex_laser(list(zip(*sorted_file_dates))[0])
        print(f"keys after regex: {sorted_list}")
        sorted_values=list(zip(*sorted_file_dates))[1]
        print(f"len sorted after laser regex: {sorted_values}")
        return dict(zip(sorted_list, sorted_values)),dict(zip(sorted_list, dates))

class WorkerThread(QThread):
    
    progress_signal=pyqtSignal(int)
    run_finished=pyqtSignal()
    message_box=pyqtSignal(str)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def run(self):
        self.main_window.runit(self.progress_signal.emit)

class SideWindow(QMainWindow):
    def __init__(self):
        super(SideWindow, self).__init__()
        self.sui=Ui_side()
        self.sui.setupUi(self)
        self.sui.apply_button.clicked.connect(self.apply_it)
        self.sui.cancel_button.clicked.connect(self.close)
        self.sui.pattern.setText(backend.pattern)

    def apply_it(self):
        backend.pattern=self.sui.pattern.displayText()
        self.close()
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
                    mainWin.zoznamPrd.append(str(url.toLocalFile()))
                else:
                    mainWin.zoznamPrd.append(str(url.toString()))
            mainWin.zoznamPrd.sort()
            for i in range(len(mainWin.zoznamPrd)):
                self.addItem((os.path.basename(str(mainWin.zoznamPrd[i]))).split(".")[0])
        else:
            event.ignore()
        
        mainWin.ui.count1.setText(str(len(mainWin.zoznamPrd)))
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self._del_item()
            mainWin.cou=len(mainWin.zoznamPrd)
            mainWin.update_label1(mainWin.cou)
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
        mainWin.cou=len(mainWin.zoznamPrd)
        for item in self.selectedItems():
            ind=(self.row(item))
            del mainWin.zoznamPrd[ind]
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
        mainWin.fileList=[]
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.clear()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    mainWin.zoznamPo.append(str(url.toLocalFile()))
                else:
                    mainWin.zoznamPo.append(str(url.toString()))
        mainWin.zoznamPo.sort()
        print("zoznamPo drop: "+ str(mainWin.zoznamPo))
        for i in range(len(mainWin.zoznamPo)):

            self.addItem((os.path.basename(str(mainWin.zoznamPo[i]))).split(".")[0])
            mainWin.fileList.append(str(os.path.basename(mainWin.zoznamPo[i])).rsplit(".",1)[0])
        else:
            event.ignore()
        print("fileList: "+str(len(mainWin.fileList))+"----"+str(mainWin.fileList))       
        mainWin.ui.count2.setText(str(len(mainWin.zoznamPo)))
        for i in mainWin.fileList:
            if len(i.split("_"))>3:
                mainWin.odraty.append(i.split("_")[-3])
            else:
                mainWin.odraty.append(i)
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self._del_item()
            mainWin.coua=len(mainWin.zoznamPo)
            mainWin.update_label2(mainWin.coua)
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
        mainWin.coua=len(mainWin.zoznamPo)
        for item in self.selectedItems():
            ind=(self.row(item))
            del mainWin.zoznamPo[ind]
            del mainWin.fileList[ind]
            self.takeItem(self.row(item))

class MainWindow(QMainWindow, Ui_main):
    
    def __init__(self):
        super().__init__()
        self.before_sorted={}
        self.after_sorted={}
        self.regex=[]
        self.zoznamPrd=[]
        self.zoznamPo=[]
        self.fileList=[]
        self.odraty=[]
        self.ranger=chart_range
        self.ftypes = [("MAT files", "*.mat"), ("all files","*")]
        self.listAfter=ListboxWidgetAfter()

        self.ui = Ui_main()
        self.ui.setupUi(self)

        self.ui.otvorisko.clicked.connect(self.otvor)
        self.ui.ulozisko.clicked.connect(self.save_it)
        self.ui.run_it.clicked.connect(self.startWorkInAThread)
        self.ui.checkBox_range.clicked.connect(self.update_check)
        self.ui.loadDataAft.clicked.connect(self.open_it2)
        self.ui.loadDataBef.clicked.connect(self.open_it1)
        self.ui.reset2.clicked.connect(self.reset_it2)
        self.ui.reset1.clicked.connect(self.reset_it1)
        self.ui.pushButton.clicked.connect(self.open_side_window)        
        self.ui.chartRange.setText(chart_range)

        # self.ui.listWidget.addItems(self.after_sorted.keys())
        self.listBefore1=ListboxWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listBefore1.sizePolicy().hasHeightForWidth())
        self.listBefore1.setSizePolicy(sizePolicy)
        self.listBefore1.setMinimumSize(QtCore.QSize(100, 180))
        self.listBefore1.setObjectName("listBefore")
        self.ui.gridLayout_4.addWidget(self.listBefore1, 2, 0, 1, 13)

        self.listAfter1=ListboxWidgetAfter()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listAfter1.sizePolicy().hasHeightForWidth())
        self.listAfter1.setSizePolicy(sizePolicy)
        self.listAfter1.setMinimumSize(QtCore.QSize(100, 180))
        self.listAfter1.setObjectName("listAfter")
        self.ui.gridLayout_4.addWidget(self.listAfter1, 2, 13, 1, 9)

        self.ui.listWidget.itemDoubleClicked.connect(self.plot_data)
        
        self.ui.nanoTpghy_bef.toggled.connect(self.update_list)
        self.ui.nanoTpghy_aft.toggled.connect(self.update_list)

        self.canvas = MplCanvas(self)
        self.data=np.random.rand(10,10)
        self.im=self.canvas.axes.imshow(self.data, cmap="jet")
        self.cbar=self.canvas.fig.colorbar(self.im,ax=self.canvas.axes,cmap="jet")
        self.ui.gridLayout_9.addWidget(self.canvas)

    progress_signal=pyqtSignal(int)
    run_finished=pyqtSignal()
    message_box=pyqtSignal(str)

    def update_list(self):
        self.ui.listWidget.clear()
        if self.ui.nanoTpghy_bef.isChecked():
            self.ui.listWidget.addItems(self.before_sorted.keys())
        elif self.ui.nanoTpghy_aft.isChecked():
            self.ui.listWidget.addItems(self.after_sorted.keys())

    def update_label1(self,s):
        self.ui.count1.setText(str(s))
    def update_label2(self,s):
        self.ui.count2.setText(str(s))
    def goodCnt(self, dictionary):
        if self.ui.checkBox_range.isChecked()==True:
            self.ranger=max(np.nanmax(array) for array in dictionary.values())
            goodCount=len(list(dictionary.keys()))
        else:
            goodCount=0
            for key in dictionary.keys():
                polka=int((dictionary[key].shape[0])/2)
                # print(f"Polka: {polka}")

                if -5<np.nanmax(dictionary[key][polka])<float(self.ranger)*2 and np.nanmin(dictionary[key][polka])>-2.5:
                    goodCount=goodCount+1

        return goodCount
    def open_side_window(self):
        self.sui = SideWindow()
        self.sui.show()

    def update_progress(self,progress):
        self.ui.progressBar.setValue(progress)
    
    def finishedRun(self):
        self.ui.run_it.setEnabled(True)
    
    def update_check(self):
        if self.ui.checkBox_range.isChecked():
            self.ui.chartRange.setEnabled(False)
        else:
            self.ui.chartRange.setEnabled(True)

    def startWorkInAThread(self):
        self.worker=WorkerThread(self)
        self.worker.progress_signal.connect(self.update_progress)
        self.ui.run_it.setEnabled(False)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.finishedRun)
        self.worker.start()
            
    def otvor(self):
        isExist = os.path.exists(directoryOut)
        if not isExist:
            os.makedirs(directoryOut)
        os.startfile(directoryOut)

    def save_it(self):
        root = tk.Tk()
        root.withdraw()
        global directoryOut
        directoryOut = fd.askdirectory(parent=root, title="Choose a directory")
        parser=ConfigParser()
        if getattr(sys, 'frozen', False):
            app_path = os.path.dirname(os.path.realpath(sys.executable))
            a_path=app_path +"/_internal/config.ini"
        else:
            app_path = os.path.dirname(os.path.abspath(__file__))
            a_path=app_path+"/config.ini"
            
        parser.read(a_path)
        parser.set("savedirectory", "directoryOut",directoryOut)
        with open(a_path, "w") as configfile:
            parser.write(configfile)

    def open_it1(self):
        root = tk.Tk()
        root.withdraw()
        pridaj = fd.askopenfilenames(parent=root, title='Select MAT files BEFORE',filetypes = self.ftypes)
        self.zoznamPrd += pridaj
        self.zoznamPrd.sort()
        self.listBefore1.clear()
        for i in range(len( self.zoznamPrd)):
            self.listBefore1.addItem((os.path.basename(str(self.zoznamPrd[i]))).rsplit(".",1)[0])
        self.ui.count1.setText(str(len( self.zoznamPrd)))

    def open_it2(self):
        global odraty
        odraty=[]
        root = tk.Tk()
        root.withdraw()
        self.fileList=[]
        pridajPo = fd.askopenfilenames(parent=root, title='Select MAT files AFTER',filetypes = self.ftypes)
        self.zoznamPo += pridajPo
        self.zoznamPo.sort()
        self.listAfter1.clear()
        for i in range(len(self.zoznamPo)):
            self.listAfter1.addItem(str(os.path.basename(self.zoznamPo[i])).rsplit(".",1)[0])
            self.fileList.append(str(os.path.basename(self.zoznamPo[i])).rsplit(".",1)[0])
        self.ui.count2.setText(str(len(self.zoznamPo)))
        for i in self.fileList:
            if len(i.split("_"))>3:
                odraty.append(i.split("_")[-3])
            else:
                odraty.append(i)
   
    def reset_it1(self):
        self.listBefore1.clear()
        self.zoznamPrd=[]
        self.ui.count1.setText("0")
        
    def reset_it2(self):
        self.listAfter1.clear()        
        self.zoznamPo=[]
        self.fileList=[]
        self.ui.count2.setText("0")
    
    def line_plot(self,array):
        shp=np.shape(array)[0]
        lim=int(shp//4)
        return array[int(shp//2)], lim
    
                
    def csv_export(self, VA,VB,R):
        avg_csv=[]
        avg_thk_bef_csv=[]
        avg_thk_af_csv=[]
        variance_csv=[]
        ttv_csv=[]
        ttv_po_csv=[]
        deltaTTV_csv=[]
        wiwnu_csv=[]
        for key in R.keys():
            Z=R[key]
            M=VB[key]
            A=VA[key]
            avg_thk_bef_csv.append(float(round((np.nanmean(M)),2)))
            avg_thk_af_csv.append(float(round((np.nanmean(A)),2)))
            if (np.nanmean(Z))<0.05:
                wiwnu_csv.append("N/A")
            else:
                wiwnu_csv.append(float(round((np.nanstd(Z)/np.nanmean(Z)*100),2)))
            ttv_csv.append(float(round((np.nanmax(M)-np.nanmin(M)),2)))
            ttv_po_csv.append(float(round(np.nanmax(A)-np.nanmin(A),2)))
            deltaTTV_csv.append(float(round((np.nanmax(A)-np.nanmin(A))-(np.nanmax(M)-np.nanmin(M)),2)))
            avg_csv.append(float(round((np.nanmean(Z)),3)))
            variance_csv.append(float(round(((np.nanmax(Z)-np.nanmin(Z))/(np.nanmean(Z))*100),2)))
        
        d={"Name":list(R.keys()),"Date": list(self.dates_aft.values()),"THK_BF":avg_thk_bef_csv,"THK_AFT": avg_thk_af_csv,"REM(um)":avg_csv,"WIWNU(%)":wiwnu_csv,"Variance":variance_csv,"dTTV":deltaTTV_csv}
        df=pd.DataFrame(data=d)
        df["Date"]=df["Date"].astype(str)
        df.to_excel(directoryOut + "\\" + "Datafile_"+self.lotName+".xlsx", index=False)

        self.ui.logWindow.append(backend.stamp("XLSX Summary file was generated."))
        if self.boool==True:
            self.ui.logWindow.append(f"Saved in: {str(directoryOut)}")
    
    def map_export(self,before, after, diff, progress):
        plt.rcParams.update({"axes.linewidth":0.6,"axes.labelpad":3, "axes.titlepad":5,
                     "axes.titlesize":8,"axes.labelsize":6,"figure.titlesize":5,
                     "xtick.labelsize": 6, "xtick.major.size":2.5,
                     "ytick.labelsize": 6,"ytick.major.width":0.5, "ytick.direction":"out","ytick.major.size":2.5,
                     "font.weight": "normal","axes.labelweight":"bold"})
        counter=0
        for key in after:
            fig, ((ax1,ax2),(ax3,ax4)) = plt.subplots(ncols=2,nrows=2)
            axlist1=[ax1,ax2,ax3,ax4]
            Z=diff[key]
            VB=before[key]
            VA=after[key]
            
            if (len(VB)<350):
                Z[280:290,110:190]="NaN"
                VB[280:290,110:190]="NaN"
                VA[280:290,110:190]="NaN"
                ext=[-self.shejp,self.shejp,-self.shejp,self.shejp]
            else:
                ext=[-self.shejp,self.shejp,-self.shejp,self.shejp]

            wiwnu = np.nanstd(Z)/np.nanmean(Z)*100
            self.wiwnu_csv.append(wiwnu)
            avgrem=np.nanmean(Z)
            minrem=np.nanmin(Z)
            TTV2=(np.nanmax(VA)-np.nanmin(VA))
            TTV1=(np.nanmax(VB)-np.nanmin(VB))
            self.avg_thk_bef.append(np.nanmean(VB))
            self.avg_thk_af.append(np.nanmean(VA))

            im1=ax1.imshow(VB, cmap="jet",interpolation='spline16', extent=ext)
            im2=ax2.imshow(VA,cmap="jet",interpolation='spline16', extent=ext)
            im3=ax3.imshow(Z,cmap="jet",interpolation='spline16', extent=ext)
            for axis in axlist1:
                axis.set_ylabel("y [mm]")
                axis.set_xlabel("x [mm]")
    
            plt.suptitle(f"WaferID: {key}_{self.dates_aft[key]}", fontsize="10")
            ax1.set_title("Before")
            ax2.set_title("After")
            ax3.set_title("Removal")
            im1.norm.autoscale([np.nanmin(VB), np.nanmax(VB)])
            im2.norm.autoscale([np.nanmin(VA), np.nanmax(VA)])
            im3.norm.autoscale([np.nanmin(Z), np.nanmax(Z)])
            fig.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.35)
            
            WMBef,lim=self.line_plot(before[key]) 
            WMAft,lim=self.line_plot(after[key])
            k=np.linspace(-lim,lim,len(WMBef))
            ax4.plot(k,WMBef,linewidth=0.5, color="blue")
            ax4.plot(k,WMAft,linewidth=0.5,color="orange")
            ax4.grid(True, linewidth=0.2, linestyle="--")
            ax4.legend(("Before","After"),fancybox=True,shadow=True,loc="upper right",fontsize="4")
            ax4.set_title("Wafer THK profile")
            ax4.set_ylabel("THK (um)")

            ax1.text(lim*0.5,-lim*0.9,f"TTV1: {TTV1:.2f} um",fontsize=4)
            ax2.text(lim*0.5,-lim*0.9,f"TTV2: {TTV2:.2f} um",fontsize=4)
            ax3.text(lim*0.52,lim*0.9,f"Avg: {avgrem:.2f} um",fontsize=4)
            ax3.text(lim*0.52,lim*0.82,f"Min: {minrem:.2f} um",fontsize=4)
            ax3.text(lim*0.5,-lim*0.9,f"WIWNU: {wiwnu:.2f} %",fontsize=4)

            # ax4.text(-0.2,0.85,"TTV2: %1.2f um" % (np.nanmax(VA)-np.nanmin(VA)),fontsize=6)
            # ax4.text(-0.2,0.8,"dTTV: %1.2f um" % deltaTTV, fontsize=6)
            # ax4.text(-0.2,0.75,"Avg removal: %1.2f um" % np.nanmean(Z), fontsize=6)
            # ax4.text(-0.2,0.70,"Min removal: %1.2f um" % np.nanmin(Z), fontsize=6)
            # ax4.text(-0.2,0.65,"Max removal: %1.2f um" % np.nanmax(Z), fontsize=6)
            # ax4.text(-0.2,0.6,"WIWNU: %1.2f %%" % wiwnu, fontsize=6)
            fig.colorbar(im2).set_label("Thickness (um)",rotation=90)
            fig.colorbar(im1)
            fig.colorbar(im3).set_label("Material removal (um)",rotation=90)
            plt.figure(figsize=(10,10))
            plt.tight_layout()
            fig.savefig(directoryOut+"\\"+key+"_"+self.dates_aft[key]+".jpg", bbox_inches='tight', dpi=400)
            plt.close(fig)
            plt.close("all")

            counter=counter+1
            self.progress_signal.emit(int((counter)*100/self.total_steps))
            progress(int((counter)*100/self.total_steps))

    def profile_export(self, after, diff):
        plt.rcParams.update({"axes.linewidth":0.6,"axes.labelpad":3, "axes.titlepad":5,
                     "axes.titlesize": 12,"axes.labelsize":8,"figure.titlesize":5,
                     "xtick.labelsize": 8, "xtick.major.size":2.5,
                     "ytick.labelsize": 8,"ytick.major.width":0.5, "ytick.direction":"out","ytick.major.size":2.5,
                     "font.weight": "normal","axes.labelweight":"bold",
                     "legend.fontsize": 8})
           
        num_plots=self.goodCnt(diff)
        if num_plots==0:
            custom_cycler=plt.cycler('color',"b")
        else:
            custom_cycler=plt.cycler('color', plt.cm.jet(np.linspace(0, 1, num_plots)))
        plt.rcParams["axes.prop_cycle"]=custom_cycler

        fig,ax1=plt.subplots(nrows=1, ncols=1, figsize=(8,6))
        
        if self.ui.checkBox_range.isChecked()==False:
            ax1.set_ylim(0, float(self.ranger))
        try:
            for key in after.keys():
                if -5<np.nanmax(diff[key][self.shejp*2])<float(self.ranger)*2 and np.nanmin(diff[key][self.shejp*2])>-2.5:
                    wafer_map=diff[key]
                    l=wafer_map[self.shejp*2]
                    k=np.linspace(-self.shejp,self.shejp,len(l))
                    self.legendList.append(key)
                    ax1.plot(k, l, linewidth=.8)
        except:
            print(f"error {key}")
        
        backend.coll(self.legendList)

        ada1 = AnchoredDrawingArea(20,20, 0, 0,loc=4, pad=0., frameon=False)
        p1 = Circle((10,10),10,color="lightblue",alpha=0.4)
        arrow1=FancyArrow(0,10,18,0,color="red",head_width=2,alpha=0.6)
        ada1.da.add_artist(p1)
        ada1.da.add_artist(arrow1)
        ax1.add_artist(ada1)

        ax1.grid(True, linewidth=0.5, linestyle="--")
        ax1.set_title("Removal profiles: "+self.lotName,loc='left')
        ax1.set_ylabel("Removal (um)")
        ax1.legend(self.legendList,ncol=column,fancybox=True,shadow=True,loc="upper right")
        ax1.set_xlabel("x (mm)")

        fig.subplots_adjust(hspace=0)
        # plt.text(.01,.03,"Correct measurement count: "+str(num_plots), ha='left',va="bottom",fontsize=3, transform = ax1.transAxes,color="grey")
        # plt.text(.01,.05,"Incorrect measurement count: "+str(len(removal)-num_plots), ha='left', va="bottom", fontsize=3, transform = ax1.transAxes,color="grey")
        plt.savefig(directoryOut+"\\"+"removalProfileChart_"+self.lotName+".jpg", bbox_inches='tight',dpi=400)
        plt.close(fig)
        plt.close("all")
            
    def runit(self, progress_callback):
        self.ranger=self.ui.chartRange.displayText()
        self.ranger=self.ranger.replace(",",".")
        isExist = os.path.exists(directoryOut)
        if not isExist:
            os.makedirs(directoryOut)
        self.legendList=[]
        self.boool=True
        if len(self.zoznamPo)==len(self.zoznamPrd) and (len(self.zoznamPo)>0):
            self.ui.logWindow.append(backend.stamp("File processing has started."))
            self.avg_thk_bef=[]
            self.avg_thk_af=[]
            self.lotName=self.fileList[0].rsplit("_",3)[0] #nazov testu
            before={}
            after={}
            self.wiwnu_csv=[]
            removal=[]
            removal_sorted_dict={}
            a=True
            for i in self.zoznamPrd:
                mat=loadmat(i,variable_names=["TF"])
                before[i]=mat["TF"]
            before_sorted,dates_bef=(backend.get_creation_sorted_dict(before))
            for i in self.zoznamPo:
                mat=loadmat(i,variable_names=["TF"]) 
                after[i]= mat["TF"]
            after_sorted,self.dates_aft=(backend.get_creation_sorted_dict(after))
            self.after_sorted=after_sorted
            self.before_sorted=before_sorted

            print("dates_aft:")
            print(self.dates_aft)
            self.total_steps=len(after_sorted)
            
            print(f"After keys: {after_sorted.keys()}")
            print(f"Before keys: {before_sorted.keys()}")

            while a==True:
                if after_sorted.keys() == before_sorted.keys():
                    for key in after_sorted.keys():
                        if (self.ui.flipBox1.isChecked()):
                            VB=np.fliplr(before_sorted[key])
                            before_sorted[key]=VB
                        else: 
                            VB=before_sorted[key]

                        if(self.ui.flipBox2.isChecked()):
                            VA=np.fliplr(after_sorted[key])
                            after_sorted[key]=VA
                        else:
                            VA=after_sorted[key]
                        removal.append(VB-VA)
                        removal_sorted_dict[key]=(VB-VA)
                    a=False
                else:
                    return self.ui.logWindow.append("Not equal lists!")
            self.shejp=int(np.shape(VA)[0]/4)

            # Removal maps + one-directional removal profiles
            if self.ui.remMapLabel.isChecked():
                self.map_export(before_sorted,after_sorted,removal_sorted_dict,progress_callback)
                self.ui.logWindow.append(backend.stamp(f"Removal maps are finished."))
                self.run_finished.emit()   

                self.profile_export(after_sorted,removal_sorted_dict)
                self.ui.logWindow.append(backend.stamp(f"Removal profile chart is finished."))

                if self.boool==True:
                    self.ui.logWindow.append(f"Saved in: {str(directoryOut)}")
                    self.boool=False
                
                self.csv_export(before_sorted,after_sorted,removal_sorted_dict)

            # 3-directional removal profiles 
            if self.ui.remProfsCheckBox.isChecked() and self.ui.remMapLabel.isChecked():
                # Three directions removal profiles
                plt.rcParams.update({"axes.linewidth":0.6,"axes.labelpad":3, "axes.titlepad":5,
                     "axes.titlesize":8,"axes.labelsize":6,"figure.titlesize":5,
                     "xtick.labelsize": 6, "xtick.major.size":2.5,
                     "ytick.labelsize": 6,"ytick.major.width":0.5, "ytick.direction":"out","ytick.major.size":2.5,
                     "font.weight": "normal","axes.labelweight":"bold"})
                num_plots=self.goodCnt(removal_sorted_dict)
                custom_cycler=plt.cycler('color', plt.cm.jet(np.linspace(0, 1, num_plots)))
                plt.rcParams["axes.prop_cycle"]=custom_cycler
                fig,(ax1,ax2,ax3)=plt.subplots(ncols=1,nrows=3, figsize=(6,8), sharex=True)
            
                for key in after_sorted.keys():
                    if -5<np.nanmax(removal_sorted_dict[key][self.shejp*2])<float(self.ranger)*2 and np.nanmin(removal_sorted_dict[key][self.shejp*2])>-2.5:
                        wafer_map=removal_sorted_dict[key]
                        self.legendList.append(key)
                        l=wafer_map[self.shejp*2]
                        k=np.linspace(-self.shejp,self.shejp,len(l))
                        m=np.diagonal(wafer_map)
                        # m=m[57:344]
                        m=backend.crop_list_EE(3,m)
                        n=np.linspace(-self.shejp,self.shejp,len(m))  
                        p=wafer_map[:,self.shejp*2]
                        o=np.linspace(-self.shejp,self.shejp,len(p))
                        
                        ax1.plot(k, l, linewidth=0.5)
                        ax2.plot(n, m, linewidth=0.5)
                        ax3.plot(o, p, linewidth=0.5)

                if self.ui.checkBox_range.isChecked()==False:
                    ax1.set_ylim(0, float(self.ranger))
                    ax2.set_ylim(0, float(self.ranger))
                    ax3.set_ylim(0, float(self.ranger))
                else:
                    self.ranger=np.nanmax(removal_sorted_dict.values())
        
                backend.coll(self.legendList)

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

                ax1.set_title("Removal profiles: "+self.lotName,fontsize=8,loc='left')
                ax1.set_ylabel("Removal (um)")
                ax1.legend(self.legendList,ncol=column,fancybox=True,shadow=True,loc="upper right",fontsize="4")
               
                ax2.set_ylabel("Removal (um)")
                ax3.set_ylabel("Removal (um)")
                ax3.set_xlabel("x (mm)")

                fig.subplots_adjust(hspace=0)
                plt.text(.01,.03,"Correct measurement count: "+str(num_plots), ha='left',va="bottom",fontsize=3, transform = ax1.transAxes,color="grey")
                plt.text(.01,.05,"Incorrect measurement count: "+str(len(removal)-num_plots), ha='left', va="bottom", fontsize=3, transform = ax1.transAxes,color="grey")
                plt.savefig(directoryOut+"\\"+"removalProfileChart_"+self.lotName+".jpg", bbox_inches='tight',dpi=400)
                plt.tight_layout(pad=0)
                plt.close(fig)
                # plot_scatter(wiwnu,avgrem)
                plt.close("all")
                self.ui.logWindow.append(backend.stamp(f"Removal profile chart is finished."))

                self.csv_export(before_sorted,after_sorted,removal_sorted_dict)
            
            elif self.ui.csvDataLabel.isChecked():
                self.csv_export(before_sorted,after_sorted,removal_sorted_dict)
                
            elif self.ui.csvDataLabel.isChecked()==False and self.ui.remProfsCheckBox.isChecked()==False and self.ui.remMapLabel.isChecked()==False:
                self.ui.logWindow.append(f"Please choose an action :)")
        else:
            self.ui.logWindow.append("No file or not equal file count!!!!!!")



    def plot_data(self, item):
            # self.canvas = MplCanvas(self)
            # self.ui.chart_space.addWidget(self.canvas)
            ext=[-self.shejp,self.shejp,-self.shejp,self.shejp]
            sigma=int(self.ui.significance_level.displayText())
            label = item.text()
            if self.ui.nanoTpghy_bef.isChecked()==True:
                y = self.before_sorted[label]
            elif self.ui.nanoTpghy_aft.isChecked()==True:
                y = self.after_sorted[label]

            # self.canvas.axes.clear()
    
            self.data=self.nanotopography(y)
            self.im.set_data(self.data)
            self.im.set_extent(ext)
            mean=np.nanmean(self.data)
            std=np.nanstd(self.data)
            self.im.set_clim(vmin=mean-std*sigma,vmax=mean+std*sigma)
            # self.im.set_clim(vmin=self.data.min(), vmax=self.data.max())
            self.canvas.axes.set_title(f"Plot for {label}")
            self.canvas.draw()
            
    
    def nanotopography(self,thicknessMatrix):
        c=0
        sa_roughness=[]
        keys=[]
        windowSize = int(self.ui.kernel_size.displayText())
        if windowSize % 2 == 0:
            windowSize = windowSize + 1 
            self.ui.kernel_size.setText(str(windowSize))
        # if thicknessMatrix.shape[1] >= 401:
        #     X, Y = np.meshgrid(np.arange(-100, 100.5, 0.5), np.arange(-100, 100.5, 0.5))
        # else:
        #     X, Y = np.meshgrid(np.arange(-75, 75.5, 0.5), np.arange(-75, 75.5, 0.5))

        # Step 4: Apply the median filter
        filteredMatrix = medfilt2d(thicknessMatrix, [windowSize, windowSize])

        # Extract the nanotopography (short wavelength thickness variation)
        nanotopography = thicknessMatrix - filteredMatrix

        return nanotopography
        # # Step 5: Transform the matrix and vectors into polar coordinates
        # theta, rho = np.arctan2(Y, X), np.hypot(X, Y)

        # # Step 6: Extract vector of values that corresponds to R/2
        # half_radius = np.max(rho) / 1.7
        # indices = np.abs(rho - half_radius) < 0.1  # Adjust the tolerance as needed
        # theta_half_radius = theta[indices]
        # nanotopography_half_radius = nanotopography[indices]

        # # Step 7: Compute the frequency components
        # freq = fft(np.nan_to_num(nanotopography_half_radius))

        # # Optional: Sort the data for a smoother plot
        # sortIdx = np.argsort(theta_half_radius)
        # theta_half_radius_sorted = theta_half_radius[sortIdx]
        # nanotopography_half_radius_sorted = nanotopography_half_radius[sortIdx]

        # wafer_size=np.shape(thicknessMatrix)[0]//2

        # l=filtered_data[wafer_size]
        # k=np.linspace(-wafer_size//2,wafer_size//2,len(l))
        # m=thicknessMatrix[wafer_size]
        
        # # Step 8: Display the original and nanotopography matrices
        # fig, axs = plt.subplots(ncols=2, nrows=3, figsize=(12, 15))

        # axs[0, 0].contourf(X, Y, thicknessMatrix, 100, cmap='jet')
        # axs[0, 0].set_aspect('equal')
        # axs[0, 0].set_title(f'{key} Thickness')
        # fig.colorbar(axs[0, 0].contourf(X, Y, thicknessMatrix, 100, cmap='jet'), ax=axs[0, 0])

        # axs[0, 1].contourf(X, Y, filtered_data, 100, cmap='jet')
        # axs[0, 1].set_aspect('equal')
        # axs[0, 1].set_title(f'{key} NanoWaviness')
        # fig.colorbar(axs[0, 1].contourf(X, Y, filtered_data, 100, cmap='jet'), ax=axs[0, 1])
        # circle=plt.Circle((0,0),radius=half_radius,edgecolor="red", facecolor="none",linestyle="--",alpha=0.6)
        # axs[0, 1].add_patch(circle)
        # filtered_data_zero=filtered_data+np.abs(np.nanmin(filtered_data))
        # sa_roughness.append(np.nanmean(filtered_data_zero))

        # # axs[1, 0].plot(theta_half_radius_sorted, nanotopography_half_radius_sorted, 'r-o', markerfacecolor='r', markersize=1)
        # # axs[1, 0].set_xlim([-np.pi, np.pi])
        # # axs[1, 0].set_xlabel('Theta (radians)')
        # # axs[1, 0].set_ylabel('Waviness (µm)')
        # # axs[1, 0].set_title(f'{wafer_ID} Angular Waviness')
        # # axs[1, 0].grid(True)

        # axs[1, 0].plot(k,m)
        # axs[1, 0].set_title(f'{key} THK center profile')
        # axs[1, 0].grid(True)
        # axs[1, 0].set_ylabel('THK (um)')
        # axs[1, 0].set_xlabel('x distance from center (mm)')

        # # axs[1, 1].plot(np.abs(freq))
        # axs[1, 1].plot(k,l,linewidth=0.8)
        # axs[1, 1].set_title(f'{key} Waviness center profile')
        # axs[1, 1].grid(True)
        # axs[1, 1].set_ylabel('Filtered THK (um)')
        # axs[1, 1].set_xlabel('x distance from center (mm)')
    

        # axs[2,0].plot(theta_half_radius_sorted, nanotopography_half_radius_sorted, 'b')
        # axs[2,0].set_xlim([-np.pi, np.pi])
        # axs[2,0].set_xlabel('Theta (radians)')
        # axs[2,0].set_ylabel('Waviness (µm)')
        # axs[2,0].set_title(f'{key} Angular Waviness')
        # axs[2,0].grid(True)

        # fftX=fftfreq(len(nanotopography_half_radius_sorted),1/100)
        # fftX=fftshift(fftX)
        # fftX=fftX[len(fftX)//2:len(fftX)]
        # fourier1D=fft(nanotopography_half_radius_sorted)
        # shifted=fftshift(fourier1D)
        # shifted=shifted[len(shifted)//2:len(shifted)]
        # axs[2,1].plot(fftX,shifted, 'r', markersize=1)


        # axs[2,1].set_ylabel('Amplitude')
        # axs[2,1].set_xlabel('Frequency')
        # axs[2,1].axhline(0.3, linestyle="--")
        # axs[2,1].axhline(-0.3, linestyle="--")
        # # axs[1].set(xlim=(len(fourier1D)//2,len(fourier1D)))
        # axs[2,1].set_title(f'{key} fft')
        # axs[2,1].grid(True)

        # fig_file3 = f'{os.path.dirname(file)}/{key} Nano-waviness.png'
        # plt.savefig(fig_file3, bbox_inches="tight",dpi=300)
        # plt.close()
        # keys.append(key)
        # c=c+(1/files_count)*100

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(constrained_layout=True)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)


if __name__ == "__main__":
    import sys
    config=ConfigParser()
    # ulozenie aplikacie, 2 pripady: python exe a direct scritp
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(os.path.realpath(sys.executable))
        font_dirs = application_path+"/_internal/Aptos"
        config.read(application_path +"/_internal/config.ini")
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
        config.read(application_path +"/config.ini")
        font_dirs = application_path+"/Aptos"

    font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
    for font_file in font_files:
        font_manager.fontManager.addfont(font_file)
    directoryOut=config['savedirectory']["directoryout"]
    chart_range=config["chartrange"]["chart_range"]

    if directoryOut == "":
        directoryOut=(application_path+"\output")

    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    parser= ConfigParser()
    backend=Backend()
    # MainWindow = QtWidgets.QMainWindow()
    mainWin.setWindowIcon(QtGui.QIcon(("_internal/icon_wafr.ico")))    
    mainWin.show()
    sys.exit(app.exec_())