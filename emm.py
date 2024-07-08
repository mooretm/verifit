from models import verifitmodel
import xml.etree.ElementTree as ET
from matplotlib import pyplot as plt


fpath = './P0888_BestFit.xml'
#fpath = r'C:\Users\MooTra\OneDrive - Starkey\Documents\Projects\EM Music\EdgeModeMusic\LT_EMM_Music_2024_04_03.xml'
tree = ET.parse(fpath)
root = tree.getroot()


""" Other things to test for:
        -stim_type
        -mpo

    Other options:
        -rear/testbox
        -plots
"""

def parse(side, test_num):
    """ Return values from Verifit XML for the 
        supplied arguments.
    """
    for val in root.iter('test'):
        try:
            if val.attrib['side'] == side:
                for child in val.iter('data'):
                    if child.attrib['name'] == f'test{test_num}_on-ear' \
                    and child.attrib['yunit'] == 'dBspl' \
                    and child.attrib['internal'] == f"map_rearspl{test_num}":
                        to_list = child.text.split(" ")
                        to_numeric = [float(x) for x in to_list]
                        return to_numeric
        except:
            pass

sides = ['left', 'right']
plot_curve = []
for ii in range(1, 5):
    for side in sides:
        print(f"\nSide: {side}")
        print(f"Curve number: {ii}")
        plot_curve.append(parse(side, ii))
        print(parse(side, ii))

# Get 12th octave freqs
vals = root.find('test[@name="frequencies"]/data[@name="12ths"]').text
to_nums = vals.split(' ')
twelfs = [int(float(x)) for x in to_nums]
print(f"\n12th-octave freqs: {twelfs}")

plt.plot(plot_curve)
plt.ylim([-10, 140])
plt.xscale('log')
plt.show()


###########
# Archive #
###########
# dir = r'C:\Users\MooTra\OneDrive - Starkey\Documents\Projects\EM Music\EdgeModeMusic'
# v = verifitmodel.VerifitModel(path=dir)
# v.get_data()
# v.long_format()
# print(v.measured_long)


# fpath = r'C:\Users\MooTra\Downloads\P0089_BestFit.xml'
# tree = ET.parse(fpath)
# root = tree.getroot()


# for val in root.iter('test'):
#     try:
#         if val.attrib['side'] == 'left':
#             for child in val.iter('data'):
#                 if child.attrib['name'] == 'test1_on-ear' \
#                 and child.attrib['yunit'] == 'dBspl' \
#                 and child.attrib['internal'] == "map_rearspl1":
#                     print(child.attrib, child.text)
#                     left['test1'] = child.text

#     except:
#         pass
#     try:
#         if val.attrib['side'] == 'right':
#             for child in val.iter('data'):
#                 if child.attrib['name'] == 'test1_on-ear' \
#                 and child.attrib['yunit'] == 'dBspl' \
#                 and child.attrib['internal'] == "map_rearspl1":
#                     print(child.attrib, child.text)
#                     right['test1'] = child.text
#     except:
#         pass


# left = {}
# right = {}
# fpath = r'C:\Users\MooTra\OneDrive - Starkey\Documents\Projects\EM Music\EdgeModeMusic\LT_EMM_Music_2024_04_03.xml'
# tree = ET.parse(fpath)
# root = tree.getroot()

# for val in root.iter('test'):
#     try:
#         if val.attrib['side'] == 'left':
#             for child in val.iter('data'):
#                 if child.attrib['name'] == 'test1_on-ear' \
#                 and child.attrib['yunit'] == 'dBspl' \
#                 and child.attrib['internal'] == "map_rearspl1":
#                     print(child.attrib, child.text)
#                     left['test1'] = child.text
#     except:
#         pass

# for val in root.iter('test'):
#     try:
#         if val.attrib['side'] == 'right':
#             for child in val.iter('data'):
#                 if child.attrib['name'] == 'test1_on-ear' \
#                 and child.attrib['yunit'] == 'dBspl' \
#                 and child.attrib['internal'] == "map_rearspl1":
#                     print(child.attrib, child.text)
#                     right['test1'] = child.text
#     except:
#         pass


# def parse(side, test_num):
#     """ Return values from Verifit XML for the 
#         supplied arguments.
#     """
#     for val in root.iter('test'):
#         try:
#             if val.attrib['side'] == side:
#                 for child in val.iter('data'):
#                     if child.attrib['name'] == f'test{test_num}_on-ear' \
#                     and child.attrib['yunit'] == 'dBspl' \
#                     and child.attrib['internal'] == f"map_rearspl{test_num}":
#                         print(child.attrib, child.text)
#                         right['test1'] = child.text
#         except:
#             pass
