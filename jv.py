#!/usr/bin/env python3

import click
import json
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window, ScrollOffsets
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import ANSI

class JsonViewer:
    def __init__(self, json_lines):
        self.json_lines = json_lines
        self.current_index = 0
        self.kb = KeyBindings()
        self.collapsed_paths = set()
        self.scroll_offset = 0
        self.scroll_x = 0  # 添加水平滚动偏移量
        self.setup_keybindings()
        
        # 定义颜色代码
        self.colors = {
            'key': '\033[36m',      # 青色表示键名
            'string': '\033[32m',    # 绿色表示字符串
            'number': '\033[33m',    # 黄色表示数字
            'boolean': '\033[35m',   # 紫色表示布尔值
            'null': '\033[31m',      # 红色表示 null
            'reset': '\033[0m',      # 重置颜色
            'brace': '\033[37m',     # 白色表示括号
            'comma': '\033[37m',     # 白色表示逗号
        }

    def setup_keybindings(self):
        @self.kb.add('q')
        def _(event):
            """退出程序"""
            event.app.exit()
            
        @self.kb.add('down')
        def _(event):
            """查看下一个 JSON 对象"""
            if self.current_index < len(self.json_lines) - 1:
                self.current_index += 1
                self.scroll_offset = 0  # 重置垂直滚动偏移
                self.scroll_x = 0        # 重置水平滚动偏移
                self.update_display(event.app)
                
        @self.kb.add('up')
        def _(event):
            """查看上一个 JSON 对象"""
            if self.current_index > 0:
                self.current_index -= 1
                self.scroll_offset = 0  # 重置垂直滚动偏移
                self.scroll_x = 0        # 重置水平滚动偏移
                self.update_display(event.app)
        
        @self.kb.add('enter')
        def _(event):
            """展开/折叠当前选中的 JSON 字段"""
            self.toggle_collapse()
            self.update_display(event.app)

        @self.kb.add('pagedown')
        @self.kb.add('c-f')  # Ctrl+F
        def _(event):
            """向下滚动一页"""
            window = event.app.layout.current_window
            if window:
                window_height = window.render_info.window_height
                max_offset = len(self.get_formatted_json_lines())  # 放宽最大偏移量
                self.scroll_offset = min(
                    self.scroll_offset + window_height,
                    max_offset
                )
                self.update_display(event.app)

        @self.kb.add('pageup')
        @self.kb.add('c-b')  # Ctrl+B
        def _(event):
            """向上滚动一页"""
            window = event.app.layout.current_window
            if window:
                window_height = window.render_info.window_height
                self.scroll_offset = max(self.scroll_offset - window_height, 0)
                self.update_display(event.app)

        @self.kb.add('j')
        def _(event):
            """向下滚动一行"""
            window = event.app.layout.current_window
            if window:
                max_offset = len(self.get_formatted_json_lines()) * 2  # 放宽最大偏移量
                if self.scroll_offset < max_offset:
                    self.scroll_offset += 1
                    self.update_display(event.app)

        @self.kb.add('k')
        def _(event):
            """向上滚动一行"""
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
                self.update_display(event.app)

        @self.kb.add('f')
        def _(event):
            """向下翻一页"""
            window = event.app.layout.current_window
            if window and window.render_info:
                page_size = window.render_info.window_height
                max_offset = len(self.get_formatted_json_lines())  # 放宽最大偏移量
                self.scroll_offset = min(
                    self.scroll_offset + page_size,
                    max_offset
                )
                self.update_display(event.app)

        @self.kb.add('b')
        def _(event):
            """向上翻一页"""
            window = event.app.layout.current_window
            if window and window.render_info:
                page_size = window.render_info.window_height
                self.scroll_offset = max(self.scroll_offset - page_size, 0)
                self.update_display(event.app)
        
        @self.kb.add('left')
        def _(event):
            """向左滚动"""
            if self.scroll_x > 0:
                self.scroll_x = max(0, self.scroll_x - 4)  # 每次左移4个字符
                self.update_display(event.app)

        @self.kb.add('right')
        def _(event):
            """向右滚动"""
            self.scroll_x += 4  # 每次右移4个字符
            self.update_display(event.app)

    def toggle_collapse(self):
        """切换当前路径的展开/折叠状态"""
        current_path = str(self.current_index)
        if current_path in self.collapsed_paths:
            self.collapsed_paths.remove(current_path)
        else:
            self.collapsed_paths.add(current_path)

    def format_json(self, obj, indent=0, path=''):
        """递归格式化 JSON，支持折叠功能和语法高亮"""
        if path in self.collapsed_paths:
            return ' ' * indent + self.colors['brace'] + '{ ... }' + self.colors['reset']
        
        if isinstance(obj, dict):
            if not obj:
                return self.colors['brace'] + '{}' + self.colors['reset']
            
            lines = []
            lines.append(self.colors['brace'] + '{' + self.colors['reset'])
            
            for i, (key, value) in enumerate(obj.items()):
                current_path = f"{path}.{key}" if path else key
                formatted_value = self.format_json(value, indent + 2, current_path)
                comma = self.colors['comma'] + ',' + self.colors['reset'] if i < len(obj) - 1 else ''
                
                key_str = f'{" " * (indent + 2)}{self.colors["key"]}"{key}"{self.colors["reset"]}: {formatted_value}{comma}'
                lines.append(key_str)
                
            lines.append(' ' * indent + self.colors['brace'] + '}' + self.colors['reset'])
            return '\n'.join(lines)
        
        elif isinstance(obj, list):
            if not obj:
                return self.colors['brace'] + '[]' + self.colors['reset']
                
            lines = []
            lines.append(self.colors['brace'] + '[' + self.colors['reset'])
            
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                formatted_item = self.format_json(item, indent + 2, current_path)
                comma = self.colors['comma'] + ',' + self.colors['reset'] if i < len(obj) - 1 else ''
                lines.append(f'{" " * (indent + 2)}{formatted_item}{comma}')
                
            lines.append(' ' * indent + self.colors['brace'] + ']' + self.colors['reset'])
            return '\n'.join(lines)
        
        elif isinstance(obj, str):
            return f'{self.colors["string"]}"{obj}"{self.colors["reset"]}'
        elif isinstance(obj, bool):
            return f'{self.colors["boolean"]}{str(obj).lower()}{self.colors["reset"]}'
        elif obj is None:
            return f'{self.colors["null"]}null{self.colors["reset"]}'
        else:  # numbers
            return f'{self.colors["number"]}{obj}{self.colors["reset"]}'
    
    def get_formatted_json_lines(self):
        """获取格式化后的 JSON 按行分割的列表，并应用水平和垂直滚动偏移"""
        if not self.json_lines:
            return ["没有找到 JSON 数据"]
        try:
            current_json = self.json_lines[self.current_index]
            formatted_json = self.format_json(current_json, path=str(self.current_index))
            status = (
                f"\n[{self.current_index + 1}/{len(self.json_lines)}] "
                "(↑↓: 切换条目, j/k: 滚动行, f/b: 翻页, Enter: 展开/折叠, q: 退出)\n"
            )
            full_text = formatted_json + status
            lines = full_text.split('\n')
            
            # 应用水平滚动偏移
            if self.scroll_x > 0:
                lines = [line[self.scroll_x:] if len(line) > self.scroll_x else '' for line in lines]
            
            # 应用垂直滚动偏移
            if self.scroll_offset > 0:
                lines = lines[self.scroll_offset:]
            
            return lines
        except Exception as e:
            return [f"错误: {str(e)}"]
    
    def get_formatted_json(self):
        """将格式化后的 JSON 重新组合为单个字符串"""
        lines = self.get_formatted_json_lines()
        return '\n'.join(lines)
    
    def update_display(self, app):
        text = self.get_formatted_json()
        app.layout.container.children[0].content.text = ANSI(text)
        app.invalidate()
    
    def run(self):
        if not self.json_lines:
            print("没有找到 JSON 数据")
            return

        # 创建主窗口
        window = Window(
            content=FormattedTextControl(
                text=ANSI(self.get_formatted_json()),
                focusable=True,
            ),
            wrap_lines=False,  # 禁用自动换行
            cursorline=True,
            allow_scroll_beyond_bottom=True,
            scroll_offsets=ScrollOffsets(top=1, bottom=1),
        )
        
        root_container = HSplit([window])
        
        # 创建应用
        app = Application(
            layout=Layout(root_container),
            key_bindings=self.kb,
            full_screen=True,
            mouse_support=True,
            style=Style.from_dict({
                'window': 'bg:#000000',
            })
        )
        
        app.run()

@click.command()
@click.argument('file', type=click.Path(exists=True))
def main(file):
    """JSONL 查看器 - 用于查看和浏览 JSONL 文件"""
    try:
        json_lines = []
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # 跳过空行
                    json_lines.append(json.loads(line))
        
        viewer = JsonViewer(json_lines)
        viewer.run()
    except Exception as e:
        click.echo(f"错误: {str(e)}", err=True)
        exit(1)

if __name__ == '__main__':
    main() 
