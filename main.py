import cv2 as cv
import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

kv = """
#:kivy 1.11.0

<MenuScreen>:
    MainWidget:

<SettingsScreen>:
    FloatLayout:
        Cam:
            id: cam1
            resolution: 800,600
        Button:
            text: 'Save frame'
            pos: 100, 0
            size: 200, 50
            size_hint:None, None
            on_press: root.save()
        
        Button:
            text: 'Exit'
            pos: 500, 0
            size: 200, 50
            size_hint:None, None
            on_press:quit()
            
ScreenManager:
    MenuScreen:
        name: 'menu'
    SettingsScreen:
        name: 'settings'
"""

contrast = 30
brightness = 0
url = 'http://hamby:hamby@192.168.1.2:8080/video'
bytes = bytes()


class MainWidget(Widget):

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        btn1 = Button(text='Start ESP32-CAM',pos=(330,300),size=(130,100))
        btn1.bind(on_press=self.capture)
        btn2 = Button(text='Exit app',pos=(330,150),size=(130,100))
        btn2.bind(on_press=self.exit)
        self.add_widget(btn1)
        self.add_widget(btn2)

    # def savecard(self, btn_instance):

    def capture(self, btn_inst):
        app = App.get_running_app()
        app.root.current = "settings"

    def exit(self, btn_inst):
        quit()

class MenuScreen(Screen):
    pass


class SettingsScreen(Screen):
   def save(self):
        ret, frame = cv.VideoCapture(url).read()
        cv.imwrite("test.png",frame)



class Cam(Image):

    def on_kv_post(self, base_widget):
        self.capture = cv.VideoCapture(url)
        
        # cv.namedWindow("CV2 Image")
        Clock.schedule_interval(self.update, 1.0 / 33.0)

    def update(self, dt):
        ret, imageFrame = self.capture.read()       
        
        # Image processing code
        imageFrame = np.int16(imageFrame)
        imageFrame = imageFrame * (contrast/127+1) - contrast + brightness
        imageFrame = np.clip(imageFrame,0 , 255)
        imageFrame = np.uint8(imageFrame)
        hsv = cv.cvtColor(imageFrame, cv.COLOR_BGR2HSV)
        brown_lower = np.array([10,100,20],np.uint8)
        brown_upper = np.array([20, 255, 200], np.uint8)
        brown_mask = cv.inRange(hsv, brown_lower, brown_upper)
        kernel = np.ones((5, 5), "uint8")
        brown_mask = cv.dilate(brown_mask, kernel)

        contours, hierarchy = cv.findContours(brown_mask,cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)
        for pic, contour in enumerate(contours):
            area = cv.contourArea(contour)
            if(area > 200):
                x, y, w, h = cv.boundingRect(contour)
                imageFrame = cv.rectangle(imageFrame, (x, y),(x + w, y + h),(0, 0, 255), 2)
                cv.putText(imageFrame, "Dry", (x, y),cv.FONT_HERSHEY_SIMPLEX,1.0, (0, 0, 0))

            buf = cv.flip(imageFrame,0)
            buf = buf.tobytes()
            texture1 = Texture.create(size=(imageFrame.shape[1],imageFrame.shape[0]),
                                        colorfmt='bgr')  # in grayscale gibts kein bgr
                                    # if working on RASPBERRY PI, use colorfmt='rgba' here instead, but stick with "bgr" in blit_buffer.
            texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')  # replacing texture
                                # display image from the texture
            self.texture = texture1

    

class TestApp(App):

    def build(self):
        Window.clearcolor = (0, 0, 0.3, 1)
        return Builder.load_string(kv)


if __name__ == '__main__':
    TestApp().run()