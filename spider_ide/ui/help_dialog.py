from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QTabWidget, QWidget, QFrame, QLabel
)
from PyQt6.QtCore import Qt

from spider_ide.ui.style_kit import DARK_THEME, mono, outline_button


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("DOCUMENTATION")
        self.resize(900, 700)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['border']};
            }}
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
                border-top: 1px solid {DARK_THEME['border']};
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {DARK_THEME['text_secondary']};
                padding: 10px 20px;
                border: none;
                border-right: 1px solid {DARK_THEME['border']};
                font-family: "Consolas", monospace;
                font-size: 11px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: transparent;
                color: {DARK_THEME['text']};
                border-bottom: 1px solid {DARK_THEME['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {DARK_THEME['surface']};
                color: {DARK_THEME['text']};
            }}
            QTextEdit {{
                background-color: transparent;
                color: {DARK_THEME['text']};
                border: none;
                padding: 20px;
                font-family: "Consolas", monospace;
                font-size: 13px;
                line-height: 1.6;
            }}
            QScrollBar:vertical {{
                background-color: {DARK_THEME['bg']};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {DARK_THEME['border']};
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        header_label = QLabel("// DOCUMENTATION")
        header_label.setFont(mono(14, bold=True, spacing=2))
        header_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']}; background: transparent;")
        layout.addWidget(header_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {DARK_THEME['border']}; max-height: 1px;")
        layout.addWidget(line)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.tabs.addTab(self._create_overview_tab(), "OVERVIEW")
        self.tabs.addTab(self._create_syntax_tab(), "SYNTAX")
        self.tabs.addTab(self._create_commands_tab(), "COMMANDS")
        self.tabs.addTab(self._create_examples_tab(), "EXAMPLES")
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = outline_button("CLOSE", DARK_THEME, compact=True)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _get_base_html(self):
        return f"""
            <style>
                body {{ background-color: transparent; color: {DARK_THEME['text']}; font-family: 'Consolas', monospace; font-size: 13px; line-height: 1.6; }}
                h1, h2 {{ color: {DARK_THEME['text']}; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; }}
                h1 {{ font-size: 20px; margin-bottom: 16px; }}
                h2 {{ font-size: 15px; margin-top: 24px; margin-bottom: 12px; color: {DARK_THEME['text_secondary']}; }}
                p {{ margin-bottom: 12px; }}
                code {{ background-color: {DARK_THEME['surface']}; color: {DARK_THEME['accent']}; padding: 2px 6px; border-radius: 0px; }}
                .code-block {{ background-color: {DARK_THEME['surface']}; padding: 16px; border-left: 2px solid {DARK_THEME['accent']}; font-family: 'Consolas', monospace; font-size: 12px; margin-bottom: 16px; }}
                .kw {{ color: #7dd3fc; font-weight: bold; }}
                .str {{ color: #fbbf24; }}
                .cmt {{ color: #52525b; font-style: italic; }}
                .fn {{ color: #4ade80; }}
            </style>
        """

    def _create_overview_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(self._get_base_html() + """
            <h1>SPIDER SCRIPT</h1>
            <p><b>Spider Script</b> is a simple scripting language for creating interactive applications and games. It uses a clean, readable syntax that is easy to learn.</p>
            
            <h2>KEY FEATURES</h2>
            <ul>
                <li><b>Simple Syntax</b> - Easy to read and write</li>
                <li><b>Interactive UI</b> - Create windows, buttons, and text elements</li>
                <li><b>Variables</b> - Store and manipulate data</li>
                <li><b>Control Flow</b> - if/else, loops, functions</li>
                <li><b>Event Handling</b> - Respond to user actions</li>
            </ul>
            
            <h2>BASIC STRUCTURE</h2>
            <div class="code-block">
                <span class="kw">Spider</span>(<span class="kw">Start</span>)<br><br>
                <span class="fn">print</span>(<span class="str">"Hello, World!"</span>)<br><br>
                <span class="fn">window</span>(<span class="str">title</span>="My App" <span class="str">width</span>=800 <span class="str">height</span>=600)
            </div>
            
            <h2>QUICK START</h2>
            <ol>
                <li>Create a new file with <code>.spider</code> extension</li>
                <li>Start with <code>Spider(Start)</code></li>
                <li>Add your commands</li>
                <li>Press <b>F5</b> to run</li>
            </ol>
        """)
        
        layout.addWidget(text)
        return widget
    
    def _create_syntax_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(self._get_base_html() + """
            <h1>SYNTAX REFERENCE</h1>
            
            <h2>COMMENTS</h2>
            <p>Use <code>#</code> or <code>//</code> for comments:</p>
            <div class="code-block">
                <span class="cmt"># This is a comment</span><br>
                <span class="cmt">// This is also a comment</span>
            </div>
            
            <h2>VARIABLES</h2>
            <p>Declare variables with <code>var</code>:</p>
            <div class="code-block">
                <span class="kw">var</span>(<span class="str">name</span>="John" <span class="str">value</span>=42)
            </div>
            
            <h2>STRINGS</h2>
            <p>Use single or double quotes:</p>
            <div class="code-block">
                <span class="fn">print</span>(<span class="str">"Hello, World!"</span>)
            </div>
            
            <h2>PARAMETERS</h2>
            <p>Commands use <code>key=value</code> syntax:</p>
            <div class="code-block">
                <span class="fn">window</span>(<span class="str">title</span>="My App" <span class="str">width</span>=800 <span class="str">height</span>=600)
            </div>
        """)
        
        layout.addWidget(text)
        return widget
    
    def _create_commands_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(self._get_base_html() + """
            <h1>COMMANDS REFERENCE</h1>
            
            <h2>PRINT</h2>
            <p>Outputs text to the console:</p>
            <div class="code-block">
                <span class="fn">print</span>(<span class="str">"Hello, World!"</span>)
            </div>
            
            <h2>VAR</h2>
            <p>Declares a variable:</p>
            <div class="code-block">
                <span class="kw">var</span>(<span class="str">name</span>="score" <span class="str">value</span>=100)
            </div>
            
            <h2>WINDOW</h2>
            <p>Creates a new window:</p>
            <div class="code-block">
                <span class="fn">window</span>(<span class="str">title</span>="My App" <span class="str">width</span>=800 <span class="str">height</span>=600 <span class="str">bg</span>="#ffffff")
            </div>
            
            <h2>TEXT</h2>
            <p>Displays text in the window:</p>
            <div class="code-block">
                <span class="fn">text</span>(<span class="str">text</span>="Hello" <span class="str">x</span>=100 <span class="str">y</span>=100 <span class="str">color</span>="black" <span class="str">size</span>=24)
            </div>
            
            <h2>BUTTON</h2>
            <p>Creates a button:</p>
            <div class="code-block">
                <span class="fn">button</span>(<span class="str">text</span>="Click Me" <span class="str">x</span>=100 <span class="str">y</span>=100 <span class="str">action</span>="on_click")
            </div>
        """)
        
        layout.addWidget(text)
        return widget
    
    def _create_examples_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(self._get_base_html() + """
            <h1>EXAMPLES</h1>
            
            <h2>HELLO WORLD</h2>
            <div class="code-block">
                <span class="kw">Spider</span>(<span class="kw">Start</span>)<br><br>
                <span class="fn">print</span>(<span class="str">"Hello, World!"</span>)
            </div>
            
            <h2>WINDOW WITH TEXT</h2>
            <div class="code-block">
                <span class="kw">Spider</span>(<span class="kw">Start</span>)<br><br>
                <span class="fn">window</span>(<span class="str">title</span>="My App" <span class="str">width</span>=800 <span class="str">height</span>=600)<br>
                <span class="fn">text</span>(<span class="str">text</span>="Hello Spider!" <span class="str">x</span>=400 <span class="str">y</span>=300 <span class="str">color</span>="black" <span class="str">size</span>=24)
            </div>
            
            <h2>BUTTON WITH ACTION</h2>
            <div class="code-block">
                <span class="kw">Spider</span>(<span class="kw">Start</span>)<br><br>
                <span class="fn">window</span>(<span class="str">title</span>="Button Demo" <span class="str">width</span>=400 <span class="str">height</span>=300)<br>
                <span class="fn">button</span>(<span class="str">text</span>="Click Me" <span class="str">x</span>=150 <span class="str">y</span>=100 <span class="str">action</span>="on_click")
            </div>
        """)
        
        layout.addWidget(text)
        return widget 