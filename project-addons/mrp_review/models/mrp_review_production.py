# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, exceptions, _


class MrpReviewProduction(models.Model):

    _name = 'mrp.review.production'
    _inherits = {'mrp.production': 'production_id'}

    production_id = fields.Many2one('mrp.production', 'Production')

    production_notes = fields.Text('Production notes')
    direction_notes = fields.Text('Direction notes')
    production_adjustement_ids = fields.One2many('mrp.production.adjustments',
                                                 compute='_get_adjustement_ids')
    review_state = fields.Selection((('draft', 'Draft'), ('done', 'Done')),
                                    'State', default='draft')

    @api.one
    @api.depends('production_id')
    def _get_adjustement_ids(self):
        ids = []
        for workcenter_line in self.production_id.workcenter_lines:
            if workcenter_line.adjustsments_ids:
                ids += workcenter_line.adjustsments_ids._ids
        self.production_adjustement_ids = ids
