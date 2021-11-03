# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class ProductStockUnsafety(models.Model):
    _inherit = 'product.stock.unsafety'
    _inherits = {'product.product': 'product_id'}

    product_id = fields.Many2one(string='Product',
                                 comodel_name='product.product',
                                 required=True,
                                 ondelete='cascade',
                                 readonly=True)
    stock_by_day_i = fields.Float(string='Stock by day [I]', digits=(16, 2),
                                  readonly=True)
    stock_by_day_p = fields.Float(string='Stock by day [P]', digits=(16, 2),
                                  readonly=True)
    stock_by_day_p_ind_min = fields.Float(string='Minimum stock by day [P] (indirect)',
                                          digits=(16, 2), readonly=True)
    stock_by_day_i_total = fields.Float(
        string='Stock by day [I] (direct+indirect)', digits=(16, 2),
        readonly=True)
    stock_by_day_p_total = fields.Float(
        string='Stock by day [P] (direct+indirect)', digits=(16, 2),
        readonly=True)
    min_action = fields.Float(string='Minimum action quantity',
                              compute='_min_action')
    action_limit_exceeded = fields.Boolean(compute='_action_limit_exceeded',
                                           store=True)

    @api.one
    def _min_action(self):
        orderpoint_id = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_id.id),
            ('from_date', '<=', fields.Date.today()),
            ('to_date', '>=', fields.Date.today())],
            order='id desc', limit=1)

        if not orderpoint_id:
            orderpoint_id = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', self.product_id.id),
                ('from_date', '=', False),
                ('to_date', '=', False)],
                order='id desc', limit=1)

        self.min_action = orderpoint_id.product_min_action_qty \
            if orderpoint_id else 0

    @api.one
    @api.depends('min_action', 'virtual_conservative')
    def _action_limit_exceeded(self):
        self.action_limit_exceeded = self.virtual_conservative < self.min_action

    @api.model
    def create(self, vals):
        res = super(ProductStockUnsafety, self).create(vals)
        res.write({
            'stock_by_day_i': res.product_id.stock_by_day_i,
            'stock_by_day_p': res.product_id.stock_by_day_p,
            'stock_by_day_i_total': res.product_id.stock_by_day_i_total,
            'stock_by_day_p_total': res.product_id.stock_by_day_p_total
        })
        return res

    @api.multi
    def create_production_planning_order(self):
        return self.product_id.create_production_planning_order()
