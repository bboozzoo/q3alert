#!/usr/bin/env python

import gtk
import gobject
import glib
import pynotify
import socket
from os import makedirs
from ConfigParser import SafeConfigParser
from os.path import exists
from io import BytesIO

def singleton(cls):
    """
    signleton decorator functionb
    """
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

class Q3Status(object):
    """
    Q3 status wrapper
    """
    
    def __init__(self, data_map):
        """
        """
        self._data = data_map

    def get(self, key, adapter):
        """
        return contents of field
        """
        value = self._data.get(key)

        if not value:
            raise KeyError

        if adapter:
            value = adapter(value)

        return value
        
class Q3StatusMonitor(gobject.GObject):
    """
    class to handle polling the state and sending notifications
    """
    __gsignals__ = { 
        'status-update' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (object, ))
        }

    def __init__(self, ):
        """
        constructor
        """
        self.__gobject_init__()

        self._conf = Q3StatusConf()
        self._host = self._conf.get('net', 'host')
        self._port = self._conf.get('net', 'port', int)

        self._req_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._glib_io_tag = None
 

    def _send_status_req(self, ):
        """
        get status from server
        """
        
        if not self._host or \
                not self._port or \
                not self._req_socket:
            return None

        print 'get status'
        request = '\xff\xff\xff\xffgetinfo xxx'

        self._glib_io_tag = glib.io_add_watch(self._req_socket.fileno(), glib.IO_IN, self._data_ready_cb)
        self._req_socket.sendto(request, (self._host, self._port))

    def _data_ready_cb(self, source, condition):
        """
        callback for data ready on request socket
        """
        # fetch data
        response = self._req_socket.recv(2000)
        # handle response
        response_data = response.split('\\')
        print response_data
        
        # sanity check
        header = response_data[0][4:].strip()
        print header
        if header != 'infoResponse':
            return None
        
        # skip header
        response_data = response_data[1:]
    
        # check length of remanining parameters - should be even
        # these are key-value pairs
        if len(response_data) % 2 != 0:
            return None
        
        keys = [response_data[i] for i in range(len(response_data)) if i % 2 == 0]
        values = [response_data[i] for i in range(len(response_data)) if i % 2 == 1]
        request_map = dict(zip(keys, values))
        
        self.emit('status-update', Q3Status(request_map))

        # clear source tag
        self._glib_io_tag = None
        # return false to remove from watch
        return False
        

    def poll(self, ):
        """
        """
        self._send_status_req()
        
