"""
PyQt6 signal-based data bus for inter-tab communication.

This module provides a QObject-based data bus that uses PyQt signals and slots
for real-time communication between tabs while maintaining type safety.
"""

import logging
from typing import Dict, Optional, List, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from anafis.gui.shared.data_transforms import (
    DataPayload,
    TabData,
    create_data_message,
    validate_data_message,
    get_data_summary,
)
from anafis.core.data_structures import TabRegistration, BusStatistics, RegisteredTabs

logger = logging.getLogger(__name__)


class DataBusSignals(QObject):
    """Signal definitions for the data bus."""

    # Data transmission signals
    data_published = pyqtSignal(dict)  # DataPayload
    data_received = pyqtSignal(str, dict)  # (tab_id, DataPayload)

    # Tab management signals
    tab_registered = pyqtSignal(str, str)  # (tab_id, tab_type)
    tab_unregistered = pyqtSignal(str)  # (tab_id)

    # Status and error signals
    transmission_error = pyqtSignal(str, str)  # (tab_id, error_message)
    bus_status_changed = pyqtSignal(bool)  # (is_active)

    # Debug signals
    message_validated = pyqtSignal(dict, bool)  # (message, is_valid)


class DataBus(QObject):
    """
    PyQt6 signal-based data bus for inter-tab communication.

    Provides a centralized hub for tabs to send and receive data
    using PyQt's signal-slot mechanism for thread-safe communication.
    """

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        # Initialize signal handler
        self.signals = DataBusSignals(self)

        # Tab registry
        self.registered_tabs: Dict[str, TabRegistration] = {}

        # Data routing and filtering
        self.data_filters: Dict[str, Callable[[DataPayload], bool]] = {}
        self.subscription_map: Dict[str, List[str]] = {}  # tab_id -> [data_types]

        # Configuration
        self.max_message_history = 100
        self.enable_validation = True
        self.enable_logging = True

        # Message history for debugging
        self.message_history: List[DataPayload] = []

        # Connect internal signals
        self._connect_internal_signals()

        # Status
        self.is_active = False
        self._activate_bus()

        logger.info("Data bus initialized successfully")

    def _connect_internal_signals(self) -> None:
        """Connect internal signal handlers."""
        self.signals.data_published.connect(self._handle_data_published)
        self.signals.tab_registered.connect(self._handle_tab_registered)
        self.signals.tab_unregistered.connect(self._handle_tab_unregistered)

    def _activate_bus(self) -> None:
        """Activate the data bus."""
        self.is_active = True
        self.signals.bus_status_changed.emit(True)
        logger.info("Data bus activated")

    def deactivate_bus(self) -> None:
        """Deactivate the data bus."""
        self.is_active = False
        self.signals.bus_status_changed.emit(False)
        logger.info("Data bus deactivated")

    def register_tab(
        self,
        tab_id: str,
        tab_type: str,
        callback: Optional[Callable[[DataPayload], None]] = None,
    ) -> bool:
        """
        Register a tab with the data bus.

        Args:
            tab_id: Unique identifier for the tab
            tab_type: Type of tab (spreadsheet, fitting, etc.)
            callback: Optional callback function for receiving data

        Returns:
            True if registration successful, False otherwise
        """
        if not self.is_active:
            logger.error(f"Cannot register tab {tab_id}: Data bus not active")
            return False

        if tab_id in self.registered_tabs:
            logger.warning(f"Tab {tab_id} already registered, updating registration")

        registration = TabRegistration(tab_id, tab_type, callback)
        self.registered_tabs[tab_id] = registration

        # Initialize subscription list
        if tab_id not in self.subscription_map:
            self.subscription_map[tab_id] = []

        self.signals.tab_registered.emit(tab_id, tab_type)

        if self.enable_logging:
            logger.info(f"Tab registered: {tab_id} (type: {tab_type})")

        return True

    def unregister_tab(self, tab_id: str) -> bool:
        """
        Unregister a tab from the data bus.

        Args:
            tab_id: Unique identifier for the tab

        Returns:
            True if unregistration successful, False otherwise
        """
        if tab_id not in self.registered_tabs:
            logger.warning(f"Attempted to unregister non-existent tab: {tab_id}")
            return False

        del self.registered_tabs[tab_id]

        # Clean up subscriptions
        if tab_id in self.subscription_map:
            del self.subscription_map[tab_id]

        # Clean up filters
        filter_keys_to_remove = [k for k in self.data_filters.keys() if k.startswith(f"{tab_id}_")]
        for key in filter_keys_to_remove:
            del self.data_filters[key]

        self.signals.tab_unregistered.emit(tab_id)

        if self.enable_logging:
            logger.info(f"Tab unregistered: {tab_id}")

        return True

    def subscribe_to_data_type(self, tab_id: str, data_type: str) -> bool:
        """
        Subscribe a tab to receive specific data types.

        Args:
            tab_id: ID of the subscribing tab
            data_type: Type of data to subscribe to

        Returns:
            True if subscription successful, False otherwise
        """
        if tab_id not in self.registered_tabs:
            logger.error(f"Cannot subscribe: Tab {tab_id} not registered")
            return False

        if tab_id not in self.subscription_map:
            self.subscription_map[tab_id] = []

        if data_type not in self.subscription_map[tab_id]:
            self.subscription_map[tab_id].append(data_type)

            if self.enable_logging:
                logger.debug(f"Tab {tab_id} subscribed to data type: {data_type}")

            return True

        return False

    def unsubscribe_from_data_type(self, tab_id: str, data_type: str) -> bool:
        """
        Unsubscribe a tab from receiving specific data types.

        Args:
            tab_id: ID of the subscribing tab
            data_type: Type of data to unsubscribe from

        Returns:
            True if unsubscription successful, False otherwise
        """
        if tab_id not in self.subscription_map:
            return False

        if data_type in self.subscription_map[tab_id]:
            self.subscription_map[tab_id].remove(data_type)

            if self.enable_logging:
                logger.debug(f"Tab {tab_id} unsubscribed from data type: {data_type}")

            return True

        return False

    def add_data_filter(self, filter_id: str, filter_func: Callable[[DataPayload], bool]) -> None:
        """
        Add a data filter function.

        Args:
            filter_id: Unique identifier for the filter
            filter_func: Function that returns True if data should pass through
        """
        self.data_filters[filter_id] = filter_func
        logger.debug(f"Data filter added: {filter_id}")

    def remove_data_filter(self, filter_id: str) -> bool:
        """
        Remove a data filter function.

        Args:
            filter_id: Unique identifier for the filter

        Returns:
            True if filter was removed, False if it didn't exist
        """
        if filter_id in self.data_filters:
            del self.data_filters[filter_id]
            logger.debug(f"Data filter removed: {filter_id}")
            return True
        return False

    def publish_data(
        self,
        source_tab_id: str,
        data_type: str,
        data: TabData,
        metadata: Optional[Dict[str, object]] = None,
    ) -> bool:
        """
        Publish data to the bus.

        Args:
            source_tab_id: ID of the tab publishing the data
            data_type: Type of data being published
            data: The actual data payload
            metadata: Optional metadata

        Returns:
            True if publication successful, False otherwise
        """
        if not self.is_active:
            logger.error("Cannot publish data: Data bus not active")
            return False

        if source_tab_id not in self.registered_tabs:
            logger.error(f"Cannot publish data: Tab {source_tab_id} not registered")
            return False

        # Get source tab info
        source_tab = self.registered_tabs[source_tab_id]

        # Create data message
        message = create_data_message(
            source_tab_id=source_tab_id,
            source_tab_type=source_tab.tab_type,
            data_type=data_type,
            data=data,
            metadata=metadata,
        )

        # Validate message if enabled
        if self.enable_validation:
            is_valid, errors = validate_data_message(message)
            self.signals.message_validated.emit(message, is_valid)

            if not is_valid:
                error_msg = f"Data validation failed: {', '.join(errors)}"
                logger.error(error_msg)
                self.signals.transmission_error.emit(source_tab_id, error_msg)
                return False

        # Apply filters
        for filter_func in self.data_filters.values():
            try:
                if not filter_func(message):
                    logger.debug(f"Data filtered out by filter for tab {source_tab_id}")
                    return False
            except Exception as e:
                logger.error(f"Error in data filter: {e}")

        # Update tab statistics
        source_tab.message_count += 1
        source_tab.last_activity = message["timestamp"]

        # Add to history
        if len(self.message_history) >= self.max_message_history:
            self.message_history.pop(0)
        self.message_history.append(message)

        # Emit publication signal
        self.signals.data_published.emit(message)

        if self.enable_logging:
            summary = get_data_summary(data)
            logger.info(f"Data published: {source_tab_id} -> {data_type} ({summary['type']})")

        return True

    def _handle_data_published(self, message: DataPayload) -> None:
        """Handle internally published data and route to subscribers."""
        data_type = message["data_type"]
        source_tab_id = message["source_tab_id"]

        # Route to subscribed tabs
        for tab_id, subscriptions in self.subscription_map.items():
            # Don't send data back to the source
            if tab_id == source_tab_id:
                continue

            # Check if tab is subscribed to this data type
            if data_type not in subscriptions:
                continue

            # Check if tab is still registered and active
            if tab_id not in self.registered_tabs:
                continue

            tab_registration = self.registered_tabs[tab_id]
            if not tab_registration.is_active:
                continue

            # Deliver message
            try:
                if tab_registration.callback:
                    tab_registration.callback(message)

                self.signals.data_received.emit(tab_id, message)

                if self.enable_logging:
                    logger.debug(f"Data delivered: {source_tab_id} -> {tab_id} ({data_type})")

            except Exception as e:
                error_msg = f"Error delivering data to {tab_id}: {e}"
                logger.error(error_msg)
                self.signals.transmission_error.emit(tab_id, error_msg)

    def _handle_tab_registered(self, tab_id: str, tab_type: str) -> None:
        """Handle tab registration events."""
        logger.debug(f"Tab registration event: {tab_id} ({tab_type})")

    def _handle_tab_unregistered(self, tab_id: str) -> None:
        """Handle tab unregistration events."""
        logger.debug(f"Tab unregistration event: {tab_id}")

    def get_registered_tabs(self) -> Dict[str, RegisteredTabs]:
        """
        Get information about all registered tabs.

        Returns:
            Dictionary with tab information
        """
        return {
            tab_id: {
                "tab_type": reg.tab_type,
                "is_active": reg.is_active,
                "message_count": reg.message_count,
                "last_activity": reg.last_activity,
                "subscriptions": self.subscription_map.get(tab_id, []),
            }
            for tab_id, reg in self.registered_tabs.items()
        }

    def get_message_history(self, limit: Optional[int] = None) -> List[DataPayload]:
        """
        Get recent message history.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        if limit is None:
            return self.message_history.copy()
        return self.message_history[-limit:].copy()

    def clear_message_history(self) -> None:
        """Clear the message history."""
        self.message_history.clear()
        logger.debug("Message history cleared")

    def get_bus_statistics(self) -> BusStatistics:
        """
        Get data bus statistics.

        Returns:
            Dictionary with bus statistics
        """
        total_messages = sum(reg.message_count for reg in self.registered_tabs.values())
        active_tabs = sum(1 for reg in self.registered_tabs.values() if reg.is_active)

        return {
            "is_active": self.is_active,
            "total_registered_tabs": len(self.registered_tabs),
            "active_tabs": active_tabs,
            "total_messages_processed": total_messages,
            "message_history_size": len(self.message_history),
            "active_filters": len(self.data_filters),
            "total_subscriptions": sum(len(subs) for subs in self.subscription_map.values()),
        }

    def shutdown(self) -> None:
        """Shutdown the data bus and clean up resources."""
        logger.info("Shutting down data bus")

        # Unregister all tabs
        tab_ids = list(self.registered_tabs.keys())
        for tab_id in tab_ids:
            self.unregister_tab(tab_id)

        # Clear filters and history
        self.data_filters.clear()
        self.message_history.clear()
        self.subscription_map.clear()

        # Deactivate
        self.deactivate_bus()

        logger.info("Data bus shutdown complete")


# Global data bus instance
_global_data_bus: Optional[DataBus] = None


def get_global_data_bus() -> DataBus:
    """
    Get or create the global data bus instance.

    Returns:
        The global DataBus instance
    """
    global _global_data_bus

    if _global_data_bus is None:
        # Try to get QApplication instance as parent
        app = QApplication.instance()
        _global_data_bus = DataBus(app)

    return _global_data_bus


def shutdown_global_data_bus() -> None:
    """Shutdown the global data bus."""
    global _global_data_bus

    if _global_data_bus is not None:
        _global_data_bus.shutdown()
        _global_data_bus = None
