# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BivariateLegend
                                 A QGIS plugin
 This plugin helps creating bivariate legends
                              -------------------
        begin                : 2016-02-25
        git sha              : $Format:%H$
        copyright            : (C) 2016 by WebGeoDataVore
        email                : thomas.gratier@webgeodatavore.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import print_function
from __future__ import absolute_import
from builtins import range
from builtins import object
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtWidgets import QAction, QGraphicsScene, QFileDialog
from PyQt5.QtGui import QIcon, QImage, QPainter, QColor, QPixmap, QTransform
# Initialize Qt resources from file resources.py
from .resources import *

# Import QGIS components
from qgis.gui import QgsMessageBar, QgsBlendModeComboBox
from qgis.core import QgsMapLayerProxyModel, QgsRenderContext, Qgis

# Import the code for the DockWidget
from .bivariate_legend_dockwidget import BivariateLegendDockWidget
import os.path

renderContext = QgsRenderContext()


class BivariateLegend(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'BivariateLegend_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Bivariate legend')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'BivariateLegend')
        self.toolbar.setObjectName(u'BivariateLegend')

        # print "** INITIALIZING BivariateLegend"

        self.pluginIsActive = False
        self.dockwidget = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('BivariateLegend', message)

    def initGui(self):  # noqa
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/BivariateLegend/icon.png'
        text = self.tr(u'&Bivariate legend')
        self.action = QAction(
            QIcon(icon_path),
            text, self.iface.mainWindow()
        )
        # connect the action to the run method
        self.action.triggered.connect(self.run)
        # Add toolbar button and menu item
        self.iface.addPluginToMenu(text, self.action)
        self.iface.addToolBarIcon(self.action)

    def onClosePlugin(self):  # noqa
        """Cleanup necessary items here when plugin dockwidget is closed."""
        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        self.iface.removePluginMenu(
            self.tr(u'&Bivariate legend'),
            self.action)
        self.iface.removeToolBarIcon(self.action)
        # remove the toolbar
        del self.toolbar

    @staticmethod
    def generate_image_for_colors(
            colors,
            width,
            height,
            square_size,
            reverse=False):
        """
        Generate intermediate legend image for one layer.

        The input are a list of QColor, the height, the width
        and reverse for color ordering (x or y)
        """
        origin_x = 0
        origin_y = 0
        w, h = width * square_size, height * square_size
        img = QImage(w + 1, h + 1, QImage.Format_ARGB32)
        # TODO: Manage border when pen color
        # img = QImage(w + 1, h + 1, QImage.Format_ARGB32)

        qp = QPainter()
        qp.begin(img)

        for index1, val1 in enumerate(colors):
            for index in range(h):

                qp.setBrush(QColor(*val1))
                qp.setPen(Qt.NoPen)

                if reverse:
                    qp.drawRect(
                        origin_x + index1 * square_size,
                        origin_y + index * square_size,
                        origin_x + (index1 + 1) * square_size,
                        origin_y + (index + 1) * square_size
                    )
                else:
                    qp.drawRect(
                        origin_x + index * square_size,
                        origin_y + index1 * square_size,
                        origin_x + (index + 1) * square_size,
                        origin_y + (index1 + 1) * square_size
                    )

        qp.end()
        return img

    @staticmethod
    def generate_border(
            width,
            height,
            square_size):
        """
        Generate intermediate legend image for one layer.

        The input are a list of QColor, the height, the width
        and reverse for color ordering (x or y)
        """
        origin_x = 0
        origin_y = 0
        w1, h1 = width * square_size, height * square_size
        img = QImage(w1 + 1, h1 + 1, QImage.Format_ARGB32)

        qp1 = QPainter()
        qp1.begin(img)

        for index1 in range(w1):
            for index in range(h1):
                qp1.setBrush(Qt.NoBrush)
                qp1.setPen(Qt.red)
                qp1.drawRect(
                    origin_x + index * square_size,
                    origin_y + index1 * square_size,
                    origin_x + (index + 1) * square_size,
                    origin_y + (index1 + 1) * square_size
                )

        qp1.end()
        return img

    @staticmethod
    def get_colors_from_layer(layer, reverse=False):
        """Extract colors from vector layer styles."""
        colors_layer = []
        symbols_layer = layer.renderer().symbols(renderContext)
        if reverse:
            symbols_layer = reversed(symbols_layer)
        for sym in symbols_layer:
            colors_layer.append([
                sym.color().red(),
                sym.color().green(),
                sym.color().blue()
            ])
        return colors_layer

    def export_legend(self):
        """Export legend to image."""
        if (self.image_output is not None):
            filename = QFileDialog(
                filter='JPG and PNG files (*.jpeg *.jpg *.png)'
            ).getSaveFileName()
            if filename and isinstance(filename, tuple):
                self.image_output.save(filename[0], 'PNG')

    def square_width_changed(self, int_val):
        """Change square size for a cell."""
        self.square_width_cell = int_val

    def update_reverse_layer_top_colors(self, state):
        """Reverse color ordering for top layer."""
        if (state == Qt.Unchecked):
            self.reverse_layer_top_colors = False
        else:
            self.reverse_layer_top_colors = True

    def update_reverse_layer_bottom_colors(self, state):
        """Reverse color ordering for bottom layer."""
        if (state == Qt.Unchecked):
            self.reverse_layer_bottom_colors = False
        else:
            self.reverse_layer_bottom_colors = True

    def update_invert_axis(self, state):
        """Update if you want to rotate axis x and y."""
        if (state == Qt.Unchecked):
            self.invert_axis = False
        else:
            self.invert_axis = True

    def assign_blend_mode(self, index):
        """Assign blend mode."""
        # See enum QPainter.CompositionMode for correspondance
        enum_composition_mode = [
            'CompositionMode_SourceOver',
            'CompositionMode_DestinationOver',
            'CompositionMode_Clear',
            'CompositionMode_Source',
            'CompositionMode_Destination',
            'CompositionMode_SourceIn',
            'CompositionMode_DestinationIn',
            'CompositionMode_SourceOut',
            'CompositionMode_DestinationOut',
            'CompositionMode_SourceAtop',
            'CompositionMode_DestinationAtop',
            'CompositionMode_Xor',
            'CompositionMode_Plus',
            'CompositionMode_Multiply',
            'CompositionMode_Screen',
            'CompositionMode_Overlay',
            'CompositionMode_Darken',
            'CompositionMode_Lighten',
            'CompositionMode_ColorDodge',
            'CompositionMode_ColorBurn',
            'CompositionMode_HardLight',
            'CompositionMode_SoftLight',
            'CompositionMode_Difference',
            'CompositionMode_Exclusion',
            'RasterOp_SourceOrDestination',
            'RasterOp_SourceAndDestination',
            'RasterOp_SourceXorDestination',
            'RasterOp_NotSourceAndNotDestination',
            'RasterOp_NotSourceOrNotDestination',
            'RasterOp_NotSourceXorDestination',
            'RasterOp_NotSource',
            'RasterOp_NotSourceAndDestination',
            'RasterOp_SourceAndNotDestination'
        ]
        self.blend_mode = getattr(
            QPainter,
            enum_composition_mode[self.blend_mode_combo_box.blendMode()]
        )
        # fix_print_with_import
        print(enum_composition_mode[self.blend_mode_combo_box.blendMode()])

    def add_blend_mode_combobox(self):
        """Add blend mode combobox."""
        self.blend_mode_combo_box = QgsBlendModeComboBox()
        # Default value
        self.blend_mode = QPainter.CompositionMode_Multiply
        self.blend_mode_combo_box.setBlendMode(self.blend_mode)
        blend_mode_combo_box = self.blend_mode_combo_box

        # Signal inherited from QComboBox
        blend_mode_combo_box.currentIndexChanged.connect(
            self.assign_blend_mode
        )
        # Dirty insertion in the existing Qt Designer generated UI
        self.dockwidget.children()[-1].children()[0].layout().insertWidget(
            1,
            self.blend_mode_combo_box
        )

    def generate_image(self):
        """Generate image."""
        l_top = self.dockwidget.map_layer_combobox_1.currentLayer()
        l_bottom = self.dockwidget.map_layer_combobox_2.currentLayer()

        # TODO: QgsRuleBasedRenderer to manage later
        # TODO: Filter based on renderer type
        if (l_top.id() != l_bottom.id()):

            colors_layer_top = self.get_colors_from_layer(
                l_top,
                self.reverse_layer_top_colors
            )
            colors_layer_bottom = self.get_colors_from_layer(
                l_bottom,
                self.reverse_layer_bottom_colors
            )

            # Set default values
            len_color_layer_top = len(colors_layer_top)
            len_color_layer_bottom = len(colors_layer_bottom)

            # Draw image on top
            img_top = self.generate_image_for_colors(
                colors_layer_top,
                len_color_layer_bottom,
                len_color_layer_top,
                self.square_width_cell,
                reverse=False
            )
            img_bottom = self.generate_image_for_colors(
                colors_layer_bottom,
                len_color_layer_bottom,
                len_color_layer_top,
                self.square_width_cell,
                reverse=True
            )

            # Create a new painter to merge images
            painter = QPainter()
            # Declare transform function to rotate axis to switch x and y
            trans = QTransform()

            # Start from first image
            painter.begin(img_top)
            # Apply blending/composition
            painter.setCompositionMode(self.blend_mode)
            # TODO: Manage border when pen color
            painter.drawImage(0, 0, img_bottom)
            painter.end()

            # Rotate if necessary
            if self.invert_axis:
                trans = QTransform()
                trans.rotate(90)
                img_top = img_top.transformed(trans)

            # Reuse end image and display it in an UI overview
            item = QPixmap.fromImage(img_top)
            scene = QGraphicsScene()
            scene.addPixmap(item)
            self.dockwidget.graphic_preview.setScene(scene)
            # Keep reference to image to ease image export
            self.image_output = img_top
        else:
            self.iface.messageBar().pushMessage(
                "Information",
                """Choose two different layers.
                Otherwise, no image overview will be generated.
                """,
                level=Qgis.Info
            )

    def run(self):
        """Run method that loads and starts the plugin."""
        if not self.pluginIsActive:
            self.pluginIsActive = True
            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = BivariateLegendDockWidget()

            # Set default square cell
            self.square_width_cell = 20
            self.dockwidget.square_width_cell.setValue(self.square_width_cell)
            # Connect to listen to square cell value from SpinBox changed
            self.dockwidget.square_width_cell.valueChanged.connect(
                self.square_width_changed
            )

            # Set default value for color ordering
            self.reverse_layer_top_colors = False
            self.reverse_layer_bottom_colors = False

            # Reverse colors order for each layer
            self.dockwidget.checkbox_layer_1.stateChanged.connect(
                self.update_reverse_layer_top_colors
            )
            self.dockwidget.checkbox_layer_2.stateChanged.connect(
                self.update_reverse_layer_bottom_colors
            )

            # Rotate to invert X and Y axis
            self.invert_axis = False
            self.dockwidget.invert_axis.stateChanged.connect(
                self.update_invert_axis
            )

            self.dockwidget.graphic_preview.setStyleSheet(
                "background-color: transparent;"
            )

            # Restrict available layers to Polygon in layers combobox
            self.dockwidget.map_layer_combobox_1.setFilters(
                QgsMapLayerProxyModel.PolygonLayer
            )
            self.dockwidget.map_layer_combobox_2.setFilters(
                QgsMapLayerProxyModel.PolygonLayer
            )

            # Add blend combobox and listen to event
            if not hasattr(self, 'blend_mode_combo_box'):
                self.add_blend_mode_combobox()

            # Connect to_generate_image
            self.dockwidget.generate_legend.clicked.connect(
                self.generate_image
            )
            # Connect to export image
            self.dockwidget.export_legend.clicked.connect(
                self.export_legend
            )

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(
                self.onClosePlugin
            )

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
