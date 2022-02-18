#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import math

from PySide2 import QtWidgets, QtUiTools, QtCore
import numpy as np
import pyqtgraph as pg
from epics import caget

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class UiLoader(QtUiTools.QUiLoader):
    def createWidget(self, className, parent=None, name=""):
        if className == "PlotWidget":
            return pg.PlotWidget(parent=parent)
        return super().createWidget(className, parent, name)


def load_ui(fname):
    fd = QtCore.QFile(fname)
    if fd.open(QtCore.QFile.ReadOnly):
        loader = UiLoader()
        window = loader.load(fd)
        fd.close()
    return window


class Xafscsv(QtCore.QObject):

    def __init__(self):
        super(Xafscsv, self).__init__()
        # self.window = load_ui('xafs_csv.ui')
        self.window = load_ui(os.path.join(DIR_PATH, 'xafs_csv.ui'))
        self.window.installEventFilter(self)

        self.window.generateList.clicked.connect(self.xafs_csv)
        self.window.getValues.clicked.connect(self.get_positions)

    def get_positions(self):

        y2_pv_string = self.window.y2_pv.text()
        theta_pv_string = self.window.theta_pv.text()
        y2 = caget(y2_pv_string)
        theta = caget(theta_pv_string)

        self.window.dcm_y2.setValue(y2)
        self.window.dcm_theta.setValue(theta)

        offset = y2 * 2 * math.cos(math.radians(theta))
        self.window.offset.setValue(offset)

    def xafs_csv(self):

        offset = self.window.dcm_y2.value() * 2 * math.cos(math.radians(self.window.dcm_theta.value()))
        self.window.offset.setValue(offset)
        e0 = self.window.e0.value()  # EDGE ENERGY IN eV

        prestart = self.window.preStart.value()  # PREEDGE START BEFORE EDGE IN eV
        prestop = self.window.preStop.value()  # PRE EDGE STOP BEFORE EDGE IN eV
        prestep = self.window.preStep.value()  # PREEDGE STEP

        xa1start = self.window.xa1Start.value()  # XANES 1 START BEFORE EDGE IN eV
        xa1stop = self.window.xa1Stop.value()  # XANES 1 STOP BEHIND EDGE IN eV
        xa1step = self.window.xa1Step.value()  # XANES 1 STEP

        xa2start = self.window.xa2Start.value()  # XANES 2 START BEHIND EDGE IN eV
        xa2stop = self.window.xa2Stop.value()  # XANES 2 STOP BEHIND EDGE IN eV
        xa2step = self.window.xa2Step.value()  # XANES 2 STEP

        # EXAFS START IN k - SPACE(XANES STOP = 50 --> k = 3.67
        #                                  =100 --> k = 5.13
        #                                 =200 --> k = 7.26
        exstart = self.window.exStart.value()
        exstop = self.window.exStop.value()  # EXAFS STOP IN k - SPACE
        # EXAFS STEP IN
        # k - SPACE (EXAFS: deltak = 0.04... 0.06, XANES deltak = 2.5)
        exstep = self.window.exStep.value()

        # Pre - edge
        energytable = np.arange(e0 - prestart, e0 - prestop, prestep)

        # XANES_1
        xanes1_table = np.arange(e0 - xa1start, e0 + xa1stop, xa1step)
        energytable = np.append(energytable, xanes1_table)

        # XANES_2
        xanes2_table = np.arange(e0 + xa2start, e0 + xa2stop, xa2step)
        energytable = np.append(energytable, xanes2_table)

        # EXAFS
        exafs_k_table = np.arange(exstart, exstop, exstep)
        for k in exafs_k_table:
            e = round((k ** 2 / 0.263) + e0, 4)
            energytable = np.append(energytable, e)

        dcm_y2_table = np.array([])

        for energy in energytable:
            neudcm_y2 = offset / (2. * math.cos(math.asin(1.239842 / (2 * 0.31356) / energy * 1000.0)))
            dcm_y2_table = np.append(dcm_y2_table, neudcm_y2)

        energytable = energytable / 1000
        combined_data = np.vstack((energytable, dcm_y2_table)).T

        # write it to CSV
        directory = '/messung/rfa/daten/.csv'
        path = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', directory, 'CSV(*.csv)')

        path = path[0]
        header = self.window.e0_name.text() + ";" + self.window.y2_name.text()
        if path == '':
            return

        np.savetxt(path, combined_data, fmt='%.4f', delimiter=';', header=header, comments='')

    def show(self):
        self.window.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = Xafscsv()
    main.show()
    sys.exit(app.exec_())
