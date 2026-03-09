"""D-Bus service for KDE Plasma and other desktop environment integration.

Exposes Voice Notepad actions via the session D-Bus, allowing desktop
environments like KDE Plasma to trigger actions via their native
global shortcut systems.

Usage from KDE System Settings → Shortcuts → Custom Shortcuts:
    dbus-send --session --type=method_call \
        --dest=com.danielrosehill.VoiceNotepad \
        /Actions com.danielrosehill.VoiceNotepad.Actions.Toggle

Available actions: Toggle, TapToggle, Transcribe, Clear, Append, Retake
"""

import logging
import threading
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

DBUS_SERVICE_NAME = "com.danielrosehill.VoiceNotepad"
DBUS_OBJECT_PATH = "/Actions"
DBUS_INTERFACE = "com.danielrosehill.VoiceNotepad.Actions"

# Introspection XML for the D-Bus interface
INTROSPECTION_XML = f"""<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
"http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node>
  <interface name="{DBUS_INTERFACE}">
    <method name="Toggle">
      <annotation name="org.freedesktop.DBus.Method.NoReply" value="true"/>
    </method>
    <method name="TapToggle">
      <annotation name="org.freedesktop.DBus.Method.NoReply" value="true"/>
    </method>
    <method name="Transcribe">
      <annotation name="org.freedesktop.DBus.Method.NoReply" value="true"/>
    </method>
    <method name="Clear">
      <annotation name="org.freedesktop.DBus.Method.NoReply" value="true"/>
    </method>
    <method name="Append">
      <annotation name="org.freedesktop.DBus.Method.NoReply" value="true"/>
    </method>
    <method name="Retake">
      <annotation name="org.freedesktop.DBus.Method.NoReply" value="true"/>
    </method>
  </interface>
  <interface name="org.freedesktop.DBus.Introspectable">
    <method name="Introspect">
      <arg name="xml_data" type="s" direction="out"/>
    </method>
  </interface>
</node>"""


class DBusActionService:
    """Exposes app actions on the session D-Bus for desktop integration."""

    def __init__(self):
        self._callbacks: Dict[str, Callable] = {}
        self._bus = None
        self._bus_name = None
        self._running = False

    def register_action(self, name: str, callback: Callable):
        """Register a callback for a D-Bus action.

        Args:
            name: Action name (Toggle, TapToggle, Transcribe, Clear, Append, Retake)
            callback: Function to call when the action is invoked via D-Bus
        """
        self._callbacks[name] = callback

    def start(self):
        """Start the D-Bus service on the session bus."""
        try:
            import dbus
            import dbus.service
            import dbus.mainloop.glib
        except ImportError:
            logger.info("dbus-python not available, D-Bus integration disabled. "
                        "Install with: pip install dbus-python")
            return False

        try:
            # Use GLib mainloop for dbus (compatible with Qt's event loop)
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

            bus = dbus.SessionBus()
            bus_name = dbus.service.BusName(DBUS_SERVICE_NAME, bus, do_not_queue=True)

            # Create the service object
            self._service_obj = _DBusServiceObject(bus_name, self._callbacks)
            self._bus = bus
            self._bus_name = bus_name
            self._running = True

            logger.info(f"D-Bus service registered: {DBUS_SERVICE_NAME}")
            return True

        except dbus.exceptions.NameExistsException:
            logger.warning(f"D-Bus name {DBUS_SERVICE_NAME} already claimed (another instance running?)")
            return False
        except Exception as e:
            logger.warning(f"Failed to register D-Bus service: {e}")
            return False

    def stop(self):
        """Stop the D-Bus service."""
        self._running = False
        # dbus-python cleans up when the bus name goes out of scope
        self._bus_name = None
        self._bus = None
        self._service_obj = None


def _create_dbus_service_class():
    """Dynamically create the D-Bus service class (requires dbus-python)."""
    try:
        import dbus
        import dbus.service
    except ImportError:
        return None

    class _ServiceObject(dbus.service.Object):
        """D-Bus object that dispatches method calls to registered callbacks."""

        def __init__(self, bus_name, callbacks):
            super().__init__(bus_name, DBUS_OBJECT_PATH)
            self._callbacks = callbacks

        @dbus.service.method(DBUS_INTERFACE, in_signature='', out_signature='')
        def Toggle(self):
            cb = self._callbacks.get("Toggle")
            if cb:
                cb()

        @dbus.service.method(DBUS_INTERFACE, in_signature='', out_signature='')
        def TapToggle(self):
            cb = self._callbacks.get("TapToggle")
            if cb:
                cb()

        @dbus.service.method(DBUS_INTERFACE, in_signature='', out_signature='')
        def Transcribe(self):
            cb = self._callbacks.get("Transcribe")
            if cb:
                cb()

        @dbus.service.method(DBUS_INTERFACE, in_signature='', out_signature='')
        def Clear(self):
            cb = self._callbacks.get("Clear")
            if cb:
                cb()

        @dbus.service.method(DBUS_INTERFACE, in_signature='', out_signature='')
        def Append(self):
            cb = self._callbacks.get("Append")
            if cb:
                cb()

        @dbus.service.method(DBUS_INTERFACE, in_signature='', out_signature='')
        def Retake(self):
            cb = self._callbacks.get("Retake")
            if cb:
                cb()

        @dbus.service.method("org.freedesktop.DBus.Introspectable",
                             in_signature='', out_signature='s')
        def Introspect(self):
            return INTROSPECTION_XML

    return _ServiceObject


# Create the class at module level (None if dbus-python unavailable)
_DBusServiceObject = _create_dbus_service_class()
