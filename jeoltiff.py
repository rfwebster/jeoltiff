'''jeoltiff.py
:Description:
Handling tif files from JEOL Analysis Centre software

:Notes:
Not (quite) stable yet, but stable enough.
'''

__all__ = ['JeolTiff']
__author__ = 'Richard F Webster'
__version__ = '0.5'

import csv
import os
from tkinter import Tk
from tkinter.filedialog import askdirectory
import tifffile as tif
import untangle


class JeolTiff:
    ''' Class to handle opening of JEOL analytical center tifs and extract metadata contained '''
    type = 'JEOL Tiff'

    def __init__(self, fname):
        self.filename = fname
        self.isJEOL = False

        # image data in numpy array
        self.image = tif.imread(self.filename)

        self.open()

        # metadata dictionary
        self.meta = {
            'filename': '-',
            'Microscope': 'JEOL F200 S/TEM',
            'Accelerating Voltage': 1,
            'Emission Current': 1,
            'Operation Mode': '-',
            'Spot Size': 1,
            'Convergence Angle': 1,
            'Mode': '-',
            'Magnification': 0,
            'Camera Length': 0,
            'Defocus': 0,

            'Detector': '-',
            'Image size (x,y)': [0, 0],
            'Dwell Time (time, units)': [0, 'usec'],

            'lengthperpix': 1.0,
            'units': '-',
            'sunitname': '-',
            'lunitname': '-',
            'mode': '-',
            'CL': '-',
        }
        self.getmetadata()
        self.savemetadata()

    def open(self):
        pass

    def close(self):
        pass

    # Camera Length look up dictionary
    # calibrated lengths/pix 05/04/2019
    def diffperpix(self, x):
        ''' Dictionary to store diffraction clibrations  per camera length in 1/nm  per pixel,
        calibrated on 26 Nov 2019 on F200 at UNSW'''
        return {
            60:     0.082754,
            80:     0.065317,
            100:    0.05309,
            120:    0.048331761,
            150:    0.038973972,
            200:    0.02932452,
            250:    0.023499929,
            300:    0.020080653,
            400:    0.012014567,
            500:    0.011834089,
            600:    0.01003106,
            800:    0.007320717,
            1000:   0.005923978,
            1200:   0.0049947157,
            1500:   0.003636,
            2000:   0.002787,
        }[x]

    def getmetadata(self):
        ''' Function to get xml from JEOL tif and add as Gatan type (ImageJ and Digital Micrograph readable) of TIFF tags
        metadata to extract: and save in the dictionary.


        '''
        raw_xml = ''
        # Opens File and gets tag information
        with tif.TiffFile(self.filename) as tiff:
            for page in tiff.pages:
                for tag in page.tags.values():
                    # print(tag.name, tag.value)
                    if tag.name == 'ImageDescription' and tag.value[:13] == '<TemReporter2':
                        # Get the JEOL xml data (its in byte format)
                        raw_xml = tag.value
        try:  # only do files with valid xml i.e. the JEOL files
            # could add extra step to ake sure that the xml is the right xml, i.e. TemReporter2 as the first
            # saves xml data into textfile and decodes it from bytes to a UTF8 string
            # actual file is needed for untangle
            xml_filename = '{}.xml'.format(self.filename)
            with open(xml_filename, 'w', encoding='utf-8') as xml_file:
                xml_file.write(raw_xml)



            xml = untangle.parse(xml_filename)
            # Delete xml file just created
            self.isJEOL = True

        except:
            print('Not a JEOL TIFF')
            self.isJEOL = False

        if self.isJEOL:            
            self.meta['filename'] = self.filename
            
            self.meta['mode'] = str(xml.TemReporter2.MeasurementReporter.a_MeasurementUnitType.cdata)
            self.meta['lengthperpix'] = float(
                xml.TemReporter2.MeasurementReporter.a_MeasureLengthPerPixelReporter.a_LengthPerPixel.cdata)
            self.meta['Camera Length'] = int(xml.TemReporter2.MeasurementReporter.a_SelectorValue.cdata)
            self.meta['CL'] = int(xml.TemReporter2.MeasurementReporter.a_SelectorValue.cdata)
            self.meta['Defocus'] = str(xml.TemReporter2.ObservationReporter.a_EOSReporter.b_DefocusString.cdata)
            self.meta['Convergence Angle'] = str(xml.TemReporter2.ObservationReporter.a_EOSReporter.b_ConvergenceAngleAlphaNumter.cdata)
            self.meta['Spot Size'] = str(xml.TemReporter2.ObservationReporter.a_EOSReporter.b_SpotSizeString.cdata)
            self.meta['Emission Current'] = float(xml.TemReporter2.ObservationReporter.a_HTReporter.b_EmissionCurrent.cdata)
            self.meta['Mode'] = str(xml.TemReporter2.ObservationReporter.a_EOSReporter.b_OperationMode.cdata)
            self.meta['Detector'] = str(xml.TemReporter2.ObservationReporter.a_DetectorReporter.b_DetectorKind.cdata)
            self.meta['Dwell Time (time, units)'] = [float(xml.TemReporter2.ObservationReporter.a_ScanGeneratorReporter.a_ExposureTimeValue.cdata), 'usec']

            # for nm images doesn't work for STEM images?
            if self.meta['mode'] == 'UnitType_Scanning' or self.meta['mode'] == 'UnitType_Length':
                self.meta['sunitname'] = 'nm'
                self.meta['lunitname'] = 'nanometer'
                self.meta['units'] = 'nm'
            # for diffraction patterns
            elif self.meta['mode'] == 'UnitType_Diffraction':
                self.meta['sunitname'] = '1/nm'
                self.meta['lunitname'] = '1/nanometer'
                self.meta['units'] = '1/nm'
                self.meta['lengthperpix'] = self.diffperpix(self.meta['CL'])

            else:
                print('Wrong _mode_ investigate {}'.format(self.filename))
    
            # image size
            self.meta['Image size (x,y)'] = [int(xml.TemReporter2.ImageDataInformation.a_ImageSize.b_width.cdata),
                                             int(xml.TemReporter2.ImageDataInformation.a_ImageSize.b_height.cdata)]
    
            # microscope operation conditions
            self.meta['Accelerating Voltage'] = int(xml.TemReporter2.MeasurementReporter.a_AccVoltage.cdata)
            self.meta['Magnification'] = int(xml.TemReporter2.MeasurementReporter.a_SelectorValue.cdata)
            


            



        os.remove(xml_filename)

    def savemetadata(self):
        '''
        saves metadata dictionary to a csv file
        :return nothing
        '''
        w = csv.writer(open("{}.csv".format(self.filename), "w"))
        for key, val in self.meta.items():
            w.writerow([key, val])

    def savewithtags(self):
        '''saves tif files with the meta data readable by ImageJ and Gatan Digital Micrograph'''
        if self.isJEOL:
            # save these tags for Digital micrograph to read scale correctly
            tags = [(65003, 's', 3, self.meta['sunitname'], False),
                    (65004, 's', 3, self.meta['sunitname'], False),
                    (65009, 'd', 1, self.meta['lengthperpix'], False),
                    (65010, 'd', 1, self.meta['lengthperpix'], False),
                    (65012, 's', 10, self.meta['lunitname'], False),
                    (65013, 's', 10, self.meta['lunitname'], False)]

            with tif.TiffWriter('{}_{}.tif'.format(self.filename[:-4], 'dm'),
                                imagej=True) as tiff:
                tiff.save(self.image,
                          resolution=(float(1 / self.meta['lengthperpix']), float(1 / self.meta['lengthperpix'])),
                          extratags=tags, metadata={'unit': self.meta['sunitname']})
            os.remove(self.filename)


# Main function of the script
if __name__ == '__main__':
    Tk().withdraw()
    # Open Sesame
    try:
        directory = askdirectory()
    except NotADirectoryError:
        print('no folder found')
    os.chdir(directory)

    if len(directory) > 0:
        print('You chose {}'.format(directory))

    print(os.getcwd())
    print(os.listdir(os.getcwd()))

    for file in os.listdir(os.getcwd()):
        if os.path.isdir(file):
            continue
        else:
            print(file)
            filen = os.path.splitext(file)
            if filen[-1] == ('.tif' or '.tiff'):  # only do TIFF files
                tiff = JeolTiff('{}/{}'.format(directory, file))
                tiff.savewithtags()
