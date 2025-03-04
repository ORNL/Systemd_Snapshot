"""
unit_file_lists.py
Authors: Jason M. Carter, Mike Huettel
Date: December 2023
Version: 1.0

Licensed under the Apache License, Version 2.0 (the "License")
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contributors:
    Oak Ridge National Laboratory

Description:  This file holds all of the color presets that are used by the tool. This is where the tool
    goes to find which color mappings to use.

color sites of interest:

    - https://color.adobe.com/create/color-wheel
    - https://www.color-hex.com/color-palettes/
"""

element_fill_colors = {
        'ELEMENT' : '#c0c0c0',
        'ALIAS' : '#9f9f9f',
        'UNIT'   : '#000000',
        'DROPIN'  : '#424242',
        'COMMAND' : '#c9df8a',
        'EXECUTABLE' : '#77ab59',
        'LIBRARY' : '#2b6a97',
        'STRING'   : '#b3cbdc'
        }

basic_colors = {
        'white' : '#ffffff',
        'black' : '#000000',
        'red'   : '#ff0000',
        'blue'  : '#0000ff',
        'green' : '#00ff00',
        'yellow' : '#ffff00',
        'purple' : '#ff00ff',
        'cyan'   : '#00ffff'
        }

# color brewer dark color set
dark_colors = {
        'red' : '#cb181d',
        'purple' : '#6a51a3',
        'green' : '#238b45',
        'blue' : '#2171b5',
        'orange' : '#d94701'
        }

light_colors = {
        'red' : '#fb6a4a',
        'purple' : '#9e9ac8',
        'green' : '#74c476',
        'blue' : '#6baed6',
        'orange' : '#fd8d3c'
        }

green_colors = {
        'dark'   : '#238b45',
        'normal' : '#74c476',
        'light'  : '#bae4b3',
        'white'  : '#edf8e9',
        'gray'   : '#aaaaaa'
        }

blue_colors = {
        'dark'   : '#00008b',
        'normal' : '#6baed6',
        'light'  : '#63b8ff',
        'white'  : '#eff3ff',
        'gray'   : '#aaaaaa'
        }

red_colors = {
        'dark'   : '#cb181d',
        'normal' : '#fb6a4a',
        'light'  : '#fcae91',
        'white'  : '#fee5d9',
        'gray'   : '#aaaaaa'
        }

purple_colors = {
        'darkest': '#313178',
        'dark'   : '#4e4e94',
        'normal' : '#7474b0',
        'light'  : '#a1a1ce',
        'white'  : '#cfcfe8',
        }

orange_colors = {
        'darkest': '#633a00',
        'dark'   : '#c45f00',
        'normal' : '#ff6f00',
        'light'  : '#ffb38a',
        'white'  : '#ffd7b5',
        }