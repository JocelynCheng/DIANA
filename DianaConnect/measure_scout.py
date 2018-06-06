'''Measure AP and Lateral dimensions from DICOM localizer images for SSDE calculations'''

import pydicom
import logging
import numpy as np
# from matplotlib import pyplot as plt
from pprint import pformat
from sklearn.mixture import GMM
import json
import glob
import os

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Can use tag "degrees of azimuth" to identify lateral vs. AP
# 90 its a lateral scout -> PA dimension
# 0,180 its an AP scout -> lateral dimension

def MeasureScout(fp):

    # Read DICOM file and info
    # Get ref file
    dcm = pydicom.read_file(fp)

    # Load spacing values (in mm)
    pixel_spacing = (float(dcm.PixelSpacing[0]), float(dcm.PixelSpacing[1]))

    # Load study info
    patient_name = dcm.PatientName
    accession_number = dcm.AccessionNumber

    # Determine measurement dimension
    orientation = dcm.ImageOrientationPatient

    if orientation[0]*orientation[0] > 0.2:
        # This is a PA scout, which gives the lateral measurement
        measured_dim = 'lateral_dim'
    elif orientation[1]*orientation[1] > 0.2:
        # This is a lateral scout, which gives the AP measurement
        measured_dim = 'AP_dim'
    else:
        measured_dim = 'Unknown_dim'

    # Setup pixel array data
    dcm_px = np.array(dcm.pixel_array, dtype=np.float32)

    # Determine weighted threshold separating tissue/non-tissue attenuations
    # using a GMM
    thresh = np.mean(dcm_px[dcm_px>0])

    gmm = GMM(2).fit(dcm_px[dcm_px>0].reshape(-1,1))
    thresh = np.sum(gmm.weights_[::-1]*gmm.means_.ravel())

    # logging.debug(gmm.weights_[::-1])
    # logging.debug(gmm.means_.ravel())

    logging.debug("Threshold: {0}".format(thresh))

    # Compute avg width based on unmasked pixels
    mask = dcm_px > thresh

    px_counts = np.sum(mask,axis=1)
    avg_px_count = np.mean(px_counts[px_counts>0])
    # Across image spacing is 2nd component (axis 1)
    d_avg = avg_px_count * pixel_spacing[1] / 10;

    logging.debug("Average {0} width: {1}".format(measured_dim, d_avg))

    # plt.imshow(mask)
    # plt.show()

    ret = {'PatientName': patient_name,
           'AccessionNumber': accession_number,
           measured_dim:  d_avg}

    return ret


def test_measurement():

    results = {}

    fp = "./tests/data/ct_scout_01.dcm"
    ret = MeasureScout(fp)
    results[ret['AccessionNumber']] = ret

    fp = "./tests/data/ct_scout_02.dcm"
    ret = MeasureScout(fp)
    logging.debug(pformat(ret))
    results[ret['AccessionNumber']].update(ret)

    assert results == {'': {'AP_dim': 28.21344537815126,
                            'AccessionNumber': '',
                            'PatientName': 'Anonymized1',
                            'lateral_dim': 42.907881773399012}}

    return True

def measure_glob(regex, out_json):
    fns = glob.glob(regex)
    logging.debug(fns)

    results = {}
    for fp in fns:
        ret = MeasureScout(fp)

        key = ret.get("AccessionNumber")
        if not key:
            key = ret.get("PatientName")

        if not results.get(key):
            results[key] = ret
        else:
            results[key].update(ret)

    json.dump(results.values(), open(out_json, 'w'))
    logging.debug(pformat(results.values()))

def test_glob():
    regex = r"./tests/data/ct_scout*.dcm"
    out_file = "./tests/measurements.json"
    measure_glob(regex, out_file)
    with open(out_file, 'r') as f:
        output = f.read()
    res = json.loads(output)

    os.remove(out_file)

    assert(res == [{
        "AccessionNumber": "",
        "lateral_dim": 42.90788177339901,
        "AP_dim": 28.21344537815126,
        "PatientName": "Anonymized1"
        }]
    )


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_glob()

