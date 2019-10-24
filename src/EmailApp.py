from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivymd.theming import ThemeManager
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from functools import partial
from kivymd.list import IRightBodyTouch, MDList, TwoLineAvatarIconListItem, ILeftBody
from kivymd.button import MDIconButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
import re
import myscript as my
import webbrowser as wb
import sys
import requests
import time
import shelve
import _thread
import tmp
from navigationdrawer import NavigationDrawer


class Navigator(NavigationDrawer):
	# image_source = StringProperty('images/me.jpg')
	title = StringProperty('Navigation')


shelf = shelve.open('creddata')
user = tuple(shelf.keys())[0]


def isValidEmail(email):
    match = re.match(
        '^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
    if match == None:
        return False
    else:
        return True


def send_mail(fadd, tadd, sub, mes, refresh_token):
    my.send_mail(fadd, tadd, sub, mes, refresh_token)
    ValidatePopup('Mail sent', 'Your mail is sent successfully').open()


class Intent(ScreenManager):
    session = {}

    def put_extras(self, key, value):
        self.session[key] = value

    def get_extras(self, key):
        if key in self.session.keys():
            return self.session[key]
        else:
            return ''


class StartScreen(Screen):
    pass


class CheckConnScreen(Screen):
    status = ObjectProperty()

    def on_enter(self, *args):
        url = 'http://www.google.com'
        try:
            _ = requests.get(url, timeout=5)
        except requests.ConnectionError:
            NoConnPopup().open()
        else:
            print('No error')
        self.manager.current = 'switch'
        return super().on_enter(*args)


class ComposeScreen(Screen):
    fadd = ObjectProperty()
    tadd = ObjectProperty()
    sub = ObjectProperty()
    mes = ObjectProperty()

    def send(self):
        url = 'http://www.google.com'
        try:
            _ = requests.get(url, timeout=5)
        except requests.ConnectionError:
            NoConnPopup().open()
        else:
            print('No error')
            self.manager.current = 'login'
            result = self.validate()
            if not result:
                return
            refresh_token = shelf[self.fadd.text][1]
           # print("\n\n",self.fadd.text,"\n\n")
            print(refresh_token)
            _thread.start_new_thread(
                send_mail, (self.fadd.text, self.tadd.text, self.sub.text, self.mes.text, refresh_token))

    def get_values(self):
        return tuple(shelf.keys())

    def validate(self):
        if not isValidEmail(self.fadd.text):
            ValidatePopup("Invalid \'From\' address",
                          "Please select a from email address").open()
            # print(self.fadd.text)
            return False
        if not isValidEmail(self.tadd.text):
            ValidatePopup("Invalid \'To\' address",
                          "Please check your receipent's email address").open()
            return False
        if self.sub.text == '':
            ValidatePopup("Empty subject",
                          "Please add a subject for the receiver").open()
            return False

        return True


class LoginScreen(Screen):
    email = ObjectProperty()
    pwd = ObjectProperty()
    error = ObjectProperty()

    def validate(self):
        if not isValidEmail(self.email.text) or self.pwd.text == '':
            self.error.text = '*Invalid input'
        else:
            self.manager.put_extras('email', self.email.text)
            self.manager.put_extras('pwd', self.pwd.text)
            self.manager.current = 'getauth'


class GetAuthScreen(Screen):
    la = ObjectProperty()
    ver_code = ObjectProperty()

    def on_pre_enter(self, *args):
        self.la.text = self.manager.get_extras('email')
        scope = "https://mail.google.com/"
        url = my.generate_permission_url(my.GOOGLE_CLIENT_ID, scope)
        wb.open(url)
        return super().on_pre_enter(*args)

    def submit(self):
        refresh_token, access_token, expires_in = my.get_authorization(
            self.ver_code.text)
        email = self.manager.get_extras('email')
        pwd = self.manager.get_extras('pwd')
        shelf[email] = [pwd, refresh_token, access_token]


class InboxScreen(Screen):
    inboxview = None
    mylayout = None
    global user
    print(user)

    def on_enter(self, *args):
        if self.manager.get_extras('switched') == True:
            self.manager.put_extras('switched', False)
            if self.mylayout:
                self.mylayout.clear_widgets()
                self.mylayout = self.inboxview = None
            self.mylayout = MyLayout()
            self.inboxview = InboxView(user, 'delete','/index.txt')
            self.mylayout.add_widget(self.inboxview)
            self.add_widget(self.mylayout)

class SentScreen(Screen):
    inboxview = None
    mylayout = None
    global user
    print(user)

    def on_enter(self, *args):
            if self.mylayout:
                self.mylayout.clear_widgets()
                self.mylayout = self.inboxview = None
            self.mylayout = MyLayout()
            self.inboxview = InboxView(user, 'delete','/sent.txt',reverse=True)
            self.mylayout.add_widget(self.inboxview)
            self.add_widget(self.mylayout)
class TrashScreen(Screen):
    inboxview = None
    mylayout = None
    global user
    print(user)

    def on_enter(self, *args):
            if self.mylayout:
                self.mylayout.clear_widgets()
                self.mylayout = self.inboxview = None
            self.mylayout = MyLayout()
            self.inboxview = InboxView(user, 'delete','/trash.txt')
            self.mylayout.add_widget(self.inboxview)
            self.add_widget(self.mylayout)
class DeleteButton(IRightBodyTouch, MDIconButton):
    icon = 'delete'


class ContactPhoto(ILeftBody, AsyncImage):
        pass


class InboxView(ScrollView):
    def __init__(self, uname, bname,index,reverse=False, **kwargs):
        super(InboxView, self).__init__(**kwargs)
        mylist = MyList()
        try:
            index = open(uname+index)
        except:
            ValidatePopup(
                title='Not synced', ltext='Please connect to internet and sync your account.').open()
        else:
            for i in index:
                try:
                    # print('\n'+i+'\n')
                    date, pos, size, fadd, sub = i.split('||')
                    item = TwoLineAvatarIconListItem(
                        text=fadd, secondary_text=sub)
                    btn = DeleteButton()
                    btn.bind(on_press=partial(mylist.r_w, item))
                    item.add_widget(btn)
                    if reverse==False:
                        item.bind(on_press=partial(self.readmail, fadd, user, sub, pos, size))
                    else:
                        item.bind(on_press=partial(self.readmail, user,fadd, sub, pos, size))
                    mylist.add_widget(item)
                except: pass
            index.close()
            self.add_widget(mylist)

    def readmail(self, *args):
        fadd, tadd, sub, pos, size, temp = args
        print('\n',tadd,'\n')
        self.parent.parent.manager.put_extras('fadd', fadd)
        self.parent.parent.manager.put_extras('tadd', tadd)
        self.parent.parent.manager.put_extras('sub', sub)
        self.parent.parent.manager.put_extras('pos', pos)
        self.parent.parent.manager.put_extras('size', size)
        self.parent.parent.manager.current = 'readmail'


class MyList(MDList):
    def r_w(self, litem, btn):
        # print(litem,'removed')
        self.remove_widget(litem)


class ReadMail(Screen):
    fdisp = ObjectProperty()
    tdisp = ObjectProperty()
    sdisp = ObjectProperty()
    bdisp = ObjectProperty()

    def on_pre_enter(self, *args):
        self.create_layout()
        # print('Hello')

    def create_layout(self):
        global user
        file = open(user+'/email.txt')
        fadd = self.manager.get_extras('fadd')
        print(fadd)
        tadd = self.manager.get_extras('tadd')
        sub = self.manager.get_extras('sub')
        size = int(self.manager.get_extras('size'))
        pos = int(self.manager.get_extras('pos'))
        self.fdisp.text = fadd
        self.tdisp.text = tadd
        self.sdisp.text = sub
        file.seek(pos)
        body = file.read(size)
        # file.close()
        size = body.find('$#$')
        self.bdisp.text = body[0:size]
        self.bdisp.cursor = (0, 0)
        # print(body)


class SwitchScreen(Screen):
    pass


class SwitchView(ScrollView):
    def on_enter(self, *args):
        self.__init__()

    def __init__(self, **kwargs):
        super(SwitchView, self).__init__(**kwargs)
        mylist = MyList()
        index = tuple(shelf.keys())
        for i in index:
            try:
                item = TwoLineAvatarIconListItem(text=i)
                item.add_widget(ContactPhoto(
                    source='cliparts/'+i[0].lower()+'.gif'))
                item.bind(on_press=partial(self.switch, i))
                mylist.add_widget(item)
            except: print('Switch Exception')
        self.add_widget(mylist)

    def switch(self, i, *args):
        global user
        user = i
        self.parent.manager.session['switched'] = True
        self.parent.manager.current = 'inbox'


class NoConnPopup(Popup):
    pass


class ValidatePopup(Popup):
    def __init__(self, title, ltext,dismiss=True, **kwargs):
        self.title = title
        self.auto_dismiss = dismiss
        self.content = Label(text=ltext)
        self.size_hint = (0.5, 0.5)
        return super().__init__(**kwargs)

class SyncScreen(Screen):
    pass
class MyLayout(BoxLayout):
    pass

class EmailApp(App):
    theme_cls = ThemeManager()
    nav_drawer = ObjectProperty()
    def build(self):
        main_widget = Builder.load_file('./kv/email.kv')
        self.nav_drawer = Navigator()
        return main_widget
    def syncmail(self):
        global user,shelf
        self.root.current='login'
        _thread.start_new_thread(self.sync,(user,shelf))
        #self.sync(user,shelf)
        #self.root.current='inbox'
    def sync(self,user,shelf):
        p=ValidatePopup('Syncing mails','Please wait while we sync your mails',dismiss=False)
        p.open()
        tmp.syncmail(user,shelf)
        p.dismiss()
if __name__=='__main__':
	EmailApp().run()