class Q3StatusUI(gobject.GObject):
    """
    user interface
    """

    __gsignals__ = {
        'quit' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'poll-enable-change' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (bool,)),
        'settings-updated' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    __right_click_menu = '''
    <ui>
      <popup name="RightClickMenu">
        <menuitem action="Enable" />
        <menuitem action="Settings" />
        <menuitem action="Quit"/>
      </popup>
    </ui>
    '''

    def __init__(self, ):
        """
        constructor
        """
        self.__gobject_init__()
        self._config = Q3StatusConf()

        # build a menu for right click
        self._init_menu()

        # build settings dialog
        self._init_settings_dialog()

        # status (tray) icon
        self._init_icon()

    def _init_menu(self, ):
        """
        initialize menu for right click
        """
        ui = gtk.UIManager()
        actiongroup = gtk.ActionGroup('RightClick')

        actiongroup.add_toggle_actions([('Enable', None, '_Enable polling', None,
                                         'Enable server polling', self._toggle_polling_cb)])

        actiongroup.add_actions([('Quit', gtk.STOCK_QUIT, '_Quit', None,
                                  'Exit program', self._quit_cb),
                                 ('Settings', None, '_Settings', None,
                                  'Show settings', self._show_settings_cb)])

        ui.insert_action_group(actiongroup, 0)
        print self.__right_click_menu
        ui.add_ui_from_string(self.__right_click_menu)

        self._menu = ui.get_widget('/RightClickMenu')
        self._enable_toggle = ui.get_widget('/RightClickMenu/Enable')

        enabled_status = self._config.get('core', 'enable', bool)
        print 'polling enabled:', enabled_status
        self._enable_toggle.set_property('active', enabled_status)

    def _init_settings_dialog(self, ):
        """
        initialize settings dialog
        """
        builder = gtk.Builder()
        builder.add_from_file('settings-dialog.ui')
        d = builder.get_object('SettingsDialog')

        d.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        # save the button for later use
        # as the button will be disabled if any of the settings is invalid
        self._settings_button_ok = d.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)

        self._setting_ip_entry = builder.get_object('IPAddress')
        self._setting_ip_entry.connect('changed', self._setting_ip_entry_changed_cb, self)

        self._setting_port_entry = builder.get_object('Port')
        self._setting_port_entry.connect('changed', self._setting_port_entry_changed_cb, self)

        self._setting_poll_interval = builder.get_object('PollInterval')
        self._setting_poll_interval.set_lower(1)

        self._settings_dialog = d

    def _setting_ip_entry_changed_cb(self, entry, ui):
        """
        IP address entry has been changed
        Arguments:
        - `entry`:
        - `ui`:
        """
        pass

    def _setting_port_entry_changed_cb(self, entry, ui):
        """
        port entry has been changed
        Arguments:
        - `entry`:
        - `ui`:
        """
        bad = False
        port = 0
        try:
            port = int(entry.get_text())
        except:
            bad = True

        if not bad:
            if port <= 0 or port >= 65535:
                bad = True

        if bad:
            entry.set_property('secondary-icon-stock', gtk.STOCK_DIALOG_WARNING)
            entry.set_property('secondary-icon-tooltip-text', 'Incorrect port value')
        else:
            entry.set_property('secondary-icon-stock', None)

    def _init_icon(self, ):
        """
        initialize status icon
        """
        # load icons
        self._icon_bw = gtk.gdk.pixbuf_new_from_file('bw.svg')
        self._icon_color = gtk.gdk.pixbuf_new_from_file('colored.svg')
        
        # create status icon
        self._status_icon = gtk.status_icon_new_from_pixbuf(self._icon_bw)

        # connect signals
        self._status_icon.connect('popup-menu', self._show_popup_menu_cb)

    def show(self, ):
        """
        """
        pass

    def _toggle_polling_cb(self, b):
        """
        
        """
        print 'status:', self._enable_toggle.get_active()
        self.emit('poll-enable-change', self._enable_toggle.get_active())

    def _show_popup_menu_cb(self, status_icon, button, activate_time):
        """
        callback for right click
        Arguments:
        - `status_icon`:
        - `button`:
        - `activate_time`:
        """
        if self._menu:
            self._menu.popup(None, None, gtk.status_icon_position_menu, 
                             button, activate_time, status_icon)

    def _update_settings(self, ):
        """
        put new settings into configuration
        """
        ip = self._setting_ip_entry.get_text()
        self._config.set('net', 'host', ip)

        port = self._setting_port_entry.get_text()
        self._config.set('net', 'port', port)

        interval = int(self._setting_poll_interval.get_value())
        self._config.set('core', 'poll_interval', interval)

    def _fill_settings_dialog(self, ):
        """
        fill entries in settings dialog with current values
        """
        self._setting_ip_entry.set_text(self._config.get('net', 'host'))
        self._setting_port_entry.set_text(self._config.get('net', 'port'))
        self._setting_poll_interval.set_value(self._config.get('core', 'poll_interval', int))

    def _show_settings_cb(self, b):
        """
        show settings clicked
        """
        print 'show settings'
        # fill entries in dialog with data
        self._fill_settings_dialog()

        # show dialog, wait for response
        response = self._settings_dialog.run()
        self._settings_dialog.hide()

        # emit signal if user has changed configuration
        if response == gtk.RESPONSE_ACCEPT:
            # update settings if accepted
            self._update_settings()
            # signal that settings need to be saved
            self.emit('settings-updated')
        
    def _quit_cb(self, b):
        """
        quit clicked
        """
        self.emit('quit')

    def _display_notification(status):
        """
        """
        print 'show notification'
        n = pynotify.Notification('Qstatus', 
                                  'Game in progress\n'
                                  'Map: %s\n'
                                  'Players: %s\n' % (status['mapname'],
                                                     status['clients']))
        n.show()

