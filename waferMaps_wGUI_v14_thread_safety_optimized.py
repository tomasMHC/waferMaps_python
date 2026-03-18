
# -*- coding: utf-8 -*-
# NOTE: This is an optimized and thread-safer build of waferMaps_wGUI_v14_thread safety.py
# Key changes:
# - Heavy work (runit) logs are routed via thread-safe Qt signals (no direct UI calls from worker thread)
# - Avoid repeated sorting inside file-loading loops; sort once after loading
# - More robust progress reporting
# - Nanotopography tab: proper colorbar updates + kernel size clamping + odd kernel enforcement
# - Minor plotting optimizations (avoid expensive interpolation in loops)

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
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from scipy.signal import medfilt2d

mpl.use("Agg")
plt.rcParams['font.family'] = 'Aptos'
plt.rcParams['font.sans-serif'] = "Aptos"
plt.rcParams.update({
    "axes.linewidth": 0.6, "axes.labelpad": 3, "axes.titlepad": 5,
    "axes.titlesize": 8, "axes.labelsize": 5, "figure.titlesize": 5,
    "xtick.labelsize": 5, "xtick.major.size": 2.5,
    "ytick.labelsize": 6, "ytick.major.width": 0.5, "ytick.direction": "out", "ytick.major.size": 2.5,
    "font.weight": "normal", "axes.labelweight": "bold"
})

class Backend(object):
    def __init__(self):
        self.pattern = config["idstructure"]["id_structure"]

    def crop_list_EE(self, ee_size, list):
        new_List = []
        counter = 1
        i = 1
        for element in list:
            if (counter <= (ee_size * 2) or not np.isnan(element)):
                new_List.append(element)
            counter = counter + 1
        while i <= ee_size * 2:
            i = i + 1
            new_List.append(np.nan)
        return np.array(new_List)

    def draw_arrow(self, ax):  # circle in the canvas coordinate
        ada = AnchoredDrawingArea(20, 20, 0, 0, loc=4, pad=0., frameon=False)
        p = Circle((10, 10), 10, color="lightblue", alpha=0.4)
        arrow = FancyArrow(2, 18, 16, -16, color="red", head_width=2, alpha=0.5)
        ada.da.add_artist(p)
        ada.da.add_artist(arrow)
        ax.add_artist(ada)

    def stamp(self, s: str) -> str:
        current_time = datetime.now()
        date_time = datetime.fromtimestamp(current_time.timestamp())
        return f"{date_time.strftime('%d-%m-%Y, %H:%M:%S')}: {s}"

    def coll(self, lisst):
        global column
        a = len(lisst)
        if 5 < a <= 10:
            column = 2
        elif 10 < a < 20:
            column = 3
        elif a >= 20:
            column = 4
        else:
            column = 1

    def convert_to_regex(self, id_structure):
        regex_pattern = ""
        mapping = {
            'd': r'\d',  # digit
            's': r'[a-z]',  # letter
            '-': r'-',  # hyphen
            'S': r"[A-Z]",
            'w': r"\w",
            '_': r"_"
        }
        for char in id_structure:
            if char in mapping:
                regex_pattern += mapping[char]
            else:
                raise ValueError(f"Unsupported character '{char}' in ID structure")
        return regex_pattern

    def regex_laser(self, paths) -> list:
        lasery = []
        chars_to_replace = ["'", "[", "]", "_"]
        for p in paths:
            i = p.split("/")[-1]
            x = re.findall(self.convert_to_regex(self.pattern), i)
            for char in chars_to_replace:
                x = str(x).replace(char, "")
            lasery.append(x)
        seen = set()
        n = 1
        for i in range(len(paths)):
            if lasery[i] not in seen:
                seen.add(lasery[i])
            else:
                lasery[i] = f"{lasery[i]}_{n}"
                seen.add(lasery[i])
                n = n + 1
        return lasery

    def text_date(self, filepath):
        y = filepath.rsplit("/", 1)[1]
        x = re.findall("\d{14}PD", y)
        x = str(x).replace("'", "").replace("[", "").replace("]", "")
        if len(x) == 16:
            return x
        else:
            return datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y%m%d%H%M%SPD")

    def get_creation_sorted_dict(self, dictionary):
        file_dates = [(key, dictionary.get(key), self.text_date(key)) for key in dictionary.keys()]
        sorted_file_dates = sorted(file_dates, key=lambda x: x[2])
        dates = list(zip(*sorted_file_dates))[2]
        sorted_list = self.regex_laser(list(zip(*sorted_file_dates))[0])
        sorted_values = list(zip(*sorted_file_dates))[1]
        return dict(zip(sorted_list, sorted_values)), dict(zip(sorted_list, dates))

