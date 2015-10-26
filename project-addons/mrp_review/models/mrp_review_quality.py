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


class MrpReviewQuality(models.Model):

    _name = 'mrp.review.quality'
    _inherits = {'mrp.production': 'production_id'}

    production_id = fields.Many2one('mrp.production', 'Production',
                                    required=True, ondelete='cascade')

    case = fields.Selection((('agreed', 'Agreed'),
                             ('not agreed', 'Not agreed'), ('na', 'N/A')),
                            'Case')
    tag = fields.Selection((('agreed', 'Agreed'), ('not agreed', 'Not agreed'),
                            ('na', 'N/A')), 'Tag')
    thread = fields.Selection((('agreed', 'Agreed'),
                               ('not agreed', 'Not agreed'), ('na', 'N/A')),
                              'Thread')
    paper = fields.Selection((('agreed', 'Agreed'),
                              ('not agreed', 'Not agreed'), ('na', 'N/A')),
                             'Paper')
    calification = fields.Boolean('Calification')

    raw_lot_id = fields.Many2one('stock.production.lot', 'Raw lot',
                                 compute='_get_raw_lot', store=True)
    raw_product_id = fields.Many2one('product.product', 'Raw product',
                                     related='raw_lot_id.product_id')
    analysis_ids = fields.One2many(related='raw_lot_id.analysis_ids',
                                   string='Analysis')
    review_state = fields.Selection((('draft', 'Draft'), ('done', 'Done')),
                                    'State', default='draft')

    @api.one
    @api.depends('production_id')
    def _get_raw_lot(self):
        for line in self.production_id.move_lines + \
                self.production_id.move_lines2:
            if line.product_id.categ_id.raw_material_category:
                self.raw_lot_id = line.restrict_lot_id
                return

    @api.multi
    def quality_review(self):
        for qual_review in self:
            qual_review.review_state = 'done'
            qual_review.production_id.quality_review()
