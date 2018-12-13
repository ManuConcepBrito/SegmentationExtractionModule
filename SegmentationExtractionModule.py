import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from DICOMLib import DICOMUtils
import logging
import numpy as np
import sys

#
# SegmentationExtractionModule
#

class SegmentationExtractionModule(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Segmentation Extraction Module" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["Manuel Concepcion (BIIG UC3M)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# SegmentationExtractionModuleWidget
#

class SegmentationExtractionModuleWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
"""

  def setup(self):

    ScriptedLoadableModuleWidget.setup(self)

    self.logic = SegmentationExtractionModuleLogic()

    # ------ 1. CREACION LAYOUT Y BOTONES ------

    self.layoutManager= slicer.app.layoutManager()
    self.layoutManager.setLayout(0)



    #
    # CARGAR IMAGEN
    #

    # Creacion layout
    collapsibleButtonLoad = ctk.ctkCollapsibleButton()
    collapsibleButtonLoad.text = "Load Files"
    self.layout.addWidget(collapsibleButtonLoad)
    formLayout_load = qt.QFormLayout(collapsibleButtonLoad)

    # Definir botones para cargar DICOM y crop volume

    # DICOM
    self.inputDICOM_label = qt.QLabel('DICOM Location: ')
    self.loadDICOM_button = qt.QPushButton('Search DICOM')
    self.loadDICOM_button.accessibleDescription = 'DICOM'
    self.loadDICOM_button.toolTip = "Search DICOM"
    self.loadDICOM_button.enabled = True
    formLayout_load.addRow(self.inputDICOM_label, self.loadDICOM_button)

    # Crop Volume
    self.inputCropVolume_label = qt.QLabel('Crop Volume location: ')
    self.loadCropVolume_button = qt.QPushButton('Search Crop Volume ')
    self.loadCropVolume_button.accessibleDescription = 'Volume'
    self.loadCropVolume_button.toolTip = "Search Crop Volume"
    formLayout_load.addRow(self.inputCropVolume_label, self.loadCropVolume_button)

    # # Cuadro de texto para introducir el directorio de la imagen a cargar
    # self.inputImage_label = qt.QLabel('Imagen original: ')
    # self.inputImage_textInput = qt.QLineEdit()
    # self.inputImage_textInput.text = 'C:/Slicer/Pyramid/Pyramid/Data/inputImage.png'
    # formLayout_load.addRow(self.inputImage_label, self.inputImage_textInput) # incluimos el cuadro de texto al layout

    # Boton para cargar imagen
    self.loadImagesButton = qt.QPushButton("Load Files")
    self.loadImagesButton.toolTip = "Load files"
    self.loadImagesButton.enabled = True
    formLayout_load.addRow(self.loadImagesButton) # incluimos el boton al layout


    # SEGMENTATIONS TO EXPORT

    collapsibleButtonSegmentation = ctk.ctkCollapsibleButton()
    collapsibleButtonSegmentation.text = "Segmentations to Export"
    self.layout.addWidget(collapsibleButtonSegmentation)
    formLayout_segmentation = qt.QFormLayout(collapsibleButtonSegmentation) # Layout dentro de la seccion

    # 
    # create table 
    #

    # Original Contour Names table

    # self.segmentationsTable = qt.QTableWidget(5, 1)
    # self.segmentationsTable.setHorizontalHeaderLabels([" "])
    # self.segmentationsTable.setVerticalHeaderLabels(" ")
    # newItem = qt.QTableWidgetItem(3)
    # self.segmentationsTable.setItem(1,1, newItem)
    # formLayout_segmentation.addRow(self.segmentationsTable)

    

    # call function to get names of contours
    # define lists
    self.contour_names = ['Ojo', 'medula', 'tronco', 'paciente']
    self.original_contour_list = qt.QListWidget()
    # Initiate empty list of exported contours at first (None selected)
    self.exported_contours_list = qt.QListWidget()

    # Initiate empty list of exported contours at first (None selected)
    for contour in self.contour_names:
      contour_item = qt.QListWidgetItem(contour)
      self.original_contour_list.addItem(contour_item)


    # define button layout 
    vertical_layout_buttons = qt.QVBoxLayout()

    # define forwards button
    self.move_segments_forwards_button = qt.QPushButton(">")
    self.move_segments_forwards_button.toolTip = "Copy segmentations"
    self.move_segments_forwards_button.enabled = True
    vertical_layout_buttons.addWidget(self.move_segments_forwards_button)
    vertical_layout_buttons.addStretch()
    #define backwards button. Set enable = False at the beginning
    self.move_segments_backwards_button = qt.QPushButton("<")
    self.move_segments_backwards_button.toolTip = "Eliminate segmentation from exported list"
    self.move_segments_backwards_button.enabled = True
    vertical_layout_buttons.addWidget(self.move_segments_backwards_button)
    vertical_layout_buttons.addStretch()

    # export button
    self.export_button = qt.QPushButton('Export Labelmaps')
    self.export_button.enabled = True


    #define titles
    # title_right = qt.QLabel('Original segmentation')
    # title_right.setAlignment(qt.Qt.AlignRight)
    # title_left = qt.QLabel('Segmentations to export')
    # title_left.setAlignment(qt.Qt.AlignLeft)

    # set layout
    horizontal_layout = qt.QHBoxLayout()
    horizontal_layout.addWidget(self.original_contour_list)
    horizontal_layout.addLayout(vertical_layout_buttons)
    horizontal_layout.addWidget(self.exported_contours_list)

    #formLayout_segmentation.addRow(title_right, title_left)
    formLayout_segmentation.addRow(horizontal_layout)
    formLayout_segmentation.addRow(self.export_button)




    #
    # GUARDAR IMAGEN
    #

    # Creacion Layout
    collapsibleButtonSave = ctk.ctkCollapsibleButton()
    collapsibleButtonSave.text = "Save Labelmaps"
    self.layout.addWidget(collapsibleButtonSave)
    formLayout_save = qt.QFormLayout(collapsibleButtonSave) # Layout dentro de la seccion

    # Cuadro de texto para indicar el directorio de la imagen de salida (procesada)
    self.outputImage_label = qt.QLabel('Select folder to save: ')
    self.folder_to_save = qt.QPushButton('Explore') #'C:/Slicer/Pyramid/Pyramid/Data/outputImage.png'
    formLayout_save.addRow(self.outputImage_label, self.folder_to_save) # incluimos el cuadro de texto al layout

    # Boton para guardar imagen
    self.saveImageButton = qt.QPushButton("Save labelmaps")
    self.saveImageButton.toolTip = "Save labelmaps"
    self.saveImageButton.enabled = True
    formLayout_save.addRow(self.saveImageButton) # incluimos el boton al layout

    # Incluimos un espacio en vertical
    self.layout.addStretch(1)


    # ------ 2. CONEXION BOTONES CON FUNCIONES ------

    # Conectar cada boton a una funcion
    self.loadDICOM_button.connect('clicked(bool)', self.config_dialog_dicom)
    self.loadCropVolume_button.connect('clicked(bool)', self.config_dialog_cropped_volume)
    self.loadImagesButton.connect('clicked(bool)', self.onLoadImageButton)
    self.move_segments_forwards_button.connect('clicked(bool)', self.move_segments_forwards)
    self.move_segments_backwards_button.connect('clicked(bool)', self.move_segments_backwards)
    # self.redChannelButton.connect('clicked(bool)', self.onRedChannelButton) # al pulsar el boton se llama a la funcion onRedChannelButton
    # self.greenChannelButton.connect('clicked(bool)', self.onGreenChannelButton) # al pulsar el boton se llama a la funcion onGreenChannelButton
    # self.blueChannelButton.connect('clicked(bool)', self.onBlueChannelButton) # al pulsar el boton se llama a la funcion onBlueChannelButton
    # self.changeRangeButton.connect('clicked(bool)', self.onChangeRangeButton) # al pulsar el boton se llama a la funcion onChangeRangeButton
    # self.showImageStatisticsButton.connect('clicked(bool)', self.onShowImageStatisticsButton) # al pulsar el boton se llama a la funcion onShowImageStatisticsButton
    # self.saveImageButton.connect('clicked(bool)', self.onSaveImageButton) # al pulsar el boton se llama a la funcion onShowImageStatisticsButton
    # self.grayValueSliderWidget.connect('valuesChanged(double,double)', self.onDoubleSliderChanged) # al cambiar los valores de la Slider se llama a la funcion onDoubleSliderChanged



  def move_segments_forwards(self):

    try:
      selected_item = self.original_contour_list.selectedIndexes()[0].row()

      self.exported_contours_list.addItem(
        self.original_contour_list.takeItem(selected_item)
        )
    except IndexError:
      pass


  def move_segments_backwards(self):
    try:
      selected_item = self.exported_contours_list.selectedIndexes()[0].row()
      self.original_contour_list.addItem(
        self.exported_contours_list.takeItem(selected_item)
        )
    except IndexError:
      pass


  def config_dialog_dicom(self):
     self.open_dialog(self.loadDICOM_button)


  def config_dialog_cropped_volume(self):
     self.open_dialog(self.loadCropVolume_button)


  def open_dialog(self, button):

    if 'DICOM' in button.accessibleDescription:
      path = str(qt.QFileDialog().getExistingDirectory())
    if 'Volume' in button.accessibleDescription:
      path = str(qt.QFileDialog().getOpenFileName())
    path = path.replace('\\', '/')
    print(path)

    if path:
      # modify text of button to show path
      self.modify_button(button, path)
      # store file location
      self.logic.update_locations({button.accessibleDescription: path})



  def modify_button(self, button, new_text):
    button.setText(new_text)


  def onLoadImageButton(self):

    # cargamos la imagen en Slicer
    self.logic.loadVolumes()


  def onRedChannelButton(self):

    print 'Visualizar canal rojo'

    # llamamos a la funcion que nos permite elegir el canal
    self.logic.verCanal(0)


  def onGreenChannelButton(self):

    print 'Visualizar canal verde'

    # llamamos a la funcion que nos permite elegir el canal
    self.logic.verCanal(1)


  def onBlueChannelButton(self):

    print 'Visualizar canal azul'

    # llamamos a la funcion que nos permite elegir el canal
    self.logic.verCanal(2)


  def onDoubleSliderChanged(self):

    # actualizamos los valores que se muestran a los lados de la slider en la interfaz
    self.minRangeText.setText(int(self.grayValueSliderWidget.minimumValue))
    self.maxRangeText.setText(int(self.grayValueSliderWidget.maximumValue))


  def onChangeRangeButton(self):

    # llamamos a la funcion para cambiar el rango, pasandole los valores minimo y maximo como parametros
    self.logic.cambioRango(self.grayValueSliderWidget.minimumValue,self.grayValueSliderWidget.maximumValue)


  def onSaveImageButton(self):

    print 'Guardar imagen'

    # cogemos el directorio de salida de la imagen
    outputImageDir = self.outputImage_textInput.text
    print "Directorio imagen de salida: ", outputImageDir

    # guardamos la imagen procesada
    self.logic.guardarImagen(self.inputImageName,outputImageDir)



  def setCustomLayouts(self):
      layoutLogic = self.layoutManager.layoutLogic()
      customLayout = ("<layout type=\"horizontal\" split=\"true\">"
      " <item>"
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"ImageDisplay\">"
      "   <property name=\"orientation\" action=\"default\">Axial</property>"
      "   <property name=\"viewlabel\" action=\"default\">DISPLAY</property>"
      "   <property name=\"viewcolor\" action=\"default\">#F34A33</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <view class=\"vtkMRMLTableViewNode\" singletontag=\"TableView1\">"
      "  <property name=\"viewlabel\" action=\"default\">T</property>"
      "  </view>"
      " </item>"
      "</layout>")

      self.customLayoutId=996
      layoutLogic.GetLayoutNode().AddLayoutDescription(self.customLayoutId, customLayout)

  def onShowImageStatisticsButton(self):
  
    # Calcular estadisticas imagen
    stats = self.logic.calcularEstadisticasImagen()
    
    # Incluir valores en tabal
    self.logic.incluirFilaEnTabla(stats)


#
# PYRAMID LOGIC: Definicion de la logica del modulo









    

#
# SegmentationExtractionModuleLogic
#

class SegmentationExtractionModuleLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self):
    self.locations_dict = dict()


  def update_locations(self, new_element):
    self.locations_dict.update(new_element)

  def loadVolumes(self):
    # clear scene at start
    self.clear_scene()
    self.load_DICOM()
    self.load_crop_volume()


  def load_DICOM(self):
    # create temporary database. Save original database path to restore 
    # it when finished 
    self.original_db_path = DICOMUtils.openTemporaryDatabase()
    #assert temporary database is open

    # import DICOM to database
    DICOMUtils.importDicom(self.locations_dict['DICOM'], slicer.dicomDatabase)

    # get patient name
    patient_name = slicer.dicomDatabase.nameForPatient(
      slicer.dicomDatabase.patients()[0]
      )

    # open DICOM by name
    DICOMUtils.loadPatientByName(patient_name)
    slicer.util.selectModule('SegmentationExtractionModule')




  def load_crop_volume(self):
    [sucess, loadedVolumeNode] = slicer.util.loadVolume(self.locations_dict['Volume'],
      returnNode=True)


  def close_database(self):
    DICOMUtils.close_database(self.original_db_path)

  def clear_scene(self):
    slicer.mrmlScene.Clear(0)



  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qimage = ctk.ctkWidgetsUtils.grabWidget(widget)
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('SegmentationExtractionModuleTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True


class SegmentationExtractionModuleTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SegmentationExtractionModule1()

  def test_SegmentationExtractionModule1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = SegmentationExtractionModuleLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
