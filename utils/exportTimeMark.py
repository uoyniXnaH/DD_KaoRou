#导出时间轴字幕文件
#格式为 .srt

import os
from PySide2.QtWidgets import QGridLayout, QFileDialog, QDialog, QPushButton,\
        QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QProgressBar, QLabel,\
        QComboBox, QCheckBox, QWidget, QSlider, QFontDialog, QColorDialog, QTabWidget, \
        QMessageBox, QTimeEdit
from PySide2.QtCore import Qt, QTimer, Signal, QThread, QPoint
from PySide2.QtGui import QFontInfo, QPixmap, QIntValidator

class ExportSrt(QDialog):
    def __init__(self):
        self.srtPath = ''

        #所有时间单位均为ms
        #最短有效字幕时长，0：不移除短时长字幕
        self.minDuration = 100
        #最长字幕合并间隔，0：不合并短间隔字幕
        self.maxMerge = 100
        #时间轴偏移，0：不进行时间轴偏移
        #self.offset = 0
        #开始位置
        #self.startPos = 0
        #结束位置，0：视频末尾
        #self.endPos = 0

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
        self.minDuration = QLineEdit()
        self.layout.addWidget(self.minDuration, 2, 4, 1, 4)
        
        self.layout.addWidget(QLabel('最大合并间隔（毫秒）'), 3, 0, 1, 6)
        self.maxMerge = QLineEdit()
        self.layout.addWidget(self.maxMerge, 3, 4, 1, 4)

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
        #self.satPath.clicked.connect(self.exportSrt)
        
        self.exportSrt = QPushButton('导出文件')
        self.cancel = QPushButton('取消')
        self.help = QPushButton('帮助')
        self.layout.addWidget(self.exportSrt, 7, 0, 1, 2)
        self.layout.addWidget(self.cancel, 7, 2, 1, 2)
        self.layout.addWidget(self.help, 7, 4, 1, 2)

        self.cancel.clicked.connect(self.closeWindow)
        self.help.clicked.connect(self.dispHelp)

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