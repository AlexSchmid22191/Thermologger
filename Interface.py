from datetime import datetime

import matplotlib
import wx
from pubsub.pub import sendMessage, subscribe, unsubscribe
from serial.tools.list_ports import comports

matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.style import use
from ThreadDecorators import in_main_thread
from numpy import append


use('App.mplstyle')


class LoggerInterface(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetTitle('Thermo Logger')

        self.status_bar = wx.StatusBar(parent=self)
        self.SetStatusBar(statusBar=self.status_bar)
        self.clear_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, source=self.clear_timer, handler=self.clear_status_bar)
        subscribe(listener=self.update_status_bar, topicName='engine.status')

        self.interval = 1000

        self.timer = wx.Timer()
        self.timer.Bind(event=wx.EVT_TIMER, handler=self.request_data)
        self.timer.Start(milliseconds=self.interval)

        self.menu_bar = Menubar()
        self.SetMenuBar(self.menu_bar)

        self.Bind(event=wx.EVT_MENU, handler=self.on_quit, id=wx.ID_CLOSE)
        self.Bind(event=wx.EVT_MENU, handler=self.save_image, id=wx.ID_SAVEAS)

        self.matplot = MatplotWX(parent=self)

        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.start, handler=self.matplot.start_plotting)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.stop, handler=self.matplot.stop_plotting)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.clear, handler=self.matplot.clear_plot)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.resume, handler=self.matplot.cont_plotting)

        self.Bind(wx.EVT_MENU_RANGE, handler=self.set_interval, id=self.menu_bar.plotmenu.inter.GetMenuItems()[0].GetId(),
                  id2=self.menu_bar.plotmenu.inter.GetMenuItems()[-1].GetId())

        hbox = wx.BoxSizer(orient=wx.HORIZONTAL)
        vbox = wx.BoxSizer(orient=wx.VERTICAL)
        vbox.Add(hbox)
        vbox.Add(self.matplot, flag=wx.EXPAND | wx.FIXED_MINSIZE, proportion=1)

        vbox.Fit(self)
        self.SetSizer(vbox)

        self.SetMinSize(self.GetSize())
        self.Show(True)

    def set_interval(self, event):
        inter = self.menu_bar.plotmenu.FindItemById(event.GetId()).GetItemLabel()
        self.interval = int(float(inter)*1000)
        self.timer.Start(milliseconds=self.interval)

    @in_main_thread
    def update_status_bar(self, text):
        self.status_bar.SetStatusText(text)
        self.clear_timer.Start(milliseconds=3000, oneShot=wx.TIMER_ONE_SHOT)

    @in_main_thread
    def clear_status_bar(self, *args):
        """Clear the status bar"""
        self.status_bar.SetStatusText('')

    def save_image(self, *args):
        dlg = wx.FileDialog(self.Parent, message="Choose log file destination", defaultDir='./Pics/',
                            style=wx.FD_SAVE | wx.FD_CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            log_path = dlg.GetPath()
            self.matplot.figure.savefig(log_path)
        dlg.Destroy()

    def on_quit(self, *args):
        self.Close()

    @staticmethod
    def request_data(*args):
        sendMessage(topicName='gui.request.sensor_temp')


class MatplotWX(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        subscribe(listener=self.update_temperature, topicName='engine.answer.sensor_temp')

        self.is_plotting = False

        self.startime = datetime.now()

        self.figure = Figure(figsize=(5, 4))

        self.axes = self.figure.add_subplot(111)

        self.text = self.axes.text(0.05, 0.9, '{:.2f} °C'.format(0), transform=self.axes.transAxes, size=12)

        self.axes.set_xlabel('Time (s)')
        self.axes.set_ylabel('Temperature (°C)')

        self.sens_temp_plot, = self.axes.plot([], marker='o')

        self.canvas = FigureCanvas(self, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, flag=wx.GROW | wx.FIXED_MINSIZE, proportion=2)
        self.SetSizer(self.sizer)
        self.Fit()
        self.figure.tight_layout()

    @in_main_thread
    def update_temperature(self, temp):
        self.text.set_text('{:.2f} °C'.format(temp))
        self.figure.canvas.draw()

    @in_main_thread
    def add_sensor_temp_point(self, temp):
        delta_t = datetime.now() - self.startime
        time = delta_t.days*86400.0 + delta_t.seconds + delta_t.microseconds/1000000.0

        self.sens_temp_plot.set_xdata(append(self.sens_temp_plot.get_xdata(), time))
        self.sens_temp_plot.set_ydata(append(self.sens_temp_plot.get_ydata(), temp))

        self.axes.relim()
        self.axes.autoscale_view()
        self.figure.canvas.draw()

    def start_plotting(self, *args):
        if not self.is_plotting:
            self.is_plotting = True
            self.startime = datetime.now()
            subscribe(topicName='engine.answer.sensor_temp', listener=self.add_sensor_temp_point)

    def stop_plotting(self, *args):
        self.is_plotting = False
        unsubscribe(topicName='engine.answer.sensor_temp', listener=self.add_sensor_temp_point)

    def cont_plotting(self, *args):
        self.is_plotting = True
        subscribe(topicName='engine.answer.sensor_temp', listener=self.add_sensor_temp_point)

    def clear_plot(self, args):
        self.sens_temp_plot.set_xdata([])
        self.sens_temp_plot.set_ydata([])
        self.figure.canvas.draw()


class Menubar(wx.MenuBar):
    def __init__(self, _=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        filemenu = wx.Menu()
        self.savefig = filemenu.Append(item='Save Plot', id=wx.ID_SAVEAS)
        filemenu.Append(item='Quit', id=wx.ID_CLOSE)

        self.logmenu = LoggingMenu()
        self.dev_menu = DeviceMenu()
        self.plotmenu = PlottingMenu()

        self.Append(filemenu, 'File')
        self.Append(self.dev_menu, 'Devices')
        self.Append(self.logmenu, 'Logging')
        self.Append(self.plotmenu, 'Plotting')


class DeviceMenu(wx.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sensor_type_menu = wx.Menu()
        self.sensor_type_menu.Append(item='Thermoplatino', id=wx.ID_ANY, kind=wx.ITEM_RADIO)
        self.sensor_type_menu.Append(item='Thermolino', id=wx.ID_ANY, kind=wx.ITEM_RADIO)
        self.sensor_type_menu.Append(item='Keithly 2000', id=wx.ID_ANY, kind=wx.ITEM_RADIO)
        self.sensor_type_menu.Append(item='Pyrometer', id=wx.ID_ANY, kind=wx.ITEM_RADIO)

        self.sensor_com_menu = PortMenu()
        self.AppendSubMenu(text='Sensor type', submenu=self.sensor_type_menu)
        self.AppendSubMenu(text='Sensor port', submenu=self.sensor_com_menu)
        sensor_connect = self.Append(id=wx.ID_ANY, item='Connect sensor', kind=wx.ITEM_CHECK)

        self.Bind(event=wx.EVT_MENU, handler=self.connect_sensor, source=sensor_connect)

    def connect_sensor(self, event):
        item = self.FindItemById(event.GetId())

        if item.IsChecked():
            sensor_port, sensor_type = None, None
            for port_item in self.sensor_com_menu.GetMenuItems():
                if port_item.IsChecked():
                    sensor_port = self.sensor_com_menu.port_dict[port_item.GetItemLabelText()]

            for type_item in self.sensor_type_menu.GetMenuItems():
                if type_item.IsChecked():
                    sensor_type = type_item.GetItemLabelText()

            sendMessage(topicName='gui.con.connect_sensor', sensor_type=sensor_type, sensor_port=sensor_port)

        else:
            sendMessage(topicName='gui.con.disconnect_sensor')


class PortMenu(wx.Menu):
    def __init__(self):
        super().__init__()

        self.portdict = self.port_dict = {port[1]: port[0] for port in comports()}
        self.portItems = [wx.MenuItem(parentMenu=self, id=wx.ID_ANY, text=port, kind=wx.ITEM_RADIO)
                          for port in list(self.port_dict.keys())]

        for item in self.portItems:
            self.Append(item)


class LoggingMenu(wx.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        start = self.Append(item='Start', id=wx.ID_ANY)
        stop = self.Append(item='Stop', id=wx.ID_ANY)
        cont = self.Append(item='Continue', id=wx.ID_ANY)

        self.Bind(event=wx.EVT_MENU, source=start, handler=self.start_log)
        self.Bind(event=wx.EVT_MENU, source=stop, handler=self.stop_log)
        self.Bind(event=wx.EVT_MENU, source=cont, handler=self.continue_log)

        self.inter = wx.Menu()
        for inter in ('0.2', '0.5', '1', '2'):
            self.inter.Append(item=inter, id=wx.ID_ANY, kind=wx.ITEM_RADIO)

        self.inter.GetMenuItems()[2].Check()

        self.inter.Bind(wx.EVT_MENU, handler=self.set_interval)

        self.AppendSubMenu(submenu=self.inter, text='Update interval (ms)')

    def start_log(self, *args):
        dlg = wx.FileDialog(self.Parent, message="Choose log file destination", defaultDir='./Logs/',
                            style=wx.FD_SAVE | wx.FD_CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            log_path = dlg.GetPath()
            if not log_path[-4:] == '.dat':
                log_path += '.dat'
            sendMessage(topicName='gui.log.filename', filename=log_path)
            sendMessage(topicName='gui.log.start')
        dlg.Destroy()

        args[0].Skip()

    def set_interval(self, event):
        inter = float(self.FindItemById(event.GetId()).GetItemLabel())
        sendMessage('gui.log.interval', inter=inter)

    @staticmethod
    def stop_log(*args):
        sendMessage(topicName='gui.log.stop')

    @staticmethod
    def continue_log(*args):
        sendMessage(topicName='gui.log.continue')


class PlottingMenu(wx.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.start = self.Append(item='Start', id=wx.ID_ANY)
        self.stop = self.Append(item='Stop', id=wx.ID_ANY)
        self.resume = self.Append(item='Resume', id=wx.ID_ANY)
        self.clear = self.Append(item='Clear', id=wx.ID_ANY)
        self.AppendSeparator()

        self.inter = wx.Menu()
        for inter in ('0.5', '1', '2', '5'):
            self.inter.Append(item=inter, id=wx.ID_ANY, kind=wx.ITEM_RADIO)

        self.inter.GetMenuItems()[1].Check()

        self.AppendSubMenu(submenu=self.inter, text='Update interval (s)')
