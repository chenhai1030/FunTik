#!/usr/bin/env python3
#coding:utf-8

import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))

def debug_mode(choice):
    """Enable/disable printing helpful information for debugging the program. Default is off."""
    global _log
    if choice:
        def _log(*args):
            AppKit.NSLog(' '.join(map(str, args)))
    else:
        def _log(*_):
            pass
debug_mode(True)


if __name__ == "__main__":
    if sys.version_info.major == 3 and sys.version_info.minor == 7:
        python_path = os.path.abspath(os.path.join(current_path, os.pardir, 'python37', '1.0'))
        extra_lib = "/Users/chenhai/work/virtualenv/py3env/lib/python3.7/site-packages/PyObjCTools"
    elif sys.version_info.major == 2 and sys.version_info.minor == 7:
        python_path = os.path.abspath(os.path.join(current_path, os.pardir, 'python27', '1.0'))
        extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjC"
        sys.path.append(extra_lib)
    else:
        raise Exception("pls use 2.7 or 3.7")

import AppKit
from Foundation import NSTimer, NSRunLoop, NSDate, NSDefaultRunLoopMode
from AppKit import NSApplication, NSApp, NSStatusBar, NSImage, NSWindow, NSWindowController, NSMenu, \
    NSMenuItem, NSAlert, NSText, NSTextField, NSSecureTextField, NSButton, NSMinX, NSMinY
from AppKit import CAKeyframeAnimation, CABasicAnimation, CALayer
from PyObjCTools import AppHelper
from Quartz import CGPoint, CGRect, CGSize, CGPathCreateMutable, CGPathMoveToPoint, CGPathAddLineToPoint, CGPathCloseSubpath

from spider import Attendance


viewController = None
spider = Attendance()