class Q3StatusApp(gobject.GObject):
    """
    app core
    """
    def __init__(self, ):
        """
        """
        self.__gobject_init__()

        self._conf = Q3StatusConf()
        
        self._UI = Q3StatusUI()
        self._UI.connect('quit', self._ui_quit_cb)
        self._UI.connect('poll-enable-change', self._polling_enable_changed_cb)
        self._UI.connect('settings-updated', self._settings_updated_cb)

        self._monitor = Q3StatusMonitor()
        self._monitor.connect('status-update', self._status_update_cb)

        self._poll_interval = self._conf.get('core', 'poll_interval', int)
        self._polling = self._conf.get('core', 'enable', bool)
        if self._polling:
            self._enable_polling()
        
    def _ui_quit_cb(self, ui):
        """
        UI callback for quit operation
        """
        gtk.main_quit()

    def _status_update_cb(self, q3statusmonitor, status):
        """
        callback for status update from monitor
        """
        print 'status update'

    def _poll_timeout_cb(self):
        """
        polling timeout - check server status
        """
        retval = True
        print 'poll timeout'

        # check the state of polling variable
        # it's not possible to remove timeout from events queue (or is it?)
        # hence this workaround
        if self._polling:
            self._monitor.poll()
        else:
            retval = False

        return retval

    def run(self, ):
        """
        enter main loop
        """
        self._UI.show()
        gtk.main()

    def _polling_enable_changed_cb(self, b, status):
        """
        polling status was toggled
        Arguments:
        - `b`:
        - `status`: polling status
        """
        if status:
            if self._polling:
                print 'already enabled?'
            else:
                self._enable_polling()
        else:
            self._disable_polling()

    def _enable_polling(self, ):
        """
        enable polling - reload poll interval, set timeout and poll flag
        """
        self._poll_interval = self._conf.get('core', 'poll_interval', int)
        self._polling = True
        # start polling
        glib.timeout_add_seconds(self._poll_interval, self._poll_timeout_cb)       

    def _disable_polling(self, ):
        """
        disable polling - set polling flag
        """
        self._polling = False

    def _settings_updated_cb(self, b):
        """
        """
        print 'settings update'
        self._conf.sync()



__default_config__ = '''
[core]
poll_interval = 20
enable = 1

[net]
port = 27960
host = 10.10.16.24
'''

@singleton
class Q3StatusConf(object):
    """
    configuration wrapper
    """
    
    def __init__(self, ):
        """
        """
        self._config = SafeConfigParser()
        
        conf_dir = glib.get_user_config_dir() + '/q3status'
        self._config_path = conf_dir + '/conf'

        if not exists(conf_dir):
            makedirs(conf_dir)
            
        if not exists(self._config_path):
            self._fill_default_config()

        self._load_config()

    def _load_config(self, ):
        """
        parse configuration file
        """
        # try to load the configuration file
        if exists(self._config_path):
            self._config.read(self._config_path)

    def _fill_default_config(self, ):
        """
        """
        # first use the default configuration
        self._config.readfp(BytesIO(__default_config__))
        # now try to load the configuration file
        self.sync()

    def sync(self, ):
        """
        save configuration
        """
        with open(self._config_path, 'w') as config_file:
            config_file.truncate()
            self._config.write(config_file)

    def get(self, section, key, adapter = None):
        """
        get value of setting
        Arguments:
        - `section`: section name
        - `key`: key name
        - `adapter`: adapter function for type conversion
        """
        val = None
        try:
            val = self._config.get(section, key)
        except:
            raise KeyError

        # apply adapter if provided
        if adapter:
            val = adapter(val)

        return val

    def set(self, section, key, value):
        """
        set value of key in group
        Arguments:
        - `section`: section name
        - `key`: key
        """
        # add section it if does not exist
        if not self._config.has_section(section):
            self._config.add_section(section)
        # now store the value
        self._config.set(section, key, str(value))
            
if __name__ == '__main__':
    app = Q3StatusApp()
    app.run()



