"""
Base tab class with data bus integration.

This module provides a base class for tabs that need to communicate
with other tabs through the data bus system.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget

from .data_bus import get_global_data_bus, DataBus
from .data_transforms import DataPayload, TabData


logger = logging.getLogger(__name__)


class DataBusEnabledTab(QWidget):
    """
    Base class for tabs that integrate with the data bus.
    
    Provides automatic registration/unregistration with the data bus,
    data publishing/receiving capabilities, and signal-based communication.
    """
    
    # Signals for data bus events
    data_received = pyqtSignal(dict)  # DataPayload
    data_published = pyqtSignal(str, dict)  # (data_type, DataPayload)
    bus_error = pyqtSignal(str)  # error_message
    
    def __init__(
        self, 
        tab_id: str, 
        tab_type: str, 
        parent: Optional[QWidget] = None
    ):
        """
        Initialize data bus enabled tab.
        
        Args:
            tab_id: Unique identifier for this tab
            tab_type: Type of tab (spreadsheet, fitting, etc.)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.tab_id = tab_id
        self.tab_type = tab_type
        
        # Data bus integration
        self.data_bus: Optional[DataBus] = None
        self.subscriptions: List[str] = []
        
        # Auto-connect to data bus
        self._connect_to_data_bus()
        
        # Internal state
        self._is_initialized = False
        self._pending_publications: List[Dict[str, Any]] = []
        
        logger.debug(f"Data bus enabled tab created: {tab_id} ({tab_type})")

    def _connect_to_data_bus(self) -> None:
        """Connect to the global data bus."""
        try:
            self.data_bus = get_global_data_bus()
            
            # Register with data bus
            success = self.data_bus.register_tab(
                tab_id=self.tab_id,
                tab_type=self.tab_type,
                callback=self._handle_data_received
            )
            
            if success:
                # Connect to bus signals
                self.data_bus.signals.transmission_error.connect(self._handle_bus_error)
                logger.info(f"Tab {self.tab_id} connected to data bus")
            else:
                logger.error(f"Failed to register tab {self.tab_id} with data bus")
                
        except Exception as e:
            logger.error(f"Error connecting tab {self.tab_id} to data bus: {e}")
            self.data_bus = None

    def _handle_data_received(self, message: DataPayload) -> None:
        """Handle data received from data bus."""
        try:
            logger.debug(f"Tab {self.tab_id} received data: {message['data_type']}")
            
            # Emit signal for UI handling
            self.data_received.emit(message)
            
            # Call overrideable method for custom handling
            self.on_data_received(message)
            
        except Exception as e:
            logger.error(f"Error handling received data in tab {self.tab_id}: {e}")
            self.bus_error.emit(str(e))

    def _handle_bus_error(self, tab_id: str, error_message: str) -> None:
        """Handle data bus errors."""
        if tab_id == self.tab_id:
            logger.error(f"Data bus error for tab {self.tab_id}: {error_message}")
            self.bus_error.emit(error_message)

    def subscribe_to_data_type(self, data_type: str) -> bool:
        """
        Subscribe to receive data of a specific type.
        
        Args:
            data_type: Type of data to subscribe to
            
        Returns:
            True if subscription successful, False otherwise
        """
        if not self.data_bus:
            logger.error(f"Tab {self.tab_id}: Cannot subscribe, no data bus connection")
            return False
        
        success = self.data_bus.subscribe_to_data_type(self.tab_id, data_type)
        
        if success and data_type not in self.subscriptions:
            self.subscriptions.append(data_type)
            logger.debug(f"Tab {self.tab_id} subscribed to: {data_type}")
        
        return success

    def unsubscribe_from_data_type(self, data_type: str) -> bool:
        """
        Unsubscribe from receiving data of a specific type.
        
        Args:
            data_type: Type of data to unsubscribe from
            
        Returns:
            True if unsubscription successful, False otherwise
        """
        if not self.data_bus:
            return False
        
        success = self.data_bus.unsubscribe_from_data_type(self.tab_id, data_type)
        
        if success and data_type in self.subscriptions:
            self.subscriptions.remove(data_type)
            logger.debug(f"Tab {self.tab_id} unsubscribed from: {data_type}")
        
        return success

    def publish_data(
        self, 
        data_type: str, 
        data: TabData, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish data to the data bus.
        
        Args:
            data_type: Type of data being published
            data: The actual data payload
            metadata: Optional metadata about the data
            
        Returns:
            True if publication successful, False otherwise
        """
        if not self.data_bus:
            logger.error(f"Tab {self.tab_id}: Cannot publish, no data bus connection")
            
            # Store for later if not initialized yet
            if not self._is_initialized:
                self._pending_publications.append({
                    "data_type": data_type,
                    "data": data,
                    "metadata": metadata
                })
            
            return False
        
        success = self.data_bus.publish_data(
            source_tab_id=self.tab_id,
            data_type=data_type,
            data=data,
            metadata=metadata
        )
        
        if success:
            logger.debug(f"Tab {self.tab_id} published data: {data_type}")
            self.data_published.emit(data_type, {
                "data_type": data_type,
                "data": data,
                "metadata": metadata or {}
            })
        
        return success

    def get_subscriptions(self) -> List[str]:
        """Get list of current data type subscriptions."""
        return self.subscriptions.copy()

    def is_connected_to_bus(self) -> bool:
        """Check if tab is connected to data bus."""
        return self.data_bus is not None and self.data_bus.is_active

    def get_bus_statistics(self) -> Optional[Dict[str, Any]]:
        """Get data bus statistics."""
        if self.data_bus:
            return self.data_bus.get_bus_statistics()
        return None

    def _process_pending_publications(self) -> None:
        """Process any publications that were queued before initialization."""
        if not self._pending_publications:
            return
        
        logger.info(f"Tab {self.tab_id}: Processing {len(self._pending_publications)} pending publications")
        
        for pub in self._pending_publications:
            self.publish_data(
                data_type=pub["data_type"],
                data=pub["data"],
                metadata=pub["metadata"]
            )
        
        self._pending_publications.clear()

    def finalize_initialization(self) -> None:
        """
        Call this after tab initialization is complete.
        
        This will process any pending data publications and mark the tab as ready.
        """
        self._is_initialized = True
        self._process_pending_publications()
        
        logger.debug(f"Tab {self.tab_id} initialization finalized")

    def closeEvent(self, event) -> None:
        """Handle tab close event."""
        self._disconnect_from_data_bus()
        super().closeEvent(event)

    def _disconnect_from_data_bus(self) -> None:
        """Disconnect from data bus on tab close."""
        if self.data_bus:
            try:
                # Unregister from data bus
                self.data_bus.unregister_tab(self.tab_id)
                
                # Disconnect signals
                self.data_bus.signals.transmission_error.disconnect(self._handle_bus_error)
                
                logger.info(f"Tab {self.tab_id} disconnected from data bus")
                
            except Exception as e:
                logger.error(f"Error disconnecting tab {self.tab_id} from data bus: {e}")
            
            finally:
                self.data_bus = None
                self.subscriptions.clear()

    # Virtual methods for subclasses to override
    
    def on_data_received(self, message: DataPayload) -> None:
        """
        Handle received data (override in subclasses).
        
        Args:
            message: The received data message
        """
        pass

    def get_exportable_data(self) -> Optional[TabData]:
        """
        Get data that can be exported to other tabs (override in subclasses).
        
        Returns:
            Data suitable for publishing, or None if no exportable data
        """
        return None

    def get_supported_data_types(self) -> List[str]:
        """
        Get list of data types this tab can handle (override in subclasses).
        
        Returns:
            List of supported data type strings
        """
        return []

    def can_receive_data_type(self, data_type: str) -> bool:
        """
        Check if tab can receive a specific data type (override in subclasses).
        
        Args:
            data_type: Type of data to check
            
        Returns:
            True if tab can handle this data type, False otherwise
        """
        return data_type in self.get_supported_data_types()

    def setup_default_subscriptions(self) -> None:
        """
        Set up default data type subscriptions (override in subclasses).
        
        This method should be called after tab initialization to establish
        default subscriptions based on the tab's functionality.
        """
        pass


class SpreadsheetTabMixin:
    """Mixin for spreadsheet-specific data bus functionality."""
    
    def get_supported_data_types(self) -> List[str]:
        """Spreadsheet tabs typically receive raw data and parameters."""
        return ["dataframe", "csv_import", "parameters"]
    
    def setup_default_subscriptions(self) -> None:
        """Set up default subscriptions for spreadsheet tabs."""
        for data_type in ["csv_import", "parameters"]:
            self.subscribe_to_data_type(data_type)


class FittingTabMixin:
    """Mixin for fitting-specific data bus functionality."""
    
    def get_supported_data_types(self) -> List[str]:
        """Fitting tabs receive data ready for curve fitting."""
        return ["fitting_data", "dataframe", "parameters"]
    
    def setup_default_subscriptions(self) -> None:
        """Set up default subscriptions for fitting tabs."""
        for data_type in ["fitting_data", "dataframe"]:
            self.subscribe_to_data_type(data_type)


class SolverTabMixin:
    """Mixin for solver-specific data bus functionality."""
    
    def get_supported_data_types(self) -> List[str]:
        """Solver tabs receive parameters and constraints."""
        return ["fitting_results", "parameters", "constraints"]
    
    def setup_default_subscriptions(self) -> None:
        """Set up default subscriptions for solver tabs."""
        for data_type in ["fitting_results", "parameters"]:
            self.subscribe_to_data_type(data_type)


class MonteCarloTabMixin:
    """Mixin for Monte Carlo simulation-specific data bus functionality."""
    
    def get_supported_data_types(self) -> List[str]:
        """Monte Carlo tabs receive parameters and models."""
        return ["parameters", "model_definition", "constraints"]
    
    def setup_default_subscriptions(self) -> None:
        """Set up default subscriptions for Monte Carlo tabs."""
        for data_type in ["parameters", "model_definition"]:
            self.subscribe_to_data_type(data_type)