class MacTrayObject(AppKit.NSObject):

    def applicationDidFinishLaunching_(self, notification):
        self.isLogin = False
        self.polling_flag = True
        self.today_hours = 0

        # app_support_path = os.path.join(AppKit.NSSearchPathForDirectoriesInDomains(14, 1, 1).objectAtIndex_(0), 'FunTik')
        # if not os.path.isdir(app_support_path):
        #     os.mkdir(app_support_path)

        self.setupMenuBar()
        self.registerObserver()

    def setupMenuBar(self):
        self.statusitem = NSStatusBar.systemStatusBar().statusItemWithLength_(-1)
        self.statusitem.setHighlightMode_(True)

        # Set initial image icon
        #icon_path = os.path.join(current_path, "Resources", "favicon.png")
        icon_path = 'favicon.png'
        try:
            _log('attempting to open image at {0}'.format(icon_path))
            with open(icon_path):
                pass
        except IOError:  # literal file path didn't work -- try to locate image based on main script path
            try:
                from __main__ import __file__ as main_script_path
                main_script_path = os.path.dirname(main_script_path)
                icon_path = os.path.join(main_script_path, icon_path)
            except ImportError:
                pass
            _log('attempting (again) to open image at {0}'.format(icon_path))
            with open(icon_path):  # file doesn't exist
                pass  # otherwise silently errors in NSImage which isn't helpful for debugging
        #image = NSImage.alloc().initByReferencingFile_(icon_path.encode('utf-8').decode('utf-8'))
        image = NSImage.alloc().initByReferencingFile_(icon_path)
        image.setScalesWhenResized_(True)
        image.setSize_((20, 20))
        #image.setTemplate_(True)
        self.statusitem.setImage_(image)

        # Let it highlight upon clicking
        self.statusitem.setHighlightMode_(1)
        self.statusitem.setToolTip_("Funtool")

        # Build a very simple menu
        self.menu = NSMenu.alloc().init()

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Login', 'loginCallback:', '')
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.separatorItem()
        self.menu.addItem_(menuitem)

        # Default event
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'windowWillClose:', 'q')
        self.menu.addItem_(menuitem)

        # Bind it to the status item
        self.statusitem.setMenu_(self.menu)

        # Get the timer going
        self.timer = NSTimer.alloc().initWithFireDate_interval_target_selector_userInfo_repeats_(NSDate.date(), 180.0, self, 'updateMenuBarStatus:', None, True)
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)

        # Hide dock icon
        NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

    def updateLoginStatusBarMenu(self, username=''):
        self.menu.removeAllItems()
        menu_item = username + ': Sign out'
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(menu_item, 'logoutCallback:', '')
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.separatorItem()
        self.menu.addItem_(menuitem)

        #week hours:
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('This week : Loading...', '', '')
        self.menu.addItem_(menuitem)

        #today hours:
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Today : Loading...', '', '')
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.separatorItem()
        self.menu.addItem_(menuitem)

        # Default event
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'windowWillClose:', 'q')
        self.menu.addItem_(menuitem)

        # Trigger autovalidation
        self.menu.update()

        self.isLogin = True
        self.polling_flag = True
        self.timer.fire()

    def updateMenuBarStatus_(self, notification):
        print("timer test")
        if self.isLogin and self.polling_flag:
            self.menu.removeItemAtIndex_(2)
            week_hours = spider.get_week_hours()
            menu_item = 'This week :' + str(week_hours) + 'h'
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(menu_item, '', '')
            self.menu.insertItem_atIndex_(menuitem, 2)

            self.menu.removeItemAtIndex_(3)
            hours = spider.get_today_hours()
            if hours is not 'no data':
                self.today_hours = hours
                self.polling_flag = False
            menu_item = 'Today :' + str(hours) + 'h'
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(menu_item, '', '')
            self.menu.insertItem_atIndex_(menuitem, 3)
        elif not self.polling_flag:
            print('reflash time')
            #add 180s = 3m = 0.05h
            self.today_hours = round(self.today_hours + 0.05, 2)
            self.menu.removeItemAtIndex_(3)
            menu_item = 'Today :' + str(self.today_hours) + 'h'
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(menu_item, '', '')
            self.menu.insertItem_atIndex_(menuitem, 3)

        self.menu.update()

    def logoutCallback_(self, notification):
        self.menu.removeAllItems()
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Login', 'loginCallback:', '')
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.separatorItem()
        self.menu.addItem_(menuitem)

        # Default event
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'windowWillClose:', 'q')
        self.menu.addItem_(menuitem)

    def loginCallback_(self, notification):
        global viewController

        if not viewController:
            viewController = Window.alloc().init()

        NSApp.setDelegate_(viewController)
        # NSWindow in front
        NSApp.activateIgnoringOtherApps_(True)
        # Show the window
        viewController.showWindow_(viewController)

    def registerObserver(self):
        nc = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()
        nc.addObserver_selector_name_object_(self, 'windowWillClose:', AppKit.NSWorkspaceWillPowerOffNotification, None)

    def windowWillClose_(self, notification):
        os._exit(0)
        NSApp.terminate_(self)


class App(object):
    """
    Represents the statusbar application.
    """
    def __init__(self, name, title=None, icon=None, template=None, menu=None, quit_button='Quit'):
        _require_string(name)
        self._name = name
        self._icon = self._icon_nsimage = self._title = None
        self._template = template
        self.icon = icon
        self.title = title
        self.quit_button = quit_button
        #self._menu = Menu()
        if menu is not None:
            self.menu = menu
        #self._application_support = application_support(self._name)


class ButtonFactory(object):
    """
    Create Button with default properties.
    """
    def __init__(self, width, height):
        self._width = width
        self._height = height

    def make_button(self, x, y, text, is_enable=True):
        """
        Create button with default properties.
        """
        btn = NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(x, y, self._width, self._height))
        # NSButtonTypeOnOff = 6
        btn.setButtonType_(6)
        # NSBezelStyleRounded = 1
        btn.setBezelStyle_(1)
        btn.setTitle_(text)
        btn.setEnabled_(is_enable)
        return btn


class TextFieldFactory(object):
    """
    Create TextFiled with default properties.
    """
    def __init__(self, width, height):
        self._width = width
        self._height = height

    def make_label(self, x, y, text):
        """
        Create labels with default properties.
        """
        label = NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, self._width, self._height))
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        # NSTextAlignmentCenter = 2
        label.setAlignment_(2)
        label.setStringValue_(text)
        return label

    def make_text_filed(self, x, y, holdtext=None, secure=False):
        """
        Create text filed with default properties.
        """
        if secure:
            text_filed = NSSecureTextField.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, self._width, self._height))
        else:
            text_filed = NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, self._width, self._height))
        self.registerForNotifications()
        text_filed.setSelectable_(True)
        text_filed.setEditable_(True)
        if holdtext is not None:
            text_filed.setPlaceholderString_(holdtext)
        return text_filed

    def registerForNotifications(self):
        nc = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()
        nc.addObserver_selector_name_object_(self, 'textFieldDidChange:', AppKit.NSControlTextDidChangeNotification, self)

    def textFieldDidChange_(self, notification):
        self.setDelegate(self)


