# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class PrestashopProductCombination(models.Model):
    _inherit = "prestashop.product.combination"

    main_template_id = fields.Many2one(
        required=False,
    )

    # _sql_constraints = [
    #     ('prestashop_product_combination_prestashop_erp_uniq', 'Check(1=1)',
    #      'A record with same ID already exists on PrestaShop.'),
    # ]

    def init(self, cr):
        cr.execute(
            "alter table prestashop_product_combination "
            "drop constraint if exists prestashop_product_combination_prestashop_erp_uniq"
        )
        return True


class ProductProduct(models.Model):
    _inherit = 'product.product'

    need_export_stock = fields.Boolean()

    @api.multi
    def update_prestashop_qty(self):
        if self._context.get("cron_compute"):
            self.write({"need_export_stock": False})
            for prod in self:
                boms = self.env["mrp.bom"].search(
                    [("bom_line_ids.product_id", "=", prod.id)]
                )
                if boms:
                    self = (
                        self
                        + boms.mapped("product_tmpl_id.product_variant_ids")
                        + boms.mapped("product_id")
                    )
            for product in self:
                product.product_tmpl_id.update_prestashop_quantities()
                # Recompute qty in combination binding
                for combination_binding in product.prestashop_bind_ids:
                    combination_binding.recompute_prestashop_qty()
                for combination_binding in product.prestashop_combinations_bind_ids:
                    combination_binding.recompute_prestashop_qty()
        else:
            self.write({"need_export_stock": True})

    @api.model
    def cron_export_custom_stock(self):
        self.with_context(cron_compute=True).search([('need_export_stock', '=', True)]).update_prestashop_qty()
        return True
