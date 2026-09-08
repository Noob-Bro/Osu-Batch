"""Consistent palette for Qt controls that paint outside stylesheet rules."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QTextCharFormat
from PySide6.QtWidgets import QCalendarWidget, QToolButton
from i18n import tr


def dark_palette():
    palette = QPalette()
    colors = {
        'Window': '#171a25', 'WindowText': '#e6e8f1', 'Base': '#121620',
        'AlternateBase': '#252a3a', 'Text': '#e6e8f1', 'Button': '#30364a',
        'ButtonText': '#e6e8f1', 'Highlight': '#875c81',
        'HighlightedText': '#ffffff', 'ToolTipBase': '#353b50',
        'ToolTipText': '#ffffff', 'PlaceholderText': '#a6acc2',
        'Light': '#434b64', 'Midlight': '#33394d', 'Mid': '#33394d',
        'Dark': '#121620', 'Shadow': '#0c0e15', 'Link': '#f5a6ce',
    }
    for role, color in colors.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(color))
    for role in ('Text', 'WindowText', 'ButtonText'):
        palette.setColor(QPalette.ColorGroup.Disabled,
                         getattr(QPalette.ColorRole, role), QColor('#9299af'))
    return palette


def configure_calendar(calendar):
    calendar.setPalette(dark_palette())
    calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
    header = QTextCharFormat()
    header.setForeground(QColor('#e6e8f1'))
    header.setBackground(QColor('#252a3a'))
    calendar.setHeaderTextFormat(header)
    weekend = QTextCharFormat()
    weekend.setForeground(QColor('#f5a6ce'))
    for day in (Qt.DayOfWeek.Saturday, Qt.DayOfWeek.Sunday):
        calendar.setWeekdayTextFormat(day, weekend)
    # Native arrow icons can remain black even under an application stylesheet.
    for name, text, label in (
        ('qt_calendar_prevmonth', '‹', '上个月'),
        ('qt_calendar_nextmonth', '›', '下个月'),
    ):
        button = calendar.findChild(QToolButton, name)
        if button:
            button.setArrowType(Qt.ArrowType.NoArrow)
            button.setText(text)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setAccessibleName(tr(label))
            button.setToolTip(tr(label))
    calendar.setStyleSheet('''
        QCalendarWidget QToolButton { color:#e6e8f1; background:#30364a;
            border:0; border-radius:4px; padding:5px; }
        QCalendarWidget QToolButton:hover { background:#424a64; }
        QCalendarWidget QAbstractItemView { background:#171a25;
            color:#e6e8f1; selection-background-color:#875c81;
            selection-color:white; alternate-background-color:#252a3a; }
    ''')

