import json

class EmbeddedData:
    def __init__(self, obj_info: dict):
        self.id = obj_info.get('id')
        self.title: str = obj_info.get('title')
        self.ctype_id: int = obj_info.get('ctype_id')
        self.verbose_name: str = obj_info.get('verbose_name')
        self.verbose_name_plural: str = obj_info.get('verbose_name_plural')
        self.change_url: str = obj_info.get('change_url')

    def _embedded_decoder(d: dict) -> dict:
        obj_info: dict = d.get('objInfo')
        obj_info['deleted'] = d.get('objDeleted')
        return obj_info


class EmbeddedValueTable(EmbeddedData):
    def __init__(self, embedded_table: str):
        table_info: dict = json.loads(embedded_table,
                                      object_hook=self._embedded_decoder)
        super().__init__(table_info)
        self.api_name_unique: str | None = table_info.get('api_name_unique')
        self.columns: list[str] = self._get_columns(table_info)

    def _get_columns(table_info: dict) -> list[str]:
        vt_conf: object | None = table_info.get('vt_conf')
        if vt_conf == None:
            return []
        return getattr(vt_conf, 'cids', [])


class EmbeddedReference(EmbeddedData):
    def __init__(self, embedded_reference: str):
        reference_info: dict = json.loads(embedded_reference,
                                          object_hook=self._embedded_decoder)
        super().__init__(reference_info)
        self.preview_url: str = reference_info.get('ref_type')
        self.ref_type: str = reference_info.get('ref_type')

    def _embedded_decoder(d: dict) -> dict:
        obj_info: dict = d.get('objInfo')
        obj_info['ref_type'] = d.get('refType')
        obj_info['deleted'] = d.get('objDeleted')
        return obj_info


class EmbeddedCalculation(EmbeddedData):
    def __init__(self, embedded_calculation: str):
        calculation_info: dict \
            = json.loads(embedded_calculation,
                         object_hook=self._embedded_decoder)
        super().__init__(calculation_info)
        self.api_name_unique: str | None \
            = calculation_info.get('api_name_unique')
        