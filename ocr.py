# -*- coding: utf-8 -*-

import cv2
import re
from collections import Counter
from PIL import Image
import pytesseract

def preprocess_image(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        denoised = cv2.medianBlur(thresh, 3)
        height, width = denoised.shape
        scaled = cv2.resize(denoised, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
        
        return scaled
    except Exception as e:
        print(f"图像预处理错误: {e}")
        return None

def extract_points_advanced(image_path, user_manual_input=None):
    try:
        processed_img = preprocess_image(image_path)
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789积分点数字:：'
        
        results = []
        
        try:
            text1 = pytesseract.image_to_string(processed_img, config=custom_config, lang='chi_sim+eng')
            results.append(text1)
        except:
            text1 = pytesseract.image_to_string(processed_img, config=custom_config)
            results.append(text1)
        
        text2 = pytesseract.image_to_string(processed_img, config='--psm 8 -c tessedit_char_whitelist=0123456789')
        results.append(text2)
        
        original = Image.open(image_path)
        text3 = pytesseract.image_to_string(original, config='--psm 6')
        results.append(text3)
        
        all_numbers = []
        for text in results:
            if not text:
                continue
            
            patterns = [
                r'积分[：:]\s*(\d+)',
                r'points?[：:]\s*(\d+)',
                r'分数[：:]\s*(\d+)',
                r'得分[：:]\s*(\d+)',
                r'(\d+)\s*分',
                r'总分[：:]\s*(\d+)',
                r'合计[：:]\s*(\d+)',
                r'(?<!\d)(\d{1,4})(?!\d)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        num = int(match)
                        if 0 <= num <= 9999:
                            all_numbers.append(num)
                    except:
                        pass
        
        if all_numbers:
            most_common = Counter(all_numbers).most_common(1)[0][0]
            
            if user_manual_input is not None and user_manual_input != most_common:
                return {
                    'success': False,
                    'ocr_value': most_common,
                    'user_value': user_manual_input,
                    'error': f'识别值({most_common})与您输入({user_manual_input})不一致'
                }
            
            return {
                'success': True,
                'points': most_common,
                'confidence': len([n for n in all_numbers if n == most_common])
            }
        
        return {
            'success': False,
            'error': '未识别到有效积分数字，请确保图片清晰且包含数字'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'OCR识别失败: {str(e)}'
        }
