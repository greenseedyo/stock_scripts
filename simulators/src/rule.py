# -*- coding: utf-8 -*-

import sys
from src.criterias.interfaces import *
from src.criterias.short import *

class Rule(object):
    def set_buying_criteria(self, criteria):
        if not isinstance(criteria, ICriteria):
            raise ValueError('argument #1 must an instance of ICriteria');
        self.buying_criteria = criteria

    def set_buying_more_criteria(self, criteria):
        if not isinstance(criteria, ICriteria):
            raise ValueError('argument #1 must an instance of ICriteria');
        self.buying_more_criteria = criteria

    def set_selling_criteria(self, criteria):
        if not isinstance(criteria, ICriteria):
            raise ValueError('argument #1 must an instance of ICriteria');
        self.selling_criteria = criteria

    def check_buying_criteria(self, data_sets):
        self.buying_criteria.check(data_sets)

    def check_buying_more_criteria(self, data_sets):
        self.buying_more_criteria.check(data_sets)

    def check_selling_criteria(self, data_sets):
        self.selling_criteria.check(data_sets)
