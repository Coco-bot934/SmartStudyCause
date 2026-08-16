import sys
import os
from pathlib import Path
from threading import Thread
import json

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QListWidget, QFileDialog, QMessageBox, QCheckBox, QProgressBar
)

# ensure project root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import tools.report_tool as rt
from analyze_exam_paper_via_coze import analyze_exam_paper_via_coze


class ApiWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, url, token, prompt, images, image_names, template_bytes, template_name, use_async):
        super().__init__()
        self.url = url
        self.token = token
        self.prompt = prompt
        self.images = images
        self.image_names = image_names
        self.template_bytes = template_bytes
        self.template_name = template_name
        self.use_async = use_async

    def run(self):
        try:
            url = self.url
            if not url:
                cfg = rt.parse_config_from_source(rt.API_PY)
                url = cfg.get("url") or os.environ.get("COZE_API_URL")
            token = self.token or os.environ.get("COZE_API_TOKEN")
            if self.use_async and url and url.endswith("stream_run"):
                url = url.replace("stream_run", "async_run")
            payload = rt.build_payload(self.prompt, self.images, self.image_names, self.template_bytes, self.template_name)
            result = rt.call_agent_api(url, token, payload, stream=True)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class CozeWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, image_urls, bot_id=None, access_token=None, user_id=None, base_url=None):
        super().__init__()
        self.image_urls = image_urls
        self.bot_id = bot_id
        self.access_token = access_token
        self.user_id = user_id
        self.base_url = base_url

    def run(self):
        try:
            # call analyze_exam_paper_via_coze (synchronous)
            resp = analyze_exam_paper_via_coze(
                image_urls=self.image_urls,
                bot_id=self.bot_id or os.environ.get('COZE_BOT_ID', ''),
                access_token=self.access_token or os.environ.get('COZE_ACCESS_TOKEN', ''),
                user_id=self.user_id or 'gui_user',
                base_url=self.base_url or os.environ.get('COZE_BASE_URL', '')
            )
            # analyze_exam_paper_via_coze returns a string or error string
            self.finished.emit({"text": resp})
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Exam Report Generator")
        self.resize(700, 500)

        layout = QVBoxLayout()

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("在这里输入发送给 agent 的提示词（分析要求）")
        layout.addWidget(QLabel("Prompt:"))
        layout.addWidget(self.prompt_edit)

        img_layout = QHBoxLayout()
        self.img_list = QListWidget()
        img_buttons = QVBoxLayout()
        btn_add = QPushButton("添加图片")
        btn_add.clicked.connect(self.add_images)
        btn_remove = QPushButton("移除所选")
        btn_remove.clicked.connect(self.remove_selected_images)
        img_buttons.addWidget(btn_add)
        img_buttons.addWidget(btn_remove)
        img_layout.addWidget(self.img_list)
        img_layout.addLayout(img_buttons)
        layout.addWidget(QLabel("Exam Images:"))
        layout.addLayout(img_layout)

        tpl_layout = QHBoxLayout()
        self.tpl_label = QLabel("未选择模板")
        btn_tpl = QPushButton("选择模板 (.docx)")
        btn_tpl.clicked.connect(self.select_template)
        tpl_layout.addWidget(self.tpl_label)
        tpl_layout.addWidget(btn_tpl)
        layout.addWidget(QLabel("Template (optional):"))
        layout.addLayout(tpl_layout)

        opts_layout = QHBoxLayout()
        self.async_cb = QCheckBox("使用 async_run")
        opts_layout.addWidget(self.async_cb)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        opts_layout.addWidget(self.progress)
        layout.addLayout(opts_layout)

        btn_generate = QPushButton("生成报告")
        btn_generate.clicked.connect(self.generate_report)
        layout.addWidget(btn_generate)

        self.setLayout(layout)

        # internal state
        self.image_paths = []
        self.template_path = None

    def add_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择图片", str(Path.cwd()), "Images (*.png *.jpg *.jpeg *.bmp)")
        for p in paths:
            if p not in self.image_paths:
                self.image_paths.append(p)
                self.img_list.addItem(p)

    def remove_selected_images(self):
        for item in self.img_list.selectedItems():
            row = self.img_list.row(item)
            self.img_list.takeItem(row)
            try:
                self.image_paths.pop(row)
            except Exception:
                pass

    def select_template(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择模板", str(Path.cwd()), "Word (*.docx)")
        if p:
            self.template_path = p
            self.tpl_label.setText(Path(p).name)

    def generate_report(self):
        if not self.image_paths:
            QMessageBox.warning(self, "提示", "请先添加至少一张试卷图片。")
            return
        prompt = self.prompt_edit.toPlainText().strip() or "请分析上传的试卷并产出详细报告。"

        # detect whether all image paths are URLs
        is_url_images = all(p.startswith('http://') or p.startswith('https://') for p in self.image_paths)

        images_bytes = []
        image_names = []
        image_urls = None
        if is_url_images:
            image_urls = list(self.image_paths)
        else:
            try:
                for p in self.image_paths:
                    with open(p, 'rb') as f:
                        images_bytes.append(f.read())
                        image_names.append(Path(p).name)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取图片失败: {e}")
                return

        template_bytes = None
        template_name = None
        if self.template_path:
            try:
                with open(self.template_path, 'rb') as f:
                    template_bytes = f.read()
                    template_name = Path(self.template_path).name
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取模板失败: {e}")
                return

        # prepare worker
        cfg = rt.parse_config_from_source(rt.API_PY)
        url = cfg.get("url") or os.environ.get("COZE_API_URL")
        token = cfg.get("auth_token") or os.environ.get("COZE_API_TOKEN") or os.environ.get('COZE_ACCESS_TOKEN')

        use_async = self.async_cb.isChecked()

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)

        if image_urls is not None:
            # Prefer the actual Coze Agent endpoint (`stream_run` / `async_run`) because that is the API pattern used in z_扣子api.py.
            self.worker = ApiWorker(
                url or os.environ.get('COZE_API_URL') or cfg.get('url'),
                token,
                prompt,
                [
                    b'' for _ in image_urls
                ],
                [Path(u).name if not u.startswith('http') else u.split('/')[-1] for u in image_urls],
                template_bytes,
                template_name,
                use_async
            )
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            t = Thread(target=self.worker.run, daemon=True)
            t.start()
        else:
            self.worker = ApiWorker(url, token, prompt, images_bytes, image_names, template_bytes, template_name, use_async)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            t = Thread(target=self.worker.run, daemon=True)
            t.start()

    def on_error(self, msg):
        self.progress.setVisible(False)
        QMessageBox.critical(self, "调用错误", msg)

    def on_finished(self, result: dict):
        self.progress.setVisible(False)
        # handle binary
        try:
            if result.get("error"):
                QMessageBox.critical(self, "错误", str(result.get("error")))
                return

            if result.get("binary"):
                b = result["binary"]
                path, _ = QFileDialog.getSaveFileName(self, "保存报告为", "report.docx", "Word (*.docx)")
                if path:
                    with open(path, 'wb') as f:
                        f.write(b)
                    QMessageBox.information(self, "完成", f"报告已保存到 {path}")
                return

            data = result.get("data") or result.get("text")
            if isinstance(data, dict):
                doc_bytes = rt.json_to_docx(data)
                path, _ = QFileDialog.getSaveFileName(self, "保存报告为", "report.docx", "Word (*.docx)")
                if path:
                    with open(path, 'wb') as f:
                        f.write(doc_bytes)
                    QMessageBox.information(self, "完成", f"报告已保存到 {path}")
                return

            # fallback: save text
            text = result.get("text") or (json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else str(result))
            path, _ = QFileDialog.getSaveFileName(self, "保存报告为", "report.txt", "Text (*.txt)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "完成", f"报告已保存到 {path}")
        except Exception as e:
            QMessageBox.critical(self, "处理返回结果失败", str(e))


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
