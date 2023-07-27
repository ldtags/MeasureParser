from html.parser import HTMLParser
from spellchecker import SpellChecker
import re

spell = SpellChecker()

class MyHTMLParser(HTMLParser):
    def handle_data(self, data: str) -> None:
        regex = re.compile('[^a-zA-Z]')
        spell.word_frequency.load_words(['IWF', 'IMEF', 'kWh', 'MEF', 'high-efficiency'])
        strings: list[str] = data.split(' ')
        for string in strings:
            correct: str = spell.correction(string)
            if string != correct:
                string = regex.sub('', string)
                correct = spell.correction(string)
            print(string, '-', correct)
        
parser = MyHTMLParser()
parser.feed("<p style=\"margin-left:0in; margin-right:0in\"><span><span>This measure pertains to ENERGY STAR</span></span>\u00ae<span><span>-certified </span></span>clothes washers in residential buildings<span><span>. </span></span>A significant amount of the energy used for clothes washing is used for heating the water. Horizontal-axis (front loading) clothes washers tumble clothes through a smaller pool of water than conventional vertical-axis (top loading) models, saving up to 50% of energy consumed in the washing process. High-efficiency machines also have more efficient motors that spin clothes two to three times faster than the conventional machines. Thus, more water is removed from the clothes, which reduces the energy required to dry them.</p>\n<p style=\"margin-left:0in; margin-right:0in\"><span><span>The following terms are useful to understand the ENERGY STAR\u00a0</span></span><span><span>clothes washer measure:</span></span></p>\n<ul>\n<li><span><span><span><span><span>The <strong>capacity</strong> is the entire volume measured in cubic feet which a dry-clothes load could occupy within the clothes container during washer operation.</span></span></span></span></span></li>\n<li><span><span><span><span><span>The <strong>energy consumption per cycle</strong> is equal to the sum of the washing machine electrical energy consumption, the hot water heater energy consumption, and the dryer energy consumption.</span></span></span></span></span></li>\n<li><span><span><span><span><span>The <strong>integrated</strong> <strong>modified energy factor (IMEF)</strong> and <strong>modified energy factor (MEF)</strong> indicate how many cubic feet of laundry can be washed and dried with one (1) kWh of electricity. The higher the number, the greater the efficiency. The efficiency requirements for residential clothes washer models are based upon IMEF.</span></span></span></span></span></li>\n<li><span><span><span><span><span>The <strong>integrated</strong> <strong>water factor (IWF)</strong> is the number of gallons needed for each cubic foot of capacity. A lower number indicates lower water consumption and therefore represents more efficient use of the water.</span></span></span></span></span></li>\n</ul>")
