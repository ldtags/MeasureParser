import sqlite3
from src.measure_parser.objects import Measure

class dbservice():
    def __init__(self, filepath: str):
        self.connection = sqlite3.connect(filepath)
        self.cursor = self.connection.cursor()

    def get_all_params(self, measure: Measure) -> list[str]:
        query: str = 'SELECT api_name FROM parameters WHERE criteria IN ('
        criteria: list[str] = ['REQ']

        if measure.is_DEER():
            criteria.append('DEER')

        if measure.is_GSIA_nondef():
            criteria.append('GSIA')

        if (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            criteria.append('MAT')

        if measure.is_WEN():
            criteria.append('WEN')

        if measure.is_sector_nondef():
            criteria.append('NTG')

        if measure.is_interactive():
            criteria.append('INTER')

        length: int = len(criteria)
        for i, spec in enumerate(criteria):
            query += spec
            if i != length - 1:
                query += ', '
        query += ')'

        params: list[str] = self.cursor.execute(query).fetchall()
        if (measure.is_interactive()
                and not measure.contains_param('LightingType')):
            params.remove('LightingType')

        return params
    
    
    def get_value_tables(self, measure: Measure) -> list[str]:
        query: str = 'SELECT api_name FROM tables WHERE shared = 0'
        query += ' AND criteria IN ('
        criteria: list[str] = ['REQ']

        if measure.is_DEER():
            criteria.append('DEER')

        if (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            criteria.append('MAT')
            
        if measure.contains_value_table('emergingTech'):
            criteria.append('ET')
            
        if measure.is_deemed():
            criteria.append('DEEM')
            
        if measure.is_fuel_sub():
            criteria.append('FUEL')
            
        if measure.is_interactive():
            criteria.append('INTER')
            
        length: int = len(criteria)
        for i, spec in enumerate(criteria):
            query += spec
            if i != length - 1:
                query += ', '
        query += ')'
        
        tables: list[str] = self.cursor.execute(query).fetchall()
        if (measure.is_interactive()
                and not measure.contains_value_table('IEApplicability')):
            tables.remove('IEApplicability')

        return tables
        
        
    def get_shared_tables(self, measure: Measure) -> list[str]:
        query: str = 'SELECT api_name FROM tables WHERE shared != 0'
        query += ' AND criteria IN ('
        criteria: list[str] = ['REQ']
        
        if measure.is_DEER():
            criteria.append('DEER')
            
        if measure.is_GSIA_default():
            criteria.append('GSIA-DEF')
            
        if measure.is_GSIA_nondef():
            criteria.append('GSIA')
            
        if (measure.contains_MAT_label('AR')
                or measure.contains_MAT_label('AOE')):
            criteria.append('MAT')
            
        if measure.is_WEN():
            criteria.append('WEN')
            
        if measure.is_res_default():
            criteria.append('RES-DEF')
        else:
            criteria.append('RES')
            
        if measure.is_nonres_default():
            criteria.append('RES-NDEF')
        elif 'RES' not in criteria:
            criteria.append('RES')
            
        if measure.is_interactive():
            criteria.append('INTER')
        
        length: int = len(criteria)
        for i, spec in enumerate(criteria):
            query += spec
            if i != length - 1:
                query += ', '
        query += ')'

        tables: list[str] = self.cursor.execute(query).fetchall()
        if measure.is_interactive():
            commercial: str = 'commercialInteractiveEffects'
            if not measure.contains_shared_table(commercial):
                tables.remove(commercial)
            residential: str = 'residentialInteractiveEffects'
            if not measure.contains_shared_table(residential):
                tables.remove(residential)

        return tables