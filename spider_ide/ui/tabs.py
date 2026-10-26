from PyQt6.QtWidgets import QTabBar, QStyleOptionTab
from PyQt6.QtCore import Qt, QRect, QSize, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen

from spider_ide.ui.style_kit import DARK_THEME, mono


class BrutalistTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setDocumentMode(True)
        self.setMovable(True)
        self.setTabsClosable(False)
        self.setFont(mono(11))
        self._hovered_index = -1
        self._close_hovered_index = -1
        self._closing_tabs = {}

    def get_theme(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'theme'):
                return parent.theme
            if hasattr(parent, 'main_window') and hasattr(parent.main_window, 'theme'):
                return parent.main_window.theme
            parent = parent.parent()
        return DARK_THEME 

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        if index in self._closing_tabs:
            size.setWidth(int(self._closing_tabs[index].currentValue()))
        else:
            size.setWidth(max(100, size.width()))
        return size

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        theme = self.get_theme()
        
        for index in range(self.count()):
            if index in self._closing_tabs and self._closing_tabs[index].currentValue() <= 1:
                continue
                
            option = QStyleOptionTab()
            self.initStyleOption(option, index)
            rect = self.tabRect(index)
            is_selected = index == self.currentIndex()
            is_hovered = index == self._hovered_index
            

            
            if is_selected:
                painter.fillRect(rect, QColor(theme['bg']))

                painter.setPen(QPen(QColor(theme['accent']), 2))
                painter.drawLine(rect.left(), rect.bottom()-1, rect.right(), rect.bottom()-1)
            elif is_hovered:
                painter.fillRect(rect, QColor(theme['surface']))
            

            text_color = theme['text'] if is_selected else theme['text_secondary']
            painter.setPen(QColor(text_color))
            
            text_rect = QRect(rect)
            text_rect.adjust(12, 0, -30, 0)
            painter.setFont(mono(11))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, option.text)
            

            close_rect = QRect(rect.right() - 24, rect.center().y() - 6, 12, 12)
            is_close_hovered = (index == self._close_hovered_index)
            
            if is_close_hovered:
                painter.fillRect(close_rect, QColor('#ef4444')) 
                painter.setPen(QColor(theme['bg'])) 
            else:
                painter.setPen(QColor(theme['text_secondary']))
                
            painter.drawLine(close_rect.left() + 3, close_rect.top() + 3, close_rect.right() - 3, close_rect.bottom() - 3)
            painter.drawLine(close_rect.right() - 3, close_rect.top() + 3, close_rect.left() + 3, close_rect.bottom() - 3)

    def mouseMoveEvent(self, event):
        index = self.tabAt(event.pos())
        if index != self._hovered_index:
            self._hovered_index = index
            self.update()
        
        close_hovered = -1
        for i in range(self.count()):
            if i in self._closing_tabs:
                continue
            rect = self.tabRect(i)
            close_rect = QRect(rect.right() - 24, rect.center().y() - 6, 12, 12)
            if close_rect.contains(event.pos()):
                close_hovered = i
                break
                
        if close_hovered != self._close_hovered_index:
            self._close_hovered_index = close_hovered
            self.update()
            
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hovered_index != -1 or self._close_hovered_index != -1:
            self._hovered_index = -1
            self._close_hovered_index = -1
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._close_hovered_index != -1:
            self._start_close_animation(self._close_hovered_index)
            return
        super().mousePressEvent(event)

    def _start_close_animation(self, index):
        if index in self._closing_tabs:
            return
        
        current_width = self.tabSizeHint(index).width()
        anim = QVariantAnimation(self)
        anim.setStartValue(current_width)
        anim.setEndValue(0)
        anim.setDuration(150)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        def on_value_changed(value):
            self._closing_tabs[index] = anim
            self.update()
            
        def on_finished():
            if index in self._closing_tabs:
                del self._closing_tabs[index]
            self.tabCloseRequested.emit(index)
            
        anim.valueChanged.connect(on_value_changed)
        anim.finished.connect(on_finished)
        anim.start() 