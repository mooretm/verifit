import pandas as pd
import xml.etree.ElementTree as ET


LEVELS = ['soft50', 'soft55', 'avg60', 'avg65', 'avg70', 'loud75', 'loud80']
test_type = 'rear'

tree = ET.parse('./P0136_BestFit.xml')
root = tree.getroot()

# Get 12th octave freqs
freqs = root.find("./test[@name='frequencies']/data[@name='12ths']").text
freqs = freqs.split()
freqs_12oct = [int(float(freq)) for freq in freqs]

# Get audiometric freqs
freqs = root.find("./test[@name='frequencies']/data[@name='audiometric']").text
freqs = freqs.split()[:-2]
freqs_audio = [int(float(freq)) for freq in freqs]


#################
# Measured SPLs #
#################
# Hold measured SPL values
spl_dict = {}
# Hold target SPL values
target_dict = {}
# Match target test number with stim_level
key_dict = {}

sides = ['left', 'right']
# Speech Signal
for item in LEVELS:
    for side in sides:
        try:
            # Get spl values as list
            vals = root.find(f"./test[@side='{side}']/data[@stim_level='{item}']").text
            spl_dict[side + item[-2:]] = vals.split()

            # Get speech test number (to match to target test number)
            for num in [1,2,3,4]:
                if vals == root.find(f"./test[@side='{side}']/data[@internal='map_{test_type}spl{num}']").text:
                    key_dict[item] = f'map_{test_type}_targetspl{str(num)}'

        except AttributeError as e:
            pass
            #print(f"No data for {side + item[-2:]}")

# MPO
for side in sides:
    try:
        vals = root.find(f"./test[@side='{side}']/data[@stim_type='mpo']").text
        spl_dict[side + 'mpo'] = vals.split()
    except AttributeError as e:
        print(f"No data for {side} MPO")

df = pd.DataFrame(spl_dict)
df.insert(loc=0, column='frequency', value=freqs_12oct)
spls = df[df['frequency'].isin(freqs_audio)]
spls.reset_index(drop=True, inplace=True)
print(f'\nMeasured SPLs')
print(spls)


###########
# Targets #
###########
# Speech targets
for key, value in key_dict.items():
    for side in sides:
        try:
            vals = root.find(f"./test[@side='{side}']/data[@internal='{value}']").text
            target_dict[side + key[-2:]] = vals.split()[:-2]
        except AttributeError as e:
            print(f"No data for {key, '->', value}")

targets = pd.DataFrame(target_dict)
targets.insert(loc=0, column='frequency', value=freqs_audio)
targets.apply(pd.to_numeric, errors='ignore')
print(f'\nTarget Values')
print(targets)

# Note: No targets for MPO, but there are UCL data. Not pulled because
# I was told we never use it.
