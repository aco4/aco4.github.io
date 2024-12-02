# pip install pandas
# pip install requests
# pip install pretty_html_table

import pandas as pd
import requests
r = requests.get('https://raw.githubusercontent.com/Warzone2100/warzone2100/master/data/mp/stats/research.json')
df = pd.DataFrame.from_dict(r.json())

r = requests.get('https://raw.githubusercontent.com/Warzone2100/warzone2100/master/data/mp/stats/structure.json')
sdf = pd.DataFrame.from_dict(r.json())

starting_technologies = [
    # Default tech
    'R-Sys-Spade1Mk1',            # Construction Unit
    'R-Vehicle-Body01',           # Light Body - Viper
    'R-Vehicle-Prop-Wheels',      # Wheeled Propulsion

    # T1 Advanced Bases
    'R-Wpn-Cannon-Damage01',      # HEAT Cannon Shells
    'R-Struc-Research-Upgrade01', # Synaptic Link Data Analysis
    'R-Wpn-Flamer-Damage02',      # High Temperature Flamer Gel Mk2
    'R-Wpn-Flamer-ROF01',         # Flamer Autoloader
    'R-Wpn-MG-Damage03',          # APDSB MG Bullets Mk2
    'R-Vehicle-Engine02',         # Fuel Injection Engine Mk2
    'R-Struc-Factory-Module',     # Factory Module
    'R-Wpn-Mortar01Lt',           # Mortar
    'R-Wpn-Rocket-Damage01',      # HE Rockets
    'R-Sys-MobileRepairTurret01', # Mobile Repair Turret
    'R-Defense-WallUpgrade02',    # Improved Hardcrete Mk2
    'R-Vehicle-Prop-Halftracks',  # Half-tracked Propulsion
    'R-Comp-CommandTurret01',     # Command Turret
    'R-Struc-Materials01',        # Reinforced Base Structure Materials
    'R-Defense-TankTrap01',       # Tank Traps
    'R-Defense-HardcreteGate',    # Hardcrete Gate
    'R-Sys-Sensor-Tower02',       # Hardened Sensor Tower
    'R-Defense-Tower01',          # Heavy Machinegun Guard Tower
    'R-Defense-Tower06',          # Mini-Rocket Tower
    'R-Defense-Pillbox01',        # Heavy Machinegun Bunker
    'R-Defense-Pillbox04',        # Light Cannon Bunker
    'R-Defense-Pillbox05',        # Flamer Bunker
    'R-Defense-WallTower02',      # Light Cannon Hardpoint
]

def zero_out(tech):
    df.loc['researchPoints', tech] = 0
    reqs = df[tech]['requiredResearch']

    if not isinstance(reqs, list): # Base case
        return

    for child in reqs:
        zero_out(child)

for tech in starting_technologies:
    zero_out(tech)

def branch(tech):
    if tech is None:
        return None

    r_points = df[tech]['researchPoints']
    reqs = df[tech]['requiredResearch']

    if not isinstance(reqs, list): # Base case
        return r_points

    max_r_points = 0

    for child in reqs: # Branch
        child_r_points = branch(child)

        if child_r_points > max_r_points:
            max_r_points = child_r_points

    return r_points + max_r_points

import math

upgrade_table = [
    {
        'technology': None,
        'rate': sdf['A0ResearchFacility']['researchPoints'],
        'module_rate': None,
        'max_rate': sdf['A0ResearchFacility']['researchPoints']
    },
    {
        'technology': 'R-Struc-Research-Module',
        'rate': sdf['A0ResearchFacility']['researchPoints']
    },
    {'technology': 'R-Struc-Research-Upgrade01'},
    {'technology': 'R-Struc-Research-Upgrade02'},
    {'technology': 'R-Struc-Research-Upgrade03'},
    {'technology': 'R-Struc-Research-Upgrade04'},
    {'technology': 'R-Struc-Research-Upgrade05'},
    {'technology': 'R-Struc-Research-Upgrade06'},
    {'technology': 'R-Struc-Research-Upgrade07'},
    {'technology': 'R-Struc-Research-Upgrade08'},
    {'technology': 'R-Struc-Research-Upgrade09'}
]

for i in range(len(upgrade_table)):
    if 'rate' not in upgrade_table[i]:
        percentIncrease = df[upgrade_table[i]['technology']]['results'][0]['value'] / 100
        extra = math.ceil(sdf['A0ResearchFacility']['researchPoints'] * percentIncrease)
        upgrade_table[i]['rate'] = upgrade_table[i-1]['rate'] + extra

    if 'module_rate' not in upgrade_table[i]:
        upgrade_table[i]['module_rate'] = upgrade_table[i]['rate'] + sdf['A0ResearchFacility']['moduleResearchPoints']

    if 'max_rate' not in upgrade_table[i]:
        upgrade_table[i]['max_rate'] = max(upgrade_table[i]['rate'], upgrade_table[i]['module_rate'])

    upgrade_table[i]['inflection_point'] = branch(upgrade_table[i]['technology'])

def calc(points):
    # Identify how many upgrades we currently have, based on the starting technologies
    upgrades = 0

    for i, element in enumerate(upgrade_table[::-1]):
        if element['technology'] in starting_technologies:
            upgrades = 10 - i
            break;

    pointsDone = 0
    seconds = 0
    rate = upgrade_table[upgrades]['max_rate']

    while pointsDone < points:

        if upgrades < 10 and pointsDone > upgrade_table[upgrades + 1]['inflection_point']:
            upgrades += 1
            rate = upgrade_table[upgrades]['max_rate']

        pointsDone += rate
        seconds += 1

    return seconds

import datetime

def format_time(s):
    hours, remainder = divmod(s, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f'{hours}:{minutes:02}:{seconds:02}'
    else:
        return f'{minutes}:{seconds:02}'

mrt = pd.DataFrame({'id': list(df.columns)})
mrt['Technology'] = mrt['id'].apply(lambda x: df[x]['name'])
mrt['Minimum Research Time'] = mrt['id'].apply(lambda x: calc(branch(x)))
mrt = mrt[mrt['Minimum Research Time'] != 0]
mrt = mrt.sort_values(by=['Minimum Research Time'])
mrt = mrt.reset_index(drop=True)
mrt = mrt.drop(columns=['id'])
mrt['Minimum Research Time'] = mrt['Minimum Research Time'].apply(lambda x: format_time(x))

# print(f'Updated on {datetime.datetime.now().astimezone().strftime("%B %d, %Y at %H:%M:%S UTC%z %Z")}')
# with pd.option_context('display.max_rows', None): display(mrt)

from pretty_html_table import build_table

html_table = build_table(mrt
                        , 'grey_dark'
                        , font_size='14px'
                        , font_family='Calibri'
                        , text_align='right'
                        , width='auto'
                        , index=True
                        , padding='5px 10px 5px 10px'
                        )

with open('Warzone2100/mrt.html', 'w') as f:
    f.write(
        '<html>\n'
        + '<head><title>Minimum Research Time</title></head>\n'
        + '<body>\n'
        + '<div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">\n'
        + '<h1>Warzone 2100 Minimum Research Time</h1>\n'
        + '<p>Start with T1 Advanced Bases</p>\n'
        + html_table
        + '\n</div></body></html>'
    )