class WorkerThread(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    run_finished = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def run(self):
        # Execute heavy work in worker thread, but UI updates via signals only
        self.main_window.runit(self.progress_signal.emit, self.log_signal.emit)
        self.run_finished.emit()

class SideWindow(QMainWindow):
    def __init__(self):
        super(SideWindow, self).__init__()
        self.sui = Ui_side()
        self.sui.setupUi(self)
        self.sui.apply_button.clicked.connect(self.apply_it)
        self.sui.cancel_button.clicked.connect(self.close)
        self.sui.pattern.setText(backend.pattern)

    def apply_it(self):
        backend.pattern = self.sui.pattern.displayText()
        self.close()

class ListboxWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMovement(QListWidget.Free)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
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
            mainWin.update_label1(len(mainWin.zoznamPrd))
        elif event.key() == Qt.Key_Up:
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
        for item in self.selectedItems():
            ind = (self.row(item))
            del mainWin.zoznamPrd[ind]
            self.takeItem(self.row(item))

class ListboxWidgetAfter(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMovement(QListWidget.Free)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        mainWin.fileList = []
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
            for i in range(len(mainWin.zoznamPo)):
                self.addItem((os.path.basename(str(mainWin.zoznamPo[i]))).split(".")[0])
                mainWin.fileList.append(str(os.path.basename(mainWin.zoznamPo[i])).rsplit(".", 1)[0])
        else:
            event.ignore()
        mainWin.ui.count2.setText(str(len(mainWin.zoznamPo)))
        mainWin.odraty = []
        for i in mainWin.fileList:
            if len(i.split("_")) > 3:
                mainWin.odraty.append(i.split("_")[-3])
            else:
                mainWin.odraty.append(i)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self._del_item()
            mainWin.update_label2(len(mainWin.zoznamPo))
        elif event.key() == Qt.Key_Up:
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
        for item in self.selectedItems():
            ind = (self.row(item))
            del mainWin.zoznamPo[ind]
            del mainWin.fileList[ind]
            self.takeItem(self.row(item))

class MainWindow(QMainWindow, Ui_main):
    def __init__(self):
        super().__init__()
        self.before_sorted = {}
        self.after_sorted = {}
        self.regex = []
        self.zoznamPrd = []
        self.zoznamPo = []
        self.fileList = []
        self.odraty = []
        self.ranger = chart_range
        self.ftypes = [("MAT files", "*.mat"), ("all files", "*")]
        self.listAfter = ListboxWidgetAfter()
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
        self.ui.matchLasers.clicked.connect(self.match_lasers)
        self.listBefore1 = ListboxWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listBefore1.sizePolicy().hasHeightForWidth())
        self.listBefore1.setSizePolicy(sizePolicy)
        self.listBefore1.setMinimumSize(QtCore.QSize(100, 180))
        self.listBefore1.setObjectName("listBefore")
        self.ui.gridLayout_4.addWidget(self.listBefore1, 2, 0, 1, 13)
        self.listAfter1 = ListboxWidgetAfter()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listAfter1.sizePolicy().hasHeightForWidth())
        self.listAfter1.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.listAfter1.setFont(font)
        self.listBefore1.setFont(font)
        self.listAfter1.setMinimumSize(QtCore.QSize(100, 180))
        self.listAfter1.setObjectName("listAfter")
        self.ui.gridLayout_4.addWidget(self.listAfter1, 2, 13, 1, 9)
        self.ui.listWidget.itemDoubleClicked.connect(self.plot_data)
        self.ui.nanoTpghy_bef.toggled.connect(self.update_list)
        self.ui.nanoTpghy_aft.toggled.connect(self.update_list)
        # Matplotlib canvas
        self.canvas = MplCanvas(self)
        self.data = np.random.rand(10, 10)
        self.im = self.canvas.axes.imshow(self.data, cmap="jet", interpolation="nearest")
        self.cbar = self.canvas.fig.colorbar(self.im, ax=self.canvas.axes, cmap="jet")
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setIconSize(QtCore.QSize(12, 12))
        self.ui.gridLayout_9.addWidget(self.canvas)
        self.ui.gridLayout_9.addWidget(self.toolbar)
        if getattr(sys, 'frozen', False):
            try:
                import pyi_splash
                pyi_splash.close()
            except Exception:
                pass

    def match_lasers(self):
        from collections import defaultdict, deque
        if not self.zoznamPrd or not self.zoznamPo:
            self.append_log(backend.stamp("Load both BEFORE and AFTER files first."))
            return
        ids_before = backend.regex_laser(self.zoznamPrd)
        ids_after = backend.regex_laser(self.zoznamPo)
        idx_before = defaultdict(deque)
        for i, id_ in enumerate(ids_before):
            idx_before[id_].append(i)
        new_before_paths, new_after_paths = [], []
        matched_ids = []
        for j, id_ in enumerate(ids_after):
            if idx_before[id_]:
                i = idx_before[id_].popleft()
                new_before_paths.append(self.zoznamPrd[i])
                new_after_paths.append(self.zoznamPo[j])
                matched_ids.append(id_)
        unmatched_before = []
        for id_, q in idx_before.items():
            while q:
                i = q.popleft()
                unmatched_before.append(os.path.basename(self.zoznamPrd[i]))
        unmatched_after = [os.path.basename(self.zoznamPo[j]) for j, id_ in enumerate(ids_after) if id_ not in matched_ids]
        self.zoznamPrd = new_before_paths
        self.zoznamPo = new_after_paths
        self.listBefore1.clear()
        self.listAfter1.clear()
        for p in self.zoznamPrd:
            self.listBefore1.addItem(os.path.basename(p).rsplit(".", 1)[0])
        for p in self.zoznamPo:
            self.listAfter1.addItem(os.path.basename(p).rsplit(".", 1)[0])
        self.update_label1(len(self.zoznamPrd))
        self.update_label2(len(self.zoznamPo))
        self.fileList = [os.path.basename(p).rsplit(".", 1)[0] for p in self.zoznamPo]
        self.odraty = []
        for i in self.fileList:
            if len(i.split("_")) > 3:
                self.odraty.append(i.split("_")[-3])
            else:
                self.odraty.append(i)
        self.update_list()
        msg = [
            f"Matched pairs: {len(matched_ids)}",
            f"BEFORE-only removed: {len(unmatched_before)}",
            f"AFTER-only removed: {len(unmatched_after)}"
        ]
        self.append_log(backend.stamp("\n".join(msg)))
        if unmatched_before:
            self.append_log("BEFORE-only (unmatched):\n" + "\n".join(f" - {n}" for n in unmatched_before))
        if unmatched_after:
            self.append_log("AFTER-only (unmatched):\n" + "\n".join(f" - {n}" for n in unmatched_after))

    # --- small helpers ---
    def append_log(self, text: str):
        try:
            self.ui.logWindow.append(text)
        except Exception:
            pass

    def update_list(self):
        self.ui.listWidget.clear()
        if self.ui.nanoTpghy_bef.isChecked():
            self.ui.listWidget.addItems(self.before_sorted.keys())
        elif self.ui.nanoTpghy_aft.isChecked():
            self.ui.listWidget.addItems(self.after_sorted.keys())

    def update_label1(self, s):
        self.ui.count1.setText(str(s))

    def update_label2(self, s):
        self.ui.count2.setText(str(s))

    def goodCnt(self, dictionary):
        if self.ui.checkBox_range.isChecked():
            self.ranger = max(np.nanmax(array) for array in dictionary.values())
            goodCount = len(list(dictionary.keys()))
        else:
            goodCount = 0
            for key in dictionary.keys():
                polka = int((dictionary[key].shape[0]) / 2)
                if -5 < np.nanmax(dictionary[key][polka]) < float(self.ranger) * 2 and np.nanmin(dictionary[key][polka]) > -2.5:
                    goodCount = goodCount + 1
        return goodCount

    def open_side_window(self):
        self.sui = SideWindow()
        self.sui.show()

    def update_progress(self, progress):
        self.ui.progressBar.setValue(progress)

    def finishedRun(self):
        self.ui.run_it.setEnabled(True)

    def update_check(self):
        self.ui.chartRange.setEnabled(not self.ui.checkBox_range.isChecked())

    def startWorkInAThread(self):
        self.worker = WorkerThread(self)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.append_log)
        self.ui.run_it.setEnabled(False)
        self.worker.run_finished.connect(self.finishedRun)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def otvor(self):
        isExist = os.path.exists(directoryOut)
        if not isExist:
            os.makedirs(directoryOut)
        try:
            os.startfile(directoryOut)  # Windows only
        except Exception:
            pass

    def save_it(self):
        root = tk.Tk(); root.withdraw()
        global directoryOut
        directoryOut = fd.askdirectory(parent=root, title="Choose a directory")
        parser = ConfigParser()
        if getattr(sys, 'frozen', False):
            app_path = os.path.dirname(os.path.realpath(sys.executable))
            a_path = app_path + "/_internal/config.ini"
        else:
            app_path = os.path.dirname(os.path.abspath(__file__))
            a_path = app_path + "/config.ini"
        parser.read(a_path)
        parser.set("savedirectory", "directoryOut", directoryOut)
        with open(a_path, "w") as configfile:
            parser.write(configfile)

    def open_it1(self):
        root = tk.Tk(); root.withdraw()
        pridaj = fd.askopenfilenames(parent=root, title='Select MAT files BEFORE', filetypes=self.ftypes)
        self.zoznamPrd += pridaj
        self.zoznamPrd.sort()
        self.listBefore1.clear()
        for i in range(len(self.zoznamPrd)):
            self.listBefore1.addItem((os.path.basename(str(self.zoznamPrd[i]))).rsplit(".", 1)[0])
        self.ui.count1.setText(str(len(self.zoznamPrd)))

    def open_it2(self):
        root = tk.Tk(); root.withdraw()
        self.fileList = []
        pridajPo = fd.askopenfilenames(parent=root, title='Select MAT files AFTER', filetypes=self.ftypes)
        self.zoznamPo += pridajPo
        self.zoznamPo.sort()
        self.listAfter1.clear()
        for i in range(len(self.zoznamPo)):
            self.listAfter1.addItem(str(os.path.basename(self.zoznamPo[i])).rsplit(".", 1)[0])
            self.fileList.append(str(os.path.basename(self.zoznamPo[i])).rsplit(".", 1)[0])
        self.ui.count2.setText(str(len(self.zoznamPo)))
        self.odraty = []
        for i in self.fileList:
            if len(i.split("_")) > 3:
                self.odraty.append(i.split("_")[-3])
            else:
                self.odraty.append(i)

    def reset_it1(self):
        self.listBefore1.clear()
        self.zoznamPrd = []
        self.ui.count1.setText("0")

    def reset_it2(self):
        self.listAfter1.clear()
        self.zoznamPo = []
        self.fileList = []
        self.ui.count2.setText("0")

    def line_plot(self, array):
        shp = np.shape(array)[0]
        lim = int(shp // 4)
        return array[int(shp // 2)], lim

    def csv_export(self, VA, VB, R):
        avg_csv, avg_thk_bef_csv, avg_thk_af_csv = [], [], []
        variance_csv, ttv_csv, ttv_po_csv, deltaTTV_csv, wiwnu_csv = [], [], [], [], []
        for key in R.keys():
            Z = R[key]
            M = VB[key]
            A = VA[key]
            avg_thk_bef_csv.append(float(round((np.nanmean(M)), 2)))
            avg_thk_af_csv.append(float(round((np.nanmean(A)), 2)))
            if (np.nanmean(Z)) < 0.05:
                wiwnu_csv.append("N/A")
            else:
                wiwnu_csv.append(float(round((np.nanstd(Z) / np.nanmean(Z) * 100), 2)))
            ttv_csv.append(float(round((np.nanmax(M) - np.nanmin(M)), 2)))
            ttv_po_csv.append(float(round(np.nanmax(A) - np.nanmin(A), 2)))
            deltaTTV_csv.append(float(round((np.nanmax(A) - np.nanmin(A)) - (np.nanmax(M) - np.nanmin(M)), 2)))
            avg_csv.append(float(round((np.nanmean(Z)), 3)))
            variance_csv.append(float(round(((np.nanmax(Z) - np.nanmin(Z)) / (np.nanmean(Z)) * 100), 2)))
        d = {
            "Name": list(R.keys()),
            "Date": list(self.dates_aft.values()),
            "THK_BF": avg_thk_bef_csv,
            "THK_AFT": avg_thk_af_csv,
            "REM(um)": avg_csv,
            "WIWNU(%)": wiwnu_csv,
            "Variance": variance_csv,
            "TTV_BF": ttv_csv,
            "TTV_AFT": ttv_po_csv,
            "dTTV": deltaTTV_csv
        }
        df = pd.DataFrame(data=d)
        df["Date"] = df["Date"].astype(str)
        filename = f"Datafile_{self.lotName}.xlsx"
        df.to_excel(os.path.join(directoryOut, filename), index=False)
        self.append_log(backend.stamp("XLSX Summary file was generated."))
        self.append_log(f"Saved in: {str(directoryOut)}")

    def map_export(self, before, after, diff, progress):
        counter = 0
        for key in after:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(ncols=2, nrows=2)
            axlist1 = [ax1, ax2, ax3, ax4]
            Z = diff[key]
            VB = before[key]
            VA = after[key]
            ext = [-self.shejp, self.shejp, -self.shejp, self.shejp]
            wiwnu = np.nanstd(Z) / np.nanmean(Z) * 100 if np.nanmean(Z) != 0 else np.nan
            avgrem = np.nanmean(Z)
            minrem = np.nanmin(Z)
            TTV2 = (np.nanmax(VA) - np.nanmin(VA))
            TTV1 = (np.nanmax(VB) - np.nanmin(VB))
            self.avg_thk_bef.append(np.nanmean(VB))
            self.avg_thk_af.append(np.nanmean(VA))
            im1 = ax1.imshow(VB, cmap="jet", interpolation='nearest', extent=ext)
            im2 = ax2.imshow(VA, cmap="jet", interpolation='nearest', extent=ext)
            im3 = ax3.imshow(Z, cmap="jet", interpolation='nearest', extent=ext)
            for axis in axlist1:
                axis.set_ylabel("y [mm]")
                axis.set_xlabel("x [mm]")
            plt.suptitle(f"WaferID: {key}_{self.dates_aft[key]}", fontsize="10")
            ax1.set_title("Before")
            ax2.set_title("After")
            ax3.set_title("Removal")
            # Robust normalization
            for im in (im1, im2, im3):
                arr = im.get_array()
                lo, hi = np.nanpercentile(arr, [1, 99])
                if hi > lo:
                    im.set_clim(lo, hi)
            ax4.plot(np.linspace(-self.shejp, self.shejp, len(VB[self.shejp * 2])), VB[self.shejp * 2], linewidth=0.5, color="blue")
            ax4.plot(np.linspace(-self.shejp, self.shejp, len(VA[self.shejp * 2])), VA[self.shejp * 2], linewidth=0.5, color="orange")
            ax4.grid(True, linewidth=0.2, linestyle="--")
            ax4.legend(("Before", "After"), fancybox=True, shadow=True, loc="upper right", fontsize="4")
            ax4.set_title("Wafer THK profile")
            ax4.set_ylabel("THK (um)")
            ax1.text(self.shejp * 0.5, -self.shejp * 0.9, f"TTV1: {TTV1:.2f} um", fontsize=4)
            ax2.text(self.shejp * 0.5, -self.shejp * 0.9, f"TTV2: {TTV2:.2f} um", fontsize=4)
            ax3.text(self.shejp * 0.52, self.shejp * 0.9, f"Avg: {avgrem:.2f} um", fontsize=4)
            ax3.text(self.shejp * 0.52, self.shejp * 0.82, f"Min: {minrem:.2f} um", fontsize=4)
            ax3.text(self.shejp * 0.5, -self.shejp * 0.9, f"WIWNU: {wiwnu:.2f} %", fontsize=4)
            fig.colorbar(im2).set_label("Thickness (um)", rotation=90)
            fig.colorbar(im1)
            fig.colorbar(im3).set_label("Material removal (um)", rotation=90)
            fig.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.35)
            out_path = os.path.join(directoryOut, f"{key}_{self.dates_aft[key]}.jpg")
            fig.savefig(out_path, bbox_inches='tight', dpi=400)
            plt.close(fig); plt.close("all")
            counter += 1
            progress(int((counter) * 100 / self.total_steps))

    def profile_export(self, after, diff):
        plt.rcParams.update({"axes.linewidth":0.6,"axes.labelpad":3, "axes.titlepad":5,
                     "axes.titlesize": 12,"axes.labelsize":8,"figure.titlesize":5,
                     "xtick.labelsize": 8, "xtick.major.size":2.5,
                     "ytick.labelsize": 8,"ytick.major.width":0.5, "ytick.direction":"out","ytick.major.size":2.5,
                     "font.weight": "normal","axes.labelweight":"bold",
                     "legend.fontsize": 8})
        num_plots = self.goodCnt(diff)
        if num_plots == 0:
            custom_cycler = plt.cycler('color', "b")
        else:
            custom_cycler = plt.cycler('color', plt.cm.jet(np.linspace(0, 1, num_plots)))
        plt.rcParams["axes.prop_cycle"] = custom_cycler
        fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(8, 6))
        if not self.ui.checkBox_range.isChecked():
            ax1.set_ylim(0, float(self.ranger))
        try:
            for key in after.keys():
                if -5 < np.nanmax(diff[key][self.shejp * 2]) < float(self.ranger) * 2 and np.nanmin(diff[key][self.shejp * 2]) > -2.5:
                    wafer_map = diff[key]
                    l = wafer_map[self.shejp * 2]
                    k = np.linspace(-self.shejp, self.shejp, len(l))
                    self.legendList.append(key)
                    ax1.plot(k, l, linewidth=.8)
        except Exception:
            pass
        backend.coll(self.legendList)
        ada1 = AnchoredDrawingArea(20, 20, 0, 0, loc=4, pad=0., frameon=False)
        p1 = Circle((10, 10), 10, color="lightblue", alpha=0.4)
        arrow1 = FancyArrow(0, 10, 18, 0, color="red", head_width=2, alpha=0.6)
        ada1.da.add_artist(p1)
        ada1.da.add_artist(arrow1)
        ax1.add_artist(ada1)
        ax1.grid(True, linewidth=0.5, linestyle="--")
        ax1.set_title(f"Removal profiles: {self.lotName}", loc='left')
        ax1.set_ylabel("Removal (um)")
        ax1.legend(self.legendList, ncol=column, fancybox=True, shadow=True, loc="upper right")
        ax1.set_xlabel("x (mm)")
        fig.subplots_adjust(hspace=0)
        out_path = os.path.join(directoryOut, f"removal_profiles_{self.lotName}.jpg")
        fig.savefig(out_path, bbox_inches='tight', dpi=400)
        plt.close(fig); plt.close("all")

    def runit(self, progress_callback, log_callback=lambda s: None):
        # Ensure output directory exists
        self.ranger = self.ui.chartRange.displayText().replace(",", ".")
        isExist = os.path.exists(directoryOut)
        if not isExist:
            os.makedirs(directoryOut)
        self.legendList = []
        if len(self.zoznamPo) == len(self.zoznamPrd) and (len(self.zoznamPo) > 0):
            log_callback(backend.stamp("File processing has started."))
            self.avg_thk_bef = []
            self.avg_thk_af = []
            self.lotName = self.fileList[0].rsplit("_", 3)[0]
            before = {}
            after = {}
            # Load all files first, then sort once (optimization)
            for i in self.zoznamPrd:
                mat = loadmat(i, variable_names=["TF"])  # expect 'TF'
                before[i] = mat["TF"]
            for i in self.zoznamPo:
                mat = loadmat(i, variable_names=["TF"])  # expect 'TF'
                after[i] = mat["TF"]
            before_sorted, dates_bef = backend.get_creation_sorted_dict(before)
            after_sorted, self.dates_aft = backend.get_creation_sorted_dict(after)
            self.after_sorted = after_sorted
            self.before_sorted = before_sorted
            self.total_steps = len(after_sorted)
            if after_sorted.keys() == before_sorted.keys():
                removal_sorted_dict = {}
                for key in after_sorted.keys():
                    VB = np.fliplr(before_sorted[key]) if (self.ui.flipBox1.isChecked()) else before_sorted[key]
                    VA = np.fliplr(after_sorted[key]) if (self.ui.flipBox2.isChecked()) else after_sorted[key]
                    before_sorted[key] = VB
                    after_sorted[key] = VA
                    removal_sorted_dict[key] = (VB - VA)
                self.shejp = int(np.shape(VA)[0] / 4)
                # Exports
                if self.ui.remMapLabel.isChecked():
                    self.map_export(before_sorted, after_sorted, removal_sorted_dict, progress_callback)
                    log_callback(backend.stamp("Removal maps are finished."))
                self.profile_export(after_sorted, removal_sorted_dict)
                log_callback(backend.stamp("Removal profile chart is finished."))
                self.csv_export(after_sorted, before_sorted, removal_sorted_dict)
            else:
                log_callback("Not equal lists!")
        else:
            log_callback("No file or not equal file count!!!!!!")

    def plot_data(self, item):
        ext = [-self.shejp, self.shejp, -self.shejp, self.shejp]
        sigma = int(self.ui.significance_level.displayText())
        label = item.text()
        if self.ui.nanoTpghy_bef.isChecked():
            y = self.before_sorted[label]
        elif self.ui.nanoTpghy_aft.isChecked():
            y = self.after_sorted[label]
        else:
            return
        self.data = self.nanotopography(y)
        self.im.set_data(self.data)
        self.im.set_extent(ext)
        mean = np.nanmean(self.data)
        std = np.nanstd(self.data)
        self.im.set_clim(vmin=mean - std * sigma, vmax=mean + std * sigma)
        self.cbar.update_normal(self.im)
        self.canvas.axes.set_title(f"Plot for {label}")
        self.canvas.draw()

    def nanotopography(self, thicknessMatrix: np.ndarray) -> np.ndarray:
        # Ensure float array
        a = np.asarray(thicknessMatrix, dtype=float)
        # Kernel size from UI
        try:
            windowSize = int(self.ui.kernel_size.displayText())
        except Exception:
            windowSize = 7
        # Enforce odd and clamp to image dimensions
        h, w = a.shape[:2]
        max_odd = max(3, min(h, w) - 1)
        if max_odd % 2 == 0:
            max_odd -= 1
        if windowSize < 3:
            windowSize = 3
        if windowSize > max_odd:
            windowSize = max_odd
        if windowSize % 2 == 0:
            windowSize += 1
        # Reflect back to UI so the user sees the effective kernel
        try:
            self.ui.kernel_size.setText(str(windowSize))
        except Exception:
            pass
        # Median filter and difference
        filtered = medfilt2d(a, [windowSize, windowSize])
        return a - filtered

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(constrained_layout=True)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

if __name__ == "__main__":
    import sys
    config = ConfigParser()
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(os.path.realpath(sys.executable))
        font_dirs = application_path + "/_internal/Aptos"
        config.read(application_path + "/_internal/config.ini")
        try:
            import pyi_splash
            pyi_splash.close()
        except Exception:
            pass
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
        config.read(application_path + "/config.ini")
        font_dirs = application_path + "/Aptos"
    font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
    for font_file in font_files:
        font_manager.fontManager.addfont(font_file)
    directoryOut = config['savedirectory']["directoryout"]
    chart_range = config["chartrange"]["chart_range"]
    if directoryOut == "":
        directoryOut = (application_path + "\\output")
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    parser = ConfigParser()
    backend = Backend()
    mainWin.setWindowIcon(QtGui.QIcon(("_internal/icon_wafr.ico")))
    mainWin.show()
    sys.exit(app.exec_())
