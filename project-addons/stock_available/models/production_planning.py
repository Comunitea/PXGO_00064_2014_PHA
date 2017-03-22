# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class ProductionPlanning(models.Model):
    _name = 'production.planning'
    _description = 'Production planning of stock needed to produce'

    name = fields.Char('Production planning')


class ProductionPlanningOrders(models.Model):
    _name = 'production.planning.orders'
    _description = 'Planning of orders to produce'

    name = fields.Char(compute='_compound_name')
    date_start = fields.Datetime(string='Start date',
                                 default=lambda r: fields.Datetime.now())
    date_end = fields.Datetime(string='End date',
                               default=lambda r: fields.Datetime.now())
    product_id = fields.Many2one(string='Final product',
                                 comodel_name='product.product',
                                 required=True)
    default_code = fields.Char(related='product_id.default_code')
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id')
    bom_id = fields.Many2one(string='Bills of materials',
                             comodel_name='mrp.bom',
                             domain="[('product_tmpl_id', '=', product_tmpl_id)]",
                             required=True)
    line_id = fields.Many2one(string='Line',
                              comodel_name='mrp.routing',
                              domain="[('product_ids', 'in', product_tmpl_id)]",
                              required=True)
    product_qty = fields.Integer(string='Quantity to predict')
    production_planning = fields.Many2one(comodel_name='production.planning',
                                          ondelete='cascade',
                                          readonly=True)
    compute = fields.Boolean(string='Compute', default=True)
    stock_status = fields.Selection([('ok', 'Available'),
                                     ('out', 'Out of stock'),
                                     ('incoming', 'Incoming'),
                                     ('no_stock', 'Not available')],
                                    string='Stock status', default='ok')
    production_order = fields.Many2one(comodel_name='mrp.production',
                                       readonly=True)
    note = fields.Char(string='Note for production')
    active = fields.Boolean(default=True)

    @api.multi
    def _compound_name(self):
        for order in self:
            if order.default_code == 'Gen0001':
                order.name =  u'{} ({:d}) PR{:d}'.\
                    format(order.note, order.product_qty, order.id)
            elif self.env.context.get('show_only_order_id', False):
                order.name = u'PR{:d}'.format(order.id)
            else:
                order.name =  u'{} ({:d}) PR{:d}'.\
                    format(order.product_id.name, order.product_qty, order.id)

    @api.onchange('product_id')
    def update_bom(self):
        bom_dom = [('product_tmpl_id', '=', self.product_tmpl_id.id)]
        bom_ids = self.env['mrp.bom'].search(bom_dom)
        self.bom_id = bom_ids[0] if bom_ids else False
        self.line_id = False

    @api.onchange('date_start')
    def check_date_end(self):
        if self.date_start > self.date_end:
            self.date_end = self.date_start

    @api.onchange('date_end')
    def check_date_start(self):
        if self.date_start > self.date_end:
            self.date_start = self.date_end

    @api.multi
    def generate_order_and_archive(self):
        # Update production planning order line and recompute requirements
        self.active = False
        self.compute = False
        self.stock_available = True  # In archive, its'nt necessary
        self.production_planning.recompute_requirements()

        # Create production order and show it
        order = self.env['mrp.production'].create({
            'product_id': self.product_id.id,
            'bom_id': self.bom_id.id,
            'product_qty': self.product_qty,
            'product_uom': self.product_id.uom_id.id,
            'routing_id': self.line_id.id,
            'date_planned': self.date_start,
            'user_id': self.env.user.id,
            'origin': _('Production planning order Nº %s') % (self.id)
        })
        self.production_order = order
        if self.note:
            order.message_post(body=self.note)

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'res_id': order.id,
            'target': 'current',
            'context': self.env.context,
        }

    @api.model
    def create(self, vals):
        vals['production_planning'] = self.env.\
            ref('stock_available.production_planning_1').id
        return super(models.Model, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('date_start', False) or vals.get('date_end', False):
            has_production_order = False
            for o in self:
                has_production_order = has_production_order or o.production_order

            if has_production_order:
                raise Warning(_('The dates cannot be changed, '
                                'there are an associated production order'))

        return super(models.Model, self).write(vals)

    @api.multi
    def show_materials_needed(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'production.planning.orders',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def save_order(self):
        self.production_planning.recompute_requirements()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def cancel_order(self):
        self.unlink()


class ProductionPlanningMaterials(models.Model):
    _name = 'production.planning.materials'
    _description = 'Prevision of needed materials'
    _rec_name = 'product_id'

    product_id = fields.Many2one(string='Material',
                                 comodel_name='product.product')
    default_code = fields.Char(related='product_id.default_code')
    qty_required = fields.Float(string='Quantity required', digits=(16,2))
    qty_vsc_available = fields.Float(string='Virtual stock conservative',
                                 digits=(16,2))
    qty_incoming = fields.Float(related='product_id.real_incoming_qty', digits=(16,2))
    out_of_existences = fields.Float(related='product_id.out_of_existences',
                                     digits=(16,2))
    uom = fields.Char(string='Unit of measure')
    orders = fields.Many2many(string='Orders',
                              comodel_name='production.planning.orders',
                              relation='production_planning_ord_mat_rel',
                              ondelete='cascade')
    stock_status = fields.Selection([('ok', 'Available'),
                                     ('out', 'Out of stock'),
                                     ('incoming', 'Incoming'),
                                     ('no_stock', 'Not available')],
                                    string='Stock status', default='ok')
    production_planning = fields.Many2one(comodel_name='production.planning',
                                          readonly=True)


class ProductionPlanningOrders(models.Model):
    _inherit = 'production.planning.orders'

    materials = fields.Many2many(string='Orders',
                                 comodel_name='production.planning.materials',
                                 relation='production_planning_ord_mat_rel')


class ProductionPlanning(models.Model):
    _inherit = 'production.planning'

    orders = fields.One2many(string='Production planning orders',
                             comodel_name='production.planning.orders',
                             inverse_name='production_planning')
    materials = fields.One2many(string='Prevision of needed materials',
                                comodel_name='production.planning.materials',
                                inverse_name='production_planning')

    @api.one
    def recompute_requirements(self):
        self.materials.unlink()
        for order in self.orders:
            if order.compute:
                for line in order.bom_id.bom_line_ids:
                    material = self.materials.search([('product_id', '=',
                                                       line.product_id.id)])
                    if material:
                        material.write({
                            'qty_required': material.qty_required +
                                            (line.product_qty * order.product_qty),
                            'orders': [(4, order.id)],
                        })
                    else:
                        self.materials.create({
                            'product_id': line.product_id.id,
                            'qty_required': line.product_qty * order.product_qty,
                            'qty_vsc_available': line.product_id.virtual_conservative,
                            'uom': line.product_uom.name,
                            'orders': [(4, order.id)],
                            'production_planning': self.id
                        })

        # Check material level of availability
        for m in self.materials:
            if m.qty_vsc_available + m.qty_incoming < m.qty_required:
                m.stock_status = 'no_stock'
            elif m.qty_vsc_available < m.qty_required and m.qty_vsc_available + m.qty_incoming >= m.qty_required:
                m.stock_status = 'incoming'
            elif m.qty_vsc_available - m.out_of_existences < m.qty_required and m.qty_vsc_available >= m.qty_required:
                m.stock_status = 'out'
            else:
                m.stock_status = 'ok'

        # Inherits worst stock status to orders
        for order in self.orders:
            order.stock_status = 'ok'
            for m in order.materials:
                if m.stock_status != 'ok' and \
                   order.stock_status != 'no_stock' and \
                   (
                    (order.stock_status == 'ok') or
                    (order.stock_status == 'out' and
                        m.stock_status not in ('ok', 'out')) or
                    (order.stock_status == 'incoming' and
                        m.stock_status == 'no_stock')
                   ):
                    order.stock_status = m.stock_status

    @api.multi
    def write(self, vals):
        result = super(ProductionPlanning, self).write(vals)
        self.recompute_requirements()
        return result
