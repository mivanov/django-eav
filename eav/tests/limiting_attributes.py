from django.test import TestCase

import eav
from ..registry import EavConfig
from ..models import Attribute, Value

from .models import Patient, Encounter


class LimitingAttributes(TestCase):

    def setUp(self):
        class EncounterEavConfig(EavConfig):
            manager_attr = 'eav_objects'
            eav_attr = 'eav_field'
            generic_relation_attr = 'encounter_eav_values'
            generic_relation_related_name = 'encounters'

            @classmethod
            def get_attributes(cls, entity=None):
                return Attribute.objects.filter(slug__contains='a')

        eav.register(Encounter, EncounterEavConfig)
        eav.register(Patient)

        Attribute.objects.create(name='age', datatype=Attribute.TYPE_INT)
        Attribute.objects.create(name='height', datatype=Attribute.TYPE_FLOAT)
        Attribute.objects.create(name='weight', datatype=Attribute.TYPE_FLOAT)

    def tearDown(self):
        eav.unregister(Encounter)
        eav.unregister(Patient)

    def test_get_attribute_querysets(self):
        self.assertEqual(Patient._eav_config_cls \
                                .get_attributes().count(), 3)
        self.assertEqual(Encounter._eav_config_cls \
                                .get_attributes().count(), 1)

    def test_setting_attributes(self):
        p = Patient.objects.create(name='Jon')
        e = Encounter.objects.create(patient=p, num=1)
        p.eav.age = 3
        p.eav.height = 2.3
        p.save()
        e.eav_field.age = 4
        e.eav_field.height = 4.5
        e.save()
        self.assertEqual(Value.objects.count(), 3)
        p = Patient.objects.get(name='Jon')
        self.assertEqual(p.eav.age, 3)
        self.assertEqual(p.eav.height, 2.3)
        e = Encounter.objects.get(num=1)
        self.assertEqual(e.eav_field.age, 4)
        self.assertFalse(hasattr(e.eav_field, 'height'))
        
        
class AttributesWithParents(TestCase):
    
    def setUp(self):
        eav.register(Encounter, filter_by_parent=True)
        eav.register(Patient, filter_by_parent=True)
        Attribute.objects.create(name='age', parent=Patient, datatype=Attribute.TYPE_INT)
        Attribute.objects.create(name='date', parent=Encounter, datatype=Attribute.TYPE_DATE)
        Attribute.objects.create(name='cost', parent=Encounter, datatype=Attribute.TYPE_FLOAT)
    
    def tearDown(self):
        eav.unregister(Encounter)
        eav.unregister(Patient)
    
    def test_partitioned_admin(self):
        """
        Tests of the attribute partitioning admin objects.
        """
        patient_attrs = Patient._eav_config_cls.get_attributes()
        self.assertEqual(len(patient_attrs), 1)
        
        encounter_attrs = Encounter._eav_config_cls.get_attributes()
        self.assertEqual(len(encounter_attrs), 2)

        
