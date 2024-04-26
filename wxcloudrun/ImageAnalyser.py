import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyparsing import *

from wxcloudrun.ocrengin import get_ocr_engins

COLOR_BLUE = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (127, 127, 127)


def draw_text(image, x, y, text, color=COLOR_RED):
    pilimg = Image.fromarray(image)
    draw = ImageDraw.Draw(pilimg)
    # 参数1：字体文件路径，参数2：字体大小
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 30)
    # 参数1：打印坐标，参数2：文本，参数3：字体颜色，参数4：字体
    draw.text((x, y - 10), text, color, font=font)
    return cv2.cvtColor(np.array(pilimg), cv2.COLOR_RGB2BGR)


# 定义数字
integer = Word(nums)
# 定义比较符
operator = oneOf("> < =")
# 定义基本的数学运算符
math_op = oneOf("+ - * / × ÷")
# 定义表达式
expr = Forward()
atom = integer | Group(Literal("(").suppress() + expr + Literal(")").suppress())
expr <<= atom + ZeroOrMore(math_op + atom)
original_expr = originalTextFor(expr)
# 定义整个等式或不等式的语法
equation = original_expr.setResultsName('left_side') + operator.setResultsName('oper') + original_expr.setResultsName(
    'right_side')


def parse_equation(equation_str):
    try:
        # 尝试解析输入的字符串
        parsed = equation.parseString(equation_str)
        left_side = parsed.left_side.replace('×', '*').replace('÷', '/')
        right_side = parsed.right_side.replace('×', '*').replace('÷', '/')
        return left_side, parsed.oper, right_side
    except ParseException:
        # 如果解析失败，返回None
        return None


class ImageAnalyser:

    def __init__(self, alpha=1.5, beta=0, new_size=(640, 480), thresh=127, engin='baidu'):
        self.alpha = alpha
        self.beta = beta
        self.new_size = new_size
        self.thresh = thresh
        self.engin = engin
        self.gray_image = None
        self.bgr_image = None

    def _get_engin(self):
        support_engins = get_ocr_engins()
        if self.engin not in support_engins:
            return support_engins['baidu']()
        return support_engins[self.engin]()

    def prev_deal(self, image_path):
        image = cv2.imread(image_path)

        # 调节对比度
        adjusted_image = cv2.convertScaleAbs(image, alpha=self.alpha, beta=self.beta)

        # 插值
        # # 最近邻插值
        # image_nearest = cv2.resize(image, new_size, interpolation=cv2.INTER_NEAREST)
        #
        # # 双线性插值
        # image_linear = cv2.resize(image, new_size, interpolation=cv2.INTER_LINEAR)

        # 双三次插值
        image_cubic = cv2.resize(adjusted_image, self.new_size, interpolation=cv2.INTER_CUBIC)

        # 展示原始图像和缩放后的图像
        # cv2.imshow('Original Image', image)
        # cv2.imshow('Nearest Interpolation', image_cubic)

        # Convert to grayscale and apply threshold
        gray = cv2.cvtColor(image_cubic, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(gray, self.thresh, 255, cv2.THRESH_BINARY)  # + cv2.THRESH_OTSU
        self.gray_image = binary_image
        return binary_image

    def analyse(self, image_path):

        ocr_engin = self._get_engin()
        if self.engin == "baidu":
            results = ocr_engin.identify(image_path)
        else:
            binary_image = self.prev_deal(image_path=image_path)
            results = ocr_engin.identify(binary_image)

        color_image = cv2.imread(image_path)
        correct_num = 0
        wrong_num = 0
        for _, row in results.iterrows():
            text = row['text']
            (x, y, w, h) = row['left'], row['top'], row['width'], row['height']

            result = parse_equation(text)
            if result:
                left_side, oper, right_side = result
                left_result = int(eval(left_side))
                right_result = int(eval(right_side))
                if ((oper == '=' and left_result == right_result)
                        or (oper == '<' and left_result < right_result)
                        or (oper == '>' and left_result > right_result)):
                    x_end, y_end = x + w, y + h // 2
                    color_image = draw_text(color_image, x_end, y_end, '√', color=COLOR_RED)
                    correct_num += 1
                else:
                    x_end, y_end = x + w, y + h // 2
                    color_image = draw_text(color_image, x_end, y_end, '×', color=COLOR_BLUE)
                    cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 1)
                    color_image = draw_text(color_image, x, y, text, color=COLOR_GREEN)
                    wrong_num += 1

        self.bgr_image = color_image
        return correct_num, wrong_num

    def to_path(self, image_path, gray_or_bgr='bgr'):
        if gray_or_bgr == 'bgr':
            image = self.bgr_image
        else:
            image = self.gray_image

        cv2.imwrite(image_path, image)
        return image_path


if __name__ == '__main__':
    image_path = r'image\o4-Hhv4x_F3G-Vk3Q_1713936209.jpg'
    analyser = ImageAnalyser()
    analyser.analyse(image_path)
    cv2.imshow('image', analyser.bgr_image)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
