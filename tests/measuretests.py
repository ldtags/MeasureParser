import unittest as ut

from measure_parser.objects import (
    Measure,
    Parameter,
    SharedParameter,
    ValueTable,
    SharedValueTable,
    ParameterLabel,
    Column
)


class TestMeasure(ut.TestCase):
    def test_creation(self):
        measure = Measure('./resources/SWCR002.json')
        self.assertEqual(measure.owner, '')
        self.assertEqual(measure.id, 'SWCR002')
        self.assertEqual(measure.version_id, 'SWCR002-03')
        self.assertEqual(measure.name, 'Low-Temperature Display Case Doors With No Anti-Sweat Heaters')
        self.assertEqual(measure.use_category, 'CR')
        self.assertEqual(measure.pa_lead, 'SCE')
        self.assertEqual(measure.start_date, '2023-01-01')
        self.assertEqual(measure.end_date, 'None')
        self.assertEqual(measure.status, 'CPUC Approved')
        self.assertEqual(len(measure.parameters), 1)
        self.assertEqual(len(measure.shared_parameters), 30)
        self.assertEqual(len(measure.shared_tables), 4)
        self.assertEqual(len(measure.value_tables), 10)
        self.assertEqual(len(measure.calculations), 7)
        self.assertEqual(len(measure.exclusion_tables), 0)

        param: Parameter = measure.parameters[0]
        self.assertEqual(param.name, 'Description')
        self.assertEqual(param.api_name, 'Desc')
        self.assertEqual(param.labels[0].name, )
        self.assertEqual(param.description, '<p>Offering Description</p>')
        self.assertEqual(param.order, 1)
        self.assertEqual(param.reference_refs, [])

        param_label: ParameterLabel = param.labels[0]
        self.assertEqual(param_label.name, 'ASH Controls')
        self.assertEqual(param_label.api_name, 'ASH Controls')
        self.assertEqual(param_label.active, True)
        self.assertEqual(param_label.description, 'Display Case Door with ASH Controls')

        shared_param: SharedParameter = measure.shared_parameters[0]
        self.assertEqual(shared_param.order, 2)
        self.assertEqual(shared_param.version.version_string, 'MeasAppType')
        self.assertEqual(shared_param.labels, ['NR'])

        shared_table: SharedValueTable = measure.shared_tables[0]
        self.assertEqual(shared_table.order, 11)
        self.assertEqual(shared_table.version.version_string, 'GSIA_default')

        value_table: ValueTable = measure.value_tables[0]
        self.assertEqual(value_table.name, 'Offering ID')
        self.assertEqual(value_table.api_name, 'offerId')
        self.assertEqual(value_table.type, 'value_table')
        self.assertEqual(value_table.description, None)
        self.assertEqual(value_table.order, 1)
        self.assertEqual(value_table.determinants, ['Desc'])
        self.assertEqual(len(value_table.columns), 2)
        self.assertEqual(value_table.values, [['ASH Controls', 'A', 'Low-temperature reach-in display cases equipped with special display case glass doors that have no anti-sweat heaters']])
        self.assertEqual(value_table.reference_refs, [])

        column: Column = value_table.columns[0]
        self.assertEqual(column.name, 'Statewide Measure Offering ID')
        self.assertEqual(column.api_name, 'ID')
        self.assertEqual(column.unit, 'text')
        self.assertEqual(column.reference_refs, [])


    def test_contains(self):
        measure = Measure('./resources/SWCR014.json')
        self.assertTrue(measure.contains_param('MeasAppType'))
        self.assertTrue(measure.contains_param('BldgType'))
        self.assertTrue(measure.contains_param('LightingType'))
        self.assertTrue(measure.contains_param('iEBldgType'))
        self.assertFalse(measure.contains_param('fake param'))
        self.assertFalse(measure.contains_param('MeasAppType-015'))

        self.assertTrue(measure.contains_value_table('offerId'))
        self.assertTrue(measure.contains_value_table('costs'))
        self.assertTrue(measure.contains_value_table('emergingTech'))
        self.assertFalse(measure.contains_param('Emerging Technologies'))
        self.assertFalse(measure.contains_value_table('fake table'))

        self.assertTrue(measure.contains_shared_table('GSIA_default'))
        self.assertTrue(measure.contains_shared_table('EUL'))
        self.assertTrue(measure.contains_shared_table('CFac'))
        self.assertTrue(measure.contains_shared_table('Null'))
        self.assertFalse(measure.contains_shared_table('fake table'))
        self.assertFalse(measure.contains_shared_table('EUL-021'))
        self.assertFalse(measure.contains_shared_table('residentialInteractiveEffects'))

        self.assertTrue(measure.contains_table('offerId'))
        self.assertTrue(measure.contains_table('costs'))
        self.assertTrue(measure.contains_table('GSIA_default'))
        self.assertTrue(measure.contains_table('CFac'))
        self.assertTrue(measure.contains_table('Null'))
        self.assertFalse(measure.contains_table('fake name'))
        self.assertFalse(measure.contains_table('residentialInteractiveEffects'))
        self.assertFalse(measure.contains_table('ahioefbWIEBFwiefbnSFLKwblibufgilaLOIGAERBLI;bliruabe'))

        self.assertTrue(measure.contains_permutation('RUL_Yrs'))
        self.assertTrue(measure.contains_permutation('OfferingID'))
        self.assertTrue(measure.contains_permutation('OfferingDesc'))
        self.assertTrue(measure.contains_permutation('DEER_MeasureID'))
        self.assertFalse(measure.contains_permutation('gibberishW;ERFIBl;iwbeu;beairfujbg'))
        self.assertFalse(measure.contains_permutation('not a real permutation'))

        self.assertTrue(measure.contains_MAT_label('NR'))
        self.assertTrue(measure.contains_MAT_label('NR', 'NC'))
        self.assertTrue(measure.contains_MAT_label('NC', 'NR'))
        self.assertFalse(measure.contains_MAT_label('AR'))
        self.assertFalse(measure.contains_MAT_label('AOE', 'NR'))
        self.assertFalse(measure.contains_MAT_label('NR', 'AR'))


    def test_getters(self):
        measure = Measure('./resources/SWCR014.json')
        self.assertTrue(measure.get_shared_parameter('MeasAppType') != None)
        self.assertTrue(measure.get_shared_parameter('BldgType') != None)
        self.assertTrue(measure.get_shared_parameter('iEBldgType') != None)
        self.assertTrue(measure.get_shared_parameter('fake name') == None)
        self.assertTrue(measure.get_shared_parameter(7) == None)

        self.assertTrue(measure.get_value_table('offerId') != None)
        self.assertTrue(measure.get_value_table('emergingTech') != None)
        self.assertTrue(measure.get_value_table('fake name') == None)

        self.assertTrue(measure.get_shared_table('GSIA_default') != None)
        self.assertTrue(measure.get_shared_table('Null') != None)
        self.assertTrue(measure.get_shared_table('EUL-021') == None)
        self.assertTrue(measure.get_shared_table('fake name') == None)

        self.assertTrue(measure.get_permutation('RUL_Yrs') != None)
        self.assertTrue(measure.get_permutation('OfferingID') != None)
        self.assertTrue(measure.get_permutation('OfferingDesc') != None)
        self.assertTrue(measure.get_permutation('fake perm') == None)
        self.assertTrue(measure.get_permutation('l;lfiuerbafliBWFLlabiubfr') == None)

        self.assertTrue(measure.get_characterization('TechnologySummary') != None)
        self.assertTrue(measure.get_characterization('DEERDifferencesAnalysis') != None)
        self.assertTrue(measure.get_characterization('fake name') == None)
        self.assertTrue(measure.get_characterization('asdrfgtrhtasrzergaergeraga') == None)


    def test_measure_queries(self):
        measure = Measure('./resources/SWCR002.json')
        self.assertTrue(measure.contains_MAT_label('NR'))
        self.assertFalse(measure.contains_MAT_label('NR', 'NC'))
        self.assertFalse(measure.contains_MAT_label('AOE'))
        self.assertFalse(measure.is_DEER())
        self.assertFalse(measure.is_WEN())
        self.assertTrue(measure.is_deemed())
        self.assertFalse(measure.is_fuel_sub())
        self.assertTrue(measure.is_sector_default())
        self.assertFalse(measure.requires_ntg_version())
        self.assertFalse(measure.requires_upstream_flag())
        self.assertFalse(measure.is_res_default())
        self.assertTrue(measure.is_nonres_default())
        self.assertTrue(measure.is_GSIA_default())
        self.assertFalse(measure.is_interactive())
        self.assertEqual(measure.get_criteria(), ['REQ', 'DEF_GSIA', 'RES_NDEF', 'MAT_NCNR'])

        measure = Measure('./resources/SWCR014.json')
        self.assertTrue(measure.contains_MAT_label('NR', 'NC'))
        self.assertFalse(measure.is_DEER())
        self.assertFalse(measure.is_WEN())
        self.assertTrue(measure.is_deemed())
        self.assertFalse(measure.is_fuel_sub())
        self.assertTrue(measure.is_sector_default())
        self.assertFalse(measure.requires_ntg_version())
        self.assertTrue(measure.requires_upstream_flag())
        self.assertFalse(measure.is_res_default())
        self.assertTrue(measure.is_nonres_default())
        self.assertTrue(measure.is_GSIA_default())
        self.assertTrue(measure.is_interactive())
        self.assertEqual(measure.get_criteria(), ['REQ', 'DEF_GSIA', 'INTER', 'RES_NDEF', 'NAT_NCNR', 'DEEM', 'ET'])


if __name__ == '__main__':
    ut.main()