# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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


class StockMove(models.Model):

    _inherit = "stock.move"

    returned_qty = fields.Float('Returned qty.', help="""Qty. of move that will
                                be returned on produce""")

    served_qty = fields.Float('Served qty',
                              help="Quality system field, no data")

    q_production_id = fields.Many2one('mrp.production', '')

    changed_qty_return = fields.Boolean('changed_qty_return')


class stockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def do_enter_transfer_details(self):
        """
            Se sobreescribe la funcion para evitar problemas con el contexto.
        """
        changed = False
        for move in self.move_lines:
            if (move.q_production_id or move.raw_material_production_id) and not move.changed_qty_return:
#                 if move.product_uom_qty != move.served_qty:
#                     raise exceptions.Warning(_("""Cannot produce because
# move quantity %s and served quantity %s don't match""") %
#                                              (str(move.product_uom_qty),
#                                               str(move.served_qty)))
                if move.returned_qty > 0:
                    changed = True
                    move.changed_qty_return = True
                    move.do_unreserve()
                    if move.product_uom_qty == move.returned_qty:
                        move.action_cancel()
                        continue
                    if not move.original_move:
                        continue
                    move.product_uom_qty = move.served_qty - move.returned_qty
                    move.original_move.do_unreserve()
                    move.original_move.product_uom_qty += move.returned_qty
                    move.original_move.action_assign()
                    move.action_assign()
        if changed:
            if self.state == 'cancel':
                return
            self.do_unreserve()
            self.action_assign()
        created = self.env['stock.transfer_details'].with_context(
            {'active_model': self._name,
                'active_ids': self._ids,
                'active_id': len(self) and self[0].id or False
            }).create(
            {'picking_id': len(self) and self[0].id or False})
        return created.wizard_view()