class Window(NSWindowController):
    width = 500
    height = 200
    _win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        AppKit.NSMakeRect(0, 0, width, height),
        3,
        2,
        False)
    _win.setTitle_("Login")
    _win.center()
    _win.setReleasedWhenClosed_(False)
    _win.setCanHide_(False)

    #do not del if not us nib
    WindowController = NSWindowController.alloc().initWithWindow_(_win)
    _win.setWindowController_(WindowController)

    lable = TextFieldFactory(300, 50)
    textfield = TextFieldFactory(330, 24)
    button = ButtonFactory(85, 24)

    username_field = textfield.make_text_filed(150, (height - 100), "FunTV ID")
    password_field = textfield.make_text_filed(150, (height - 140), "Password", secure=True)

    _win.contentView().addSubview_(lable.make_label(100, (height-80), "Welcome to FunTV"))
    _win.contentView().addSubview_(username_field)
    _win.contentView().addSubview_(password_field)

    btn = button.make_button(400, (height - 180), "Log in")
    btn.setTarget_(viewController)
    btn.setAction_("submit:")
    _win.contentView().addSubview_(btn)

    def submit_(self, sender):
        username = self.username_field.stringValue()
        password = self.password_field.stringValue()

        if username == '' or password == '':
            self.shakeAnimationForView()
        else:
            ret = spider.login(username, password)
            if ret == '1':
                self._win.performClose_(self)
                NSApp.setDelegate_(sys_tray)
                sys_tray.updateLoginStatusBarMenu(username)
            else:
                self.shakeAnimationForView()

    def showWindow_(self, sender):
        self._win.makeKeyAndOrderFront_(None)
        #self._win.orderFrontRegardless()

    def windowWillClose_(self, notification):
        print("windowWillClose_")
        self._win.performClose_(self)
        NSApp.setDelegate_(sys_tray)

    def shakeAnimationForView(self):
        """Uses CoreAnimation to "shake" the window"""

        numberOfShakes = 3
        durationOfShake = 0.3
        vigourOfShake = 0.04

        frame = self._win.frame()
        shakeAnimation = CAKeyframeAnimation.animation()
        shakePath = CGPathCreateMutable()
        CGPathMoveToPoint(shakePath, None, NSMinX(frame), NSMinY(frame))
        for index in range(numberOfShakes):
            CGPathAddLineToPoint(
                shakePath, None,
                NSMinX(frame) - frame.size.width * vigourOfShake, NSMinY(frame))
            CGPathAddLineToPoint(
                shakePath, None,
                NSMinX(frame) + frame.size.width * vigourOfShake, NSMinY(frame))
        CGPathCloseSubpath(shakePath)
        shakeAnimation.setPath_(shakePath)
        shakeAnimation.setDuration_(durationOfShake)

        self._win.setAnimations_({'frameOrigin': shakeAnimation})
        self._win.animator().setFrameOrigin_(frame.origin)


sys_tray = MacTrayObject.alloc().init()

#@AppKit.objc.callbackFor(AppKit.CFNotificationCenterAddObserver)
#def networkChanged(center, observer, name, object, userInfo):
#    sys_tray.updateStatusBarMenu()


# Note: the following code can't run in class
def serve_forever():
    app = AppKit.NSApplication.sharedApplication()
    app.setDelegate_(sys_tray)

    # Listen for network change
   # nc = AppKit.CFNotificationCenterGetDarwinNotifyCenter()
   # AppKit.CFNotificationCenterAddObserver(nc, None, networkChanged, "com.apple.system.config.network_change", None, AppKit.CFNotificationSuspensionBehaviorDeliverImmediately)

    AppHelper.runEventLoop()


def main():
    serve_forever()


if __name__ == '__main__':
    main()
