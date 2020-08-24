#导出时间轴字幕文件
#格式为 .srt

import os
from PySide2.QtWidgets import QGridLayout, QFileDialog, QDialog, QPushButton,\
        QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QProgressBar, QLabel,\
        QComboBox, QCheckBox, QWidget, QSlider, QFontDialog, QColorDialog, QTabWidget, \
        QMessageBox, QTimeEdit
from PySide2.QtCore import Qt, QTime, Signal, QThread, QPoint
from PySide2.QtGui import QFontInfo, QPixmap, QIntValidator
from utils.separate_audio import Separate

def ms2TimeStr(ms):
    '''
    receive int
    return str
    ms -> h:m:s,ms
    '''
    h, m = divmod(ms, 3600000)
    m, s = divmod(m, 60000)
    s, ms = divmod(s, 1000)
    h = ('0%s' % h)[-2:]
    m = ('0%s' % m)[-2:]
    s = ('0%s' % s)[-2:]
    ms = ('%s0' % ms)[:2]
    return '%s:%s:%s,%s' % (h, m, s, ms)

def ms2QTime(ms):
    '''
    receive int
    return QTime
    '''
    h, m = divmod(ms, 3600000)
    m, s = divmod(m, 60000)
    s, ms = divmod(s, 1000)
    return QTime(h, m, s, ms)

def QTime2ms(QTime):
    '''
    arg QTime
    return int
    '''
    h = QTime.hour()
    m = QTime.minute()
    s = QTime.second()
    ms = QTime.msec()
    return h*3600000 + m*60000 + s*1000 + ms


class ExportSrt(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('输出.srt时间轴文件')
        self.resize(550,350)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        
        self.startPos = QTimeEdit()
        self.startPos.setDisplayFormat('hh:mm:ss.zzz')
        self.layout.addWidget(QLabel('开始位置'), 0, 0, 1, 3)
        self.layout.addWidget(self.startPos, 0, 2, 1, 3)

        self.endPos = QTimeEdit()
        self.endPos.setDisplayFormat('hh:mm:ss.zzz')
        self.layout.addWidget(QLabel('结束位置'), 0, 6, 1, 3)
        self.layout.addWidget(self.endPos, 0, 8, 1, 3)

        self.timeMarkType = QComboBox()
        self.timeMarkType.addItems(['相对时间', '绝对时间'])
        self.layout.addWidget(QLabel('记录方式'), 1, 0, 1, 3)
        self.layout.addWidget(self.timeMarkType, 1, 2, 1, 3)

        self.offset = QTimeEdit()
        self.offset.setDisplayFormat('hh:mm:ss.zzz')
        self.layout.addWidget(QLabel('时间轴偏移'), 1, 6, 1, 4)
        self.layout.addWidget(self.offset, 1, 8, 1, 3)

        self.layout.addWidget(QLabel('最大无效时长（毫秒）'), 2, 0, 1, 6)
        self.maxIgnore = QLineEdit()
        self.layout.addWidget(self.maxIgnore, 2, 4, 1, 4)
        self.maxIgnore.setText("100")
        
        self.layout.addWidget(QLabel('最大合并间隔（毫秒）'), 3, 0, 1, 6)
        self.maxMerge = QLineEdit()
        self.layout.addWidget(self.maxMerge, 3, 4, 1, 4)
        self.maxMerge.setText("100")

        self.mergeOrIgnore = QComboBox()
        self.mergeOrIgnore.addItems(['优先合并', '优先忽略'])
        self.layout.addWidget(QLabel('合并&忽略优先设置'), 4, 0, 1, 6)
        self.layout.addWidget(self.mergeOrIgnore, 4, 4, 1, 3)

        self.isExportUnnumbering = QCheckBox()
        self.layout.addWidget(self.isExportUnnumbering, 5, 0, 1, 1)
        self.layout.addWidget(QLabel('同时导出无编号.srt文件'), 5, 1, 1, 6)

        self.saveDir = QLineEdit()
        self.layout.addWidget(self.saveDir, 6, 0, 1, 6)
        self.setPath = QPushButton('保存位置')
        self.layout.addWidget(self.setPath, 6, 6, 1, 1)
        self.setPath.clicked.connect(self.choosePath)
        
        self.exportSrt = QPushButton('导出文件')
        self.cancel = QPushButton('取消')
        self.help = QPushButton('帮助')
        self.layout.addWidget(self.exportSrt, 7, 0, 1, 2)
        self.layout.addWidget(self.cancel, 7, 2, 1, 2)
        self.layout.addWidget(self.help, 7, 4, 1, 2)
        self.exportSrt.clicked.connect(self.execExportSrt)

        self.cancel.clicked.connect(self.closeWindow)
        self.help.clicked.connect(self.dispHelp)

    def setDefault(self, autoSub, videoDuration):
        self.autoSub = autoSub
        self.endPos.setTime(ms2QTime(videoDuration))

    def closeWindow(self):
        self.destroy(True, True)

    def dispHelp(self):
        self.helpContents = '''- 开始位置 & 结束位置：.srt文件开始及结束的时间点
- 记录方式：记录原始视频的绝对时间，或是以开始位置为0记录相对时间
- 时间轴偏移：时间点位置整体调整
- 最大无效时长：语音段时长不超过这个值时，该语音段会被忽略。0：不忽略任何语音段
- 最大合并间隔：两个语音段之间的空白时长不超过这个值时，两个语音段将被合并。0：不合并任何语音段
- 合并&忽略优先设置：如果一个语音段同时可以被合并以及被忽略，设置指定进行哪个操作'''
        self.helpPage = QMessageBox()
        self.helpPage.setText(self.helpContents)
        self.helpPage.show()

    def choosePath(self):
        subtitlePath = QFileDialog.getSaveFileName(self, "选择文件夹", '', "字幕文件 (*.srt)")[0]
        if subtitlePath:
            self.saveDir.setText(subtitlePath)

    def execExportSrt(self):
        voiceCntRaw = len(self.autoSub)
        if voiceCntRaw == 0:
            self.timeNotFound = QMessageBox()
            self.timeNotFound.setText("没有找到时间轴信息。")
            self.timeNotFound.show()
            return

        startPos = QTime2ms(self.startPos.time())
        endPos = QTime2ms(self.endPos.time())
        