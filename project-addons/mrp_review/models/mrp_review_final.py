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


class MrpReviewFinal(models.Model):

    _name = 'mrp.review.final'
    _inherits = {'mrp.production': 'production_id'}

    production_id = fields.Many2one('mrp.production', 'Production',
                                    required=True, ondelete='cascade')
    review_state = fields.Selection((('draft', 'Draft'), ('done', 'Done')),
                                    'State', default='draft')


class StockMove(models.Model):

    _inherit = 'stock.move'

    lot_supplier_id = fields.Many2one('res.partner', 'Supplier', readonly=True,
                                      related='restrict_lot_id.partner_id')
    acceptance_date = fields.Date('Acceptance date', readonly=True,
                                  related='restrict_lot_id.acceptance_date')
