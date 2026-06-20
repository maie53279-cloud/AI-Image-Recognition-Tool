# -*- coding: utf-8 -*-
"""
AI图像识别工具
基于百度AI开放平台 + PyQt5
功能：识别银行卡、身份证、驾驶证、车牌、动物、植物、Logo等
"""

import sys
import json
import base64
import urllib
import urllib.request
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QComboBox, 
                             QPushButton, QLineEdit, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap

# ==================== 配置区域 ====================
# 请在百度AI开放平台申请替换以下值
API_KEY = "请替换为你的API Key"
SECRET_KEY = "请替换为你的Secret Key"
# =================================================


class AIImageRecognition(QWidget):
    """AI图像识别工具主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.download_path = ["", ""]  # 存储图片路径
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("AI图像识别工具")
        self.setFixedSize(700, 580)
        
        # ---------- 主布局 ----------
        main_layout = QGridLayout()
        
        # ---------- 第1行：分类选择 ----------
        row1_group = QGroupBox("识别分类")
        row1_layout = QHBoxLayout()
        
        self.comboBox = QComboBox()
        categories = ["银行卡", "植物", "动物", "通用票据", "营业执照", 
                      "身份证", "车牌号", "驾驶证", "行驶证", "车型", "Logo"]
        self.comboBox.addItems(categories)
        row1_layout.addWidget(QLabel("选择识别类型:"))
        row1_layout.addWidget(self.comboBox)
        row1_layout.addStretch()
        row1_group.setLayout(row1_layout)
        main_layout.addWidget(row1_group, 0, 0, 1, 2)
        
        # ---------- 第2行：图片选择 ----------
        row2_group = QGroupBox("选择图片")
        row2_layout = QHBoxLayout()
        
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("请选择要识别的图片...")
        self.lineEdit.setReadOnly(True)
        
        self.btn_open = QPushButton("浏览图片")
        self.btn_open.clicked.connect(self.open_file)
        
        row2_layout.addWidget(self.lineEdit, 3)
        row2_layout.addWidget(self.btn_open, 1)
        row2_group.setLayout(row2_layout)
        main_layout.addWidget(row2_group, 1, 0, 1, 2)
        
        # ---------- 第3行：图片预览 + 识别结果 ----------
        # 图片预览（左侧）
        self.image_label = QLabel("请选择图片")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.image_label.setFixedSize(311, 301)
        main_layout.addWidget(self.image_label, 2, 0)
        
        # 识别结果（右侧）
        result_group = QGroupBox("识别结果")
        result_layout = QVBoxLayout()
        
        self.result_label = QLabel("等待识别...")
        self.result_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("border: 1px solid #ccc; padding: 8px; min-height: 260px; background-color: #fafafa;")
        
        self.btn_copy = QPushButton("复制结果到剪贴板")
        self.btn_copy.clicked.connect(self.copy_result)
        
        result_layout.addWidget(self.result_label)
        result_layout.addWidget(self.btn_copy)
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group, 2, 1)
        
        self.setLayout(main_layout)
        
    # ==================== 核心功能方法 ====================
    
    def get_token(self):
        """获取百度AI访问令牌（access_token）"""
        try:
            host = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
            request = urllib.request.Request(host)
            request.add_header('Content-Type', 'application/json; charset=UTF-8')
            response = urllib.request.urlopen(request)
            content = response.read().decode('utf-8')
            data = json.loads(content)
            return data.get('access_token', '')
        except Exception as e:
            self.result_label.setText(f"获取token失败: {str(e)}")
            return ''
    
    def get_file_content(self, file_path):
        """以二进制方式读取文件"""
        with open(file_path, 'rb') as f:
            return f.read()
    
    def open_file(self):
        """打开文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要识别的图片", "/", "Image Files (*.jpg *.jpeg *.png *.bmp)"
        )
        if not file_path:
            return
        
        self.download_path[0] = file_path
        self.lineEdit.setText(file_path)
        
        # 预览图片
        try:
            pixmap = QPixmap(file_path)
            scaled = pixmap.scaled(QSize(311, 301), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
        except Exception as e:
            self.image_label.setText("图片加载失败")
        
        # 触发识别
        self.recognize()
    
    def recognize(self):
        """根据选择的分类调用对应的识别方法"""
        index = self.comboBox.currentIndex()
        token = self.get_token()
        if not token:
            return
        
        # 映射索引到方法
        methods = {
            0: self.recognize_bankcard,
            1: self.recognize_plant,
            2: self.recognize_animal,
            3: self.recognize_invoice,
            4: self.recognize_business_license,
            5: self.recognize_idcard,
            6: self.recognize_license_plate,
            7: self.recognize_driving_license,
            8: self.recognize_vehicle_license,
            9: self.recognize_car,
            10: self.recognize_logo,
        }
        method = methods.get(index)
        if method:
            method(token)
    
    # ==================== 各分类识别方法 ====================
    
    def recognize_bankcard(self, token):
        """银行卡识别"""
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/bankcard"
        result = self._request_api(url, token)
        if result and 'result' in result:
            r = result['result']
            card_type = {0: '不能识别', 1: '借记卡', 2: '信用卡'}.get(r.get('bank_card_type', 0), '未知')
            text = f"识别结果：\n卡号：{r.get('bank_card_number', '')}\n银行：{r.get('bank_name', '')}\n类型：{card_type}"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_plant(self, token):
        """植物识别"""
        url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/plant"
        result = self._request_api(url, token)
        if result and 'result' in result:
            items = result['result'][:3]
            text = "识别结果（植物）：\n"
            for i, item in enumerate(items, 1):
                text += f"{i}. {item.get('name', '未知')} (置信度: {item.get('score', 0):.2%})\n"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_animal(self, token):
        """动物识别"""
        url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/animal"
        result = self._request_api(url, token)
        if result and 'result' in result:
            items = result['result'][:3]
            text = "识别结果（动物）：\n"
            for i, item in enumerate(items, 1):
                text += f"{i}. {item.get('name', '未知')} (置信度: {item.get('score', 0):.2%})\n"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_invoice(self, token):
        """通用票据识别"""
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice"
        result = self._request_api(url, token)
        if result and 'result' in result:
            r = result['result']
            text = f"识别结果（票据）：\n发票代码：{r.get('InvoiceCode', '')}\n发票号码：{r.get('InvoiceNum', '')}\n金额：{r.get('TotalAmount', '')}"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_business_license(self, token):
        """营业执照识别"""
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/business_license"
        result = self._request_api(url, token)
        if result and 'result' in result:
            r = result['result']
            text = f"识别结果（营业执照）：\n公司：{r.get('company', '')}\n法人：{r.get('legal_representative', '')}\n注册号：{r.get('reg_num', '')}"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_idcard(self, token):
        """身份证识别"""
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/idcard"
        result = self._request_api(url, token)
        if result and 'result' in result:
            r = result['result']
            text = f"识别结果（身份证）：\n姓名：{r.get('姓名', {}).get('words', '')}\n身份证号：{r.get('公民身份号码', {}).get('words', '')}\n住址：{r.get('住址', {}).get('words', '')}"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_license_plate(self, token):
        """车牌号识别"""
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/license_plate"
        result = self._request_api(url, token)
        if result and 'result' in result:
            r = result['result']
            text = f"识别结果（车牌号）：\n号码：{r.get('number', '')}\n颜色：{r.get('color', '')}"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_driving_license(self, token):
        """驾驶证识别"""
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/driving_license"
        result = self._request_api(url, token)
        if result and 'result' in result:
            r = result['result']
            text = f"识别结果（驾驶证）：\n姓名：{r.get('姓名', '')}\n驾驶证号：{r.get('证号', '')}\n准驾车型：{r.get('准驾车型', '')}"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_vehicle_license(self, token):
        """行驶证识别"""
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/vehicle_license"
        result = self._request_api(url, token)
        if result and 'result' in result:
            r = result['result']
            text = f"识别结果（行驶证）：\n车牌号：{r.get('车牌号码', '')}\n车辆类型：{r.get('车辆类型', '')}\n所有人：{r.get('所有人', '')}"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_car(self, token):
        """车型识别"""
        url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/car"
        result = self._request_api(url, token)
        if result and 'result' in result:
            items = result['result'][:3]
            text = "识别结果（车型）：\n"
            for i, item in enumerate(items, 1):
                text += f"{i}. {item.get('name', '未知')} (置信度: {item.get('score', 0):.2%})\n"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    def recognize_logo(self, token):
        """Logo识别"""
        url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/logo"
        result = self._request_api(url, token)
        if result and 'result' in result:
            items = result['result'][:3]
            text = "识别结果（Logo）：\n"
            for i, item in enumerate(items, 1):
                text += f"{i}. {item.get('name', '未知')} (置信度: {item.get('score', 0):.2%})\n"
            self.result_label.setText(text)
        else:
            self._show_error(result)
    
    # ==================== 通用辅助方法 ====================
    
    def _request_api(self, url, token):
        """通用API请求方法"""
        try:
            file_path = self.download_path[0]
            if not file_path:
                self.result_label.setText("请先选择图片")
                return None
            
            with open(file_path, 'rb') as f:
                img_data = base64.b64encode(f.read())
            
            params = {"image": img_data}
            data = urllib.parse.urlencode(params).encode('utf-8')
            
            request_url = f"{url}?access_token={token}"
            request = urllib.request.Request(url=request_url, data=data)
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            response = urllib.request.urlopen(request, timeout=30)
            content = response.read().decode('utf-8')
            return json.loads(content)
            
        except urllib.error.URLError as e:
            return {'error_msg': f'网络错误: {str(e)}'}
        except Exception as e:
            return {'error_msg': f'请求失败: {str(e)}'}
    
    def _show_error(self, result):
        """显示错误信息"""
        if result and 'error_msg' in result:
            self.result_label.setText(f"识别失败：{result['error_msg']}")
        else:
            self.result_label.setText("识别失败，请检查网络或图片格式")
    
    def copy_result(self):
        """复制识别结果到剪贴板"""
        text = self.result_label.text()
        if text and text != "等待识别...":
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            # 可选：提示复制成功（状态栏暂时省略）
        else:
            pass


# ==================== 程序入口 ====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIImageRecognition()
    window.show()
    sys.exit(app.exec_())
