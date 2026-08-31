from ctypes import wintypes
import ctypes,sys,threading,time,os,configparser
import webview
from webview import FileDialog

if sys.platform=="win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.example.AudioEditorApp")

data_dir=os.path.join(os.path.expanduser("~"),".PDFTextEditor")
os.makedirs(data_dir,exist_ok=True)
CONFIG_FILE=os.path.join(data_dir,"config.ini")

def resource_path(p):
    try:b=sys._MEIPASS
    except:b=os.path.abspath(".")
    return os.path.join(b,p)

html_path=resource_path("assets/main.html")

def load_config():
    d={"x":None,"y":None,"width":1000,"height":700,"fullscreen":False}
    try:
        c=configparser.ConfigParser()
        if not os.path.exists(CONFIG_FILE):return d
        c.read(CONFIG_FILE,encoding="utf-8")
        if "Window" not in c:return d
        s=c["Window"]
        d["x"]=None if s.get("x","None").lower()=="none" else int(s["x"])
        d["y"]=None if s.get("y","None").lower()=="none" else int(s["y"])
        d["width"]=s.getint("width",fallback=1000)
        d["height"]=s.getint("height",fallback=700)
        d["fullscreen"]=s.getboolean("fullscreen",fallback=False)
    except:pass
    return d

def save_config(w):
    try:
        c=configparser.ConfigParser()
        c["Window"]={
            "x":str(w.x),"y":str(w.y),"width":str(w.width),
            "height":str(w.height),"fullscreen":str(w.fullscreen).lower()
        }
        with open(CONFIG_FILE,"w",encoding="utf-8") as f:c.write(f)
    except:pass

cfg=load_config()
user32=ctypes.windll.user32
dwmapi=ctypes.windll.dwmapi
RED=122|(12<<8)|(12<<16)
WHITE=255|(255<<8)|(255<<16)

def titlebar():
    while not (hwnd:=user32.FindWindowW(None,"PDF Text Editor")):time.sleep(.05)
    for attr,color in ((35,RED),(36,WHITE),(34,RED)):
        v=ctypes.c_int(color)
        dwmapi.DwmSetWindowAttribute(hwnd,attr,ctypes.byref(v),ctypes.sizeof(v))

class Icon:
    def __init__(self,title,path):
        self.title=title
        self.path=os.path.abspath(path) if path else None

    def find(self):
        hwnd=self.user32.FindWindowW(None,self.title)
        if hwnd:return hwnd
        found=[]
        @ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
        def cb(hwnd,_):
            n=self.user32.GetWindowTextLengthW(hwnd)+1
            b=ctypes.create_unicode_buffer(n)
            self.user32.GetWindowTextW(hwnd,b,n)
            if self.title in b.value:found.append(hwnd)
            return True
        self.user32.EnumWindows(cb,0)
        return found[0] if found else None

    @property
    def user32(self):return ctypes.windll.user32

    def set(self):
        if not self.path or not os.path.exists(self.path):return
        hwnd=None
        for _ in range(50):
            if hwnd:=self.find():break
            time.sleep(.1)
        if not hwnd:return
        try:
            for size,msg in ((16,0),(32,1)):
                icon=self.user32.LoadImageW(0,self.path,1,size,size,0x10)
                if icon:self.user32.SendMessageW(hwnd,0x80,msg,icon)
        except:pass

class Api:
    def save_html(self,content):
        types=("HTML Files (*.html)","All Files (*.*)")
        try:r=webview.windows[0].create_file_dialog(FileDialog.SAVE,file_types=types)
        except AttributeError:r=webview.windows[0].create_file_dialog(webview.SAVE_DIALOG,file_types=types)
        if not r:return "Cancelled"
        p=r[0]
        if not p.lower().endswith((".html",".htm")):p+=".html"
        with open(p,"w",encoding="utf-8") as f:f.write(content)
        return "Saved successfully"

api=Api()

args={
    "title":"PDF Text Editor",
    "url":html_path,
    "width":cfg["width"],
    "height":cfg["height"],
    "fullscreen":cfg["fullscreen"],
    "js_api":api
}
if cfg["x"] is not None:args["x"]=cfg["x"]
if cfg["y"] is not None:args["y"]=cfg["y"]

window=webview.create_window(**args)
window.events.closing+=lambda:save_config(window)

icon=Icon("PDF Text Editor",resource_path(r"assets\icon.ico"))
threading.Thread(target=lambda:(time.sleep(1),icon.set()),daemon=True).start()
threading.Thread(target=titlebar,daemon=True).start()

webview.start(debug=False)