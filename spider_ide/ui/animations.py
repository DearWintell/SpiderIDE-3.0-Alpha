from PyQt6.QtCore import (
    QObject, QVariantAnimation, QEasingCurve, QPropertyAnimation,
    Qt, pyqtProperty, QTimer, QRect, QPoint, QSize
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


class Easing:
    @staticmethod
    def ease_in_out(t):
        return t * t * (3 - 2 * t)

    @staticmethod
    def ease_out(t):
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in(t):
        return t ** 3

    @staticmethod
    def bounce(t):
        n1 = 7.5625
        d1 = 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    @staticmethod
    def to_qt_curve(name='out_cubic'):
        mapping = {
            'linear': QEasingCurve.Type.Linear,
            'in_quad': QEasingCurve.Type.InQuad,
            'out_quad': QEasingCurve.Type.OutQuad,
            'in_out_quad': QEasingCurve.Type.InOutQuad,
            'in_cubic': QEasingCurve.Type.InCubic,
            'out_cubic': QEasingCurve.Type.OutCubic,
            'in_out_cubic': QEasingCurve.Type.InOutCubic,
            'out_bounce': QEasingCurve.Type.OutBounce,
            'in_out_bounce': QEasingCurve.Type.InOutBounce,
            'out_elastic': QEasingCurve.Type.OutElastic,
        }
        return mapping.get(name, QEasingCurve.Type.OutCubic)


class _OpacityTarget(QObject):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.effect = QGraphicsOpacityEffect(widget)
        self.widget.setGraphicsEffect(self.effect)

    def get_opacity(self):
        return self.effect.opacity()

    def set_opacity(self, value):
        self.effect.setOpacity(value)

    opacity = pyqtProperty(float, fget=get_opacity, fset=set_opacity)


class Animator:
    def __init__(self, widget):
        self.widget = widget
        self.running_animations = []

    def _track(self, anim):
        self.running_animations.append(anim)
        anim.finished.connect(lambda a=anim: self._untrack(a))

    def _untrack(self, anim):
        if anim in self.running_animations:
            self.running_animations.remove(anim)

    def stop_all(self):
        for anim in list(self.running_animations):
            anim.stop()
        self.running_animations.clear()

    def animate_value(self, start, end, duration=300, easing='out_cubic',
                      on_update=None, on_finish=None):
        anim = QVariantAnimation(self.widget)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(duration)
        anim.setEasingCurve(Easing.to_qt_curve(easing))
        if on_update:
            anim.valueChanged.connect(on_update)
        if on_finish:
            anim.finished.connect(on_finish)
        self._track(anim)
        anim.start()
        return anim

    def animate_color(self, widget, start_color, end_color, duration=300,
                      easing='out_cubic', property_name='color',
                      apply_callback=None):
        start = QColor(start_color)
        end = QColor(end_color)

        def update(t):
            r = int(start.red() + (end.red() - start.red()) * t)
            g = int(start.green() + (end.green() - start.green()) * t)
            b = int(start.blue() + (end.blue() - start.blue()) * t)
            a = int(start.alpha() + (end.alpha() - start.alpha()) * t)
            color = QColor(r, g, b, a)
            if apply_callback:
                apply_callback(color)
            elif property_name == 'color':
                widget.setStyleSheet(f"color: {color.name()};")
            elif property_name == 'background':
                widget.setStyleSheet(f"background-color: {color.name()};")

        return self.animate_value(0.0, 1.0, duration, easing, on_update=update)

    def animate_size(self, widget, start_size, end_size, duration=300,
                     easing='out_cubic'):
        anim = QPropertyAnimation(widget, b"size", self.widget)
        anim.setStartValue(QSize(*start_size))
        anim.setEndValue(QSize(*end_size))
        anim.setDuration(duration)
        anim.setEasingCurve(Easing.to_qt_curve(easing))
        self._track(anim)
        anim.start()
        return anim

    def animate_geometry(self, widget, start_rect, end_rect, duration=300,
                         easing='out_cubic'):
        anim = QPropertyAnimation(widget, b"geometry", self.widget)
        anim.setStartValue(QRect(*start_rect))
        anim.setEndValue(QRect(*end_rect))
        anim.setDuration(duration)
        anim.setEasingCurve(Easing.to_qt_curve(easing))
        self._track(anim)
        anim.start()
        return anim

    def fade_in(self, widget, duration=200, on_finish=None):
        target = _OpacityTarget(widget)
        target.set_opacity(0.0)
        widget.show()

        anim = QPropertyAnimation(target, b"opacity", self.widget)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(duration)
        anim.setEasingCurve(Easing.to_qt_curve('out_cubic'))
        if on_finish:
            anim.finished.connect(on_finish)
        self._track(anim)
        anim.start()
        widget._opacity_target = target
        return anim

    def fade_out(self, widget, duration=200, on_finish=None):
        target = getattr(widget, '_opacity_target', None)
        if target is None:
            target = _OpacityTarget(widget)
            widget._opacity_target = target

        anim = QPropertyAnimation(target, b"opacity", self.widget)
        anim.setStartValue(target.get_opacity())
        anim.setEndValue(0.0)
        anim.setDuration(duration)
        anim.setEasingCurve(Easing.to_qt_curve('in_cubic'))

        def finish():
            widget.hide()
            if on_finish:
                on_finish()

        anim.finished.connect(finish)
        self._track(anim)
        anim.start()
        return anim

    def slide_in(self, widget, direction='left', distance=300, duration=300,
                 easing='out_cubic'):
        widget.show()
        pos = widget.pos()
        dx, dy = 0, 0

        if direction == 'left':
            dx = -distance
        elif direction == 'right':
            dx = distance
        elif direction == 'top':
            dy = -distance
        elif direction == 'bottom':
            dy = distance

        start_pos = QPoint(pos.x() + dx, pos.y() + dy)
        widget.move(start_pos)

        anim = QPropertyAnimation(widget, b"pos", self.widget)
        anim.setStartValue(start_pos)
        anim.setEndValue(pos)
        anim.setDuration(duration)
        anim.setEasingCurve(Easing.to_qt_curve(easing))
        self._track(anim)
        anim.start()
        return anim

    def pulse(self, widget, times=2, scale=1.05, duration=800):
        original = widget.size()
        big = QSize(int(original.width() * scale), int(original.height() * scale))
        per_cycle = duration // (times * 2)

        def grow():
            self.animate_size(widget, original, big, per_cycle, 'out_quad',
                              on_finish=shrink)

        def shrink():
            self.animate_size(widget, big, original, per_cycle, 'in_quad',
                              on_finish=None)

        QTimer.singleShot(0, grow)

    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)


def fade_widget(widget, duration=200):
    return Animator(widget).fade_in(widget, duration)


def slide_widget(widget, direction='left', duration=300):
    return Animator(widget).slide_in(widget, direction, duration=duration) 