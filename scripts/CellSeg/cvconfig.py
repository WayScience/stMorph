
from src import cvutils
from PIL import Image
import pandas as pd
import skimage
import os

class CVConfig:
    '''
    Define your constants below.

    IS_CODEX_OUTPUT - CODEX output files have special filenames that allow outputs to contain more metadata about absolute positions, regs, and other things. Set this parameter to False if not using the filename convention, otherwise set it to True. Follow the naming convention in the install/run page on the CellVision website to output this metadata for non-CODEX images.
    SHOULD_COMPENSATE - (True/False) include lateral bleed compensation (Goltsev et al 2018) after single cell marker quantification (default is True)
    target - (string) path to directory containing image folder and channels file
    self.output_path_name - (string) name of directory to save output in. If directory does not exist, CellVision creates directory. (default value is 'output')
    DIRECTORY_PATH - (string) directory that contains your .tif bestFocus images (usually the bestFocus folder)
    CHANNEL_PATH - (string) path to your channels file (usually named channelNames.txt). Only used for tif images with more than 3 channels, or 4D TIF images.
    NUCLEAR_CHANNEL_NAME - (string) name of nuclear stain (corresponding to channelNames.txt).  Case sensitive.  Only used for tif images with more than 3 channels, or 4D TIF images.
    GROWTH_PIXELS - (int) number of pixels from which to grow out from the nucleus to define a cell boundary.  Change based on tissue types (default value is 1).
    GROWTH_METHOD - ('Standard'/'Sequential') - choose how you want to grow masks, see docs for descriptions of each growth algorithm. Only used if GROWTH_PIXELS is nonzero.
    
    OUTPUT_METHOD- how segmented data will be output, options are: (imagej_text_file, statistics, visual_image_output, visual_overlay_output, all), (default value is 'all')
    
    BOOST - (double or 'auto') multiplier with which to boost the pixels of the nuclear stain before inference.  Choose 'auto' to try to infer the best boost to use based off of AUTOBOOST_PERCENTILE (default value is 'auto')
    AUTOBOOST_REFERENCE_IMAGE - (string) If autoboosting, then set this to the image's filename to choose which image to autoboost off of (generally choose a non-empty image).  If image is not found or if it is empty, then the program uses first loaded image to autoboost. Parameter not used if BOOST is not set to 'auto', but gets metadata from selected image.
    
    OVERLAP (int) - amount of pixels overlap with which to run the stitching algorithm. Must be divisible by 2 and should be greater than expected average cell diameter in pixels (default value is 80).
    THRESHOLD - (int) minimum size (in pixels) of kept segmented instances. Objects smaller than THRESHOLD are not included in final segmentation output (default value is 20).
    INCREASE_FACTOR - (double) Amount with which to boost the size of the image. Default is 2.5x, decided by visual inspection after training on the Kaggle dataset (default value is 2.5).
    AUTOBOOST_PERCENTILE - (double) The percentile value with which to saturate to (default value is 99.98).
    FILENAME_ENDS_TO_EXCLUDE - (string tuple) The suffixes of files in DIRECTORY_PATH to exclude from segmentation (default is (montage.tif))
    
    MODEL_DIRECTORY - (string) path to save logs to
    MODEL_PATH - (string) path that contains your .h5 saved weights file for the model
    
    ---------OUTPUT PATHS-------------
    IMAGEJ_OUTPUT_PATH - path to output imagej .txt files
    QUANTIFICATION_OUTPUT_PATH - path to output .csv and .fcs quantifications
    VISUAL_OUTPUT_PATH - path to output visual masks as pngs.
    PROGRESS_TABLE_PATH - path to intermediate progress txt file in case run crashes
    
    Note:  Unfortunately, ImageJ provides no way to export to the .roi file format needed to import into ImageJ.  Additionally, we can't use numpy in ImageJ scripts.  Thus, we need to write to file and read in (using the included imagej.py script) using the ImageJ scripter if we pick output to imagej_text_file
    '''


    def __init__(self, target):
        self.target = target
        self.IS_CODEX_OUTPUT = False
        self.SHOULD_COMPENSATE = False
        self.output_path_name = os.path.join(target, 'output')
        self.DIRECTORY_PATH = os.path.join(target, 'tiles')
        self.CHANNEL_PATH = os.path.join(target, 'channelNames.txt')
        self.NUCLEAR_CHANNEL_NAME = 'DAPI'
        self.GROWTH_PIXELS = 2
        self.GROWTH_METHOD = 'Standard'
        self.OUTPUT_METHOD = "statistics"
        self.BOOST = 0.5
        self.AUTOBOOST_REFERENCE_IMAGE = 'none' #ie 'cellimage1.tif'
        self.FILENAME_ENDS_TO_EXCLUDE = 'none'

        self.OVERLAP = 80
        self.THRESHOLD = 20
        self.INCREASE_FACTOR = 2.5
        self.AUTOBOOST_PERCENTILE = 99.98
        self.root = os.path.dirname(os.path.realpath(__file__))
        self.MODEL_PATH = os.path.join(self.root,"src/modelFiles/final_weights.h5")
        self.IMAGEJ_OUTPUT_PATH = os.path.join(self.output_path_name, 'imagej_files')
        self.QUANTIFICATION_OUTPUT_PATH = os.path.join(self.output_path_name,'quantifications')
        self.VISUAL_OUTPUT_PATH = os.path.join(self.output_path_name,'visual_output')
        self.PROGRESS_TABLE_PATH = os.path.join(self.output_path_name,'progress_table.txt')
        try:
            os.makedirs(self.IMAGEJ_OUTPUT_PATH)
            os.makedirs(self.QUANTIFICATION_OUTPUT_PATH)
            os.makedirs(self.VISUAL_OUTPUT_PATH)
        except FileExistsError:
            print("Directory already exists")

        self.CHANNEL_NAMES = pd.read_csv(
            self.CHANNEL_PATH, sep='\t', header=None).values[:, 0]

        VALID_IMAGE_EXTENSIONS = ('tif', 'jpg', 'png')
        self.FILENAMES = [f for f in os.listdir(self.DIRECTORY_PATH) if f.endswith(
            VALID_IMAGE_EXTENSIONS) and not f.startswith('.') and not f.endswith(self.FILENAME_ENDS_TO_EXCLUDE)]
        if len(self.FILENAMES) < 1:
            raise NameError(
                'No image files found.  Make sure you are pointing to the right directory')
        
        reference_image_path = os.path.join(self.DIRECTORY_PATH, self.FILENAMES[0])

        if self.AUTOBOOST_REFERENCE_IMAGE != '' and self.BOOST == 'auto':
            if self.AUTOBOOST_REFERENCE_IMAGE in self.FILENAMES:
                self.FILENAMES.remove(self.AUTOBOOST_REFERENCE_IMAGE)
                self.FILENAMES.insert(0, self.AUTOBOOST_REFERENCE_IMAGE)
                print('Using autoboost reference image with filename', self.AUTOBOOST_REFERENCE_IMAGE)
            else:
                print('AUTOBOOST_REFERENCE_IMAGE does not exist.  Check your config file - image filename must match exactly.')
                print('Defaulting to first image reference...')

        self.N_DIMS, self.EXT, self.DTYPE, self.SHAPE, self.READ_METHOD = cvutils.meta_from_image(reference_image_path)
        self.PROGRESS_TABLE = []
        if(os.path.exists(self.PROGRESS_TABLE_PATH)):
            self.PROGRESS_TABLE = [line.rstrip('\n') for line in open(self.PROGRESS_TABLE_PATH)]
