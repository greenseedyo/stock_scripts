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

    def set_shorting_criteria(self, criteria):
        if not isinstance(criteria, ICriteria):
            raise ValueError('argument #1 must an instance of ICriteria');
        self.shorting_criteria = criteria

    def set_shorting_more_criteria(self, criteria):
        if not isinstance(criteria, ICriteria):
            raise ValueError('argument #1 must an instance of ICriteria');
        self.shorting_more_criteria = criteria

    def set_covering_criteria(self, criteria):
        if not isinstance(criteria, ICriteria):
            raise ValueError('argument #1 must an instance of ICriteria');
        self.covering_criteria = criteria

    def check_buying_criteria(self, data_sets):
        try:
            self.buying_criteria
        except AttributeError:
            return False
        return self.buying_criteria.check(data_sets)

    def check_buying_more_criteria(self, data_sets):
        try:
            self.buying_more_criteria
        except AttributeError:
            return False
        return self.buying_more_criteria.check(data_sets)

    def check_selling_criteria(self, data_sets):
        try:
            self.selling_criteria
        except AttributeError:
            return False
        return self.selling_criteria.check(data_sets)

    def check_shorting_criteria(self, data_sets):
        try:
            self.shorting_criteria
        except AttributeError:
            return False
        return self.shorting_criteria.check(data_sets)

    def check_shorting_more_criteria(self, data_sets):
        try:
            self.shorting_criteria
        except AttributeError:
            return False
        return self.shorting_more_criteria.check(data_sets)

    def check_covering_criteria(self, data_sets):
        try:
            self.covering_criteria
        except AttributeError:
            return False
        return self.coverling_criteria.check(data_sets)
