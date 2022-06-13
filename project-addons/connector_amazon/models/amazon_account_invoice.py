# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import locale
import os
import re
from datetime import datetime

import openerp.addons.decimal_precision as dp
from openerp import _, api, fields, models
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

from ..tools.script_launcher import (call_script_get_order,
                                     call_script_list_orders)

INVOICE_TYPES_MAP = {
    "SHIPMENT": "out_invoice",
    "RETURN": "out_refund",
    "REFUND": "out_refund",
}


def _formatString(text):
    """Formats the string into a fixed length ASCII (iso-8859-1) record.

    Note:
        'Todos los campos alfanuméricos y alfabéticos se presentarán
        alineados a la izquierda y rellenos de blancos por la derecha,
        en mayúsculas sin caracteres especiales, y sin vocales acentuadas.
        Para los caracteres específicos del idioma se utilizará la
        codificación ISO-8859-1. De esta forma la letra “Ñ” tendrá el
        valor ASCII 209 (Hex. D1) y la “Ç” (cedilla mayúscula) el valor
        ASCII 199 (Hex. C7).'
    """
    # Replace accents and convert to upper
    from unidecode import unidecode

    text = unicode(text).upper()
    text = "".join([unidecode(x) if x not in (u"Ñ", u"Ç") else x for x in text])
    text = re.sub(ur"[^A-Z0-9\s\.,-_&'´\\:;/\(\)ÑÇ\"]", "", text, re.UNICODE | re.X)
    return text


def _formatFiscalName(text):
    name = re.sub(
        ur"[^a-zA-Z0-9\sáÁéÉíÍóÓúÚñÑçÇäÄëËïÏüÜöÖ"
        ur"àÀèÈìÌòÒùÙâÂêÊîÎôÔûÛ\.,-_&'´\\:;:/]",
        "",
        text,
        re.UNICODE | re.X,
    )
    name = re.sub(r"\s{2,}", " ", name, re.UNICODE | re.X)
    return _formatString(name)


class AmazonAccountInvoice(models.Model):
    _name = "amazon.account.invoice"
    _inherit = ["mail.thread"]
    _rec_name = "order_ref"
    _decription = "amazon invoices"

    _sql_constraints = [
        (
            "order_ref_invoice_unique",
            "unique(order_ref, invoice_number)",
            "order reference and invoice number already exists!",
        )
    ]

    backend_id = fields.Many2one("amazon.backend")
    partner_id = fields.Many2one("res.partner")
    partner_name = fields.Char()
    partner_email = fields.Char()
    partner_street = fields.Char()
    partner_street2 = fields.Char()
    partner_city = fields.Char()
    partner_zip = fields.Char()
    partner_state = fields.Char()
    partner_vat = fields.Char()
    partner_is_company = fields.Boolean()
    partner_country = fields.Char("Partner country code")
    country_id = fields.Many2one("res.country", "Partner country")
    order_ref = fields.Char()
    invoice_number = fields.Char()
    invoice_date = fields.Date()
    invoice_line_ids = fields.One2many(
        "amazon.account.invoice.line", "amazon_invoice_id"
    )
    invoice_id = fields.Many2one("account.invoice")
    amz_status = fields.Char("Amazon status")
    invoice_type = fields.Selection(
        [("out_invoice", "Customer invoice"), ("out_refund", "Refund invoice")]
    )
    intracommunity = fields.Boolean()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("downloaded", "Data downloaded"),
            ("invoiced", "Invoiced"),
            ("error", "Error"),
        ],
        default="draft",
    )
    amount_untaxed = fields.Float(
        string="Untaxed",
        digits=dp.get_precision("Account"),
        store=True,
        readonly=True,
        compute="_compute_amount",
    )
    amount_tax = fields.Float(
        string="Tax",
        digits=dp.get_precision("Account"),
        store=True,
        readonly=True,
        compute="_compute_amount",
    )
    amount_total = fields.Float(
        string="Total",
        digits=dp.get_precision("Account"),
        store=True,
        readonly=True,
        compute="_compute_amount",
    )
    currency_id = fields.Many2one(
        "res.currency", related="backend_id.currency_id", readonly=True
    )

    @api.multi
    @api.depends(
        "invoice_line_ids.amount_untaxed",
        "invoice_line_ids.amount_tax",
        "invoice_line_ids.amount_total",
    )
    def _compute_amount(self):
        for invoice in self:
            invoice.amount_untaxed = sum(
                invoice.mapped("invoice_line_ids.amount_untaxed")
            )
            invoice.amount_tax = sum(invoice.mapped("invoice_line_ids.amount_tax"))
            invoice.amount_total = sum(invoice.mapped("invoice_line_ids.amount_total"))

    @api.model
    def format_vat(self, country_code, vat):
        if not vat:
            return ""
        if vat[:2] != country_code:
            vat = country_code + vat
        return vat

    @api.model
    def create(self, vals):
        vat = vals.get("partner_vat")
        if vat:
            vat = self.format_vat(vals["partner_country"], vat)
            partner = self.env["res.partner"].search([("vat", "=", vat)], limit=1)
            if partner:
                vals["partner_id"] = partner.id
        elif vals.get("partner_email"):
            partner = self.env["res.partner"].search(
                [("amazon_email", "=", vals.get("partner_email"))], limit=1
            )
            if partner:
                vals["partner_id"] = partner.id
        if vals.get("partner_country"):
            country = self.env["res.country"].search(
                [("code", "=", vals["partner_country"])], limit=1
            )
            if country:
                vals["country_id"] = country.id
        res = super(AmazonAccountInvoice, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        for rec in self:
            if not vals.get('partner_id', rec.partner_id):
                if vals.get('partner_vat', rec.partner_vat) or vals.get('partner_country', rec.partner_country):
                    vat = vals.get("partner_vat", rec.partner_vat)
                    if vat:
                        vat = self.format_vat(
                            vals.get("partner_country", rec.partner_country), vat
                        )
                        partner = self.env["res.partner"].search(
                            [("vat", "=", vat)], limit=1
                        )
                        if partner:
                            vals["partner_id"] = partner.id
                elif vals.get("partner_email", rec.partner_email):
                    partner = self.env["res.partner"].search(
                        [("amazon_email", "=", vals.get("partner_email"))], limit=1
                    )
                    if partner:
                        vals["partner_id"] = partner.id
            if vals.get("partner_country"):
                country = self.env["res.country"].search(
                    [("code", "=", vals["partner_country"])], limit=1
                )
                if country:
                    vals["country_id"] = country.id
            super(AmazonAccountInvoice, rec).write(vals)
        return True

    @api.multi
    def download_order_data(self):
        for record in self:
            session = ConnectorSession(
                self.env.cr, self.env.uid, context=self.env.context
            )
            import_order_data.delay(
                session,
                record.backend_id.id,
                record.id,
                priority=99,
            )
        return True

    def error(self, message):
        self.ensure_one()
        self.state = "error"
        self.message_post(body=message)

    @api.multi
    def create_partner(self):
        self.ensure_one()
        if self.partner_id:
            raise ValidationError(_("Partner alreadary setted"))
        if not self.partner_name:
            raise ValidationError(_("Missing partner name"))
        if not self.country_id and self.partner_country:
            raise ValidationError(
                _("Country with code {} not found").format(self.partner_country)
            )
        partner_vals = {
            "name": self.partner_name,
            "is_company": self.partner_is_company,
            "vat": self.format_vat(self.partner_country, self.partner_vat),
            "street": self.partner_street,
            "street2": self.partner_street2,
            "city": self.partner_city,
            "zip": self.partner_zip,
            "amazon_email": self.partner_email,
            "country_id": self.country_id.id,
        }
        if self.backend_id.salesperson_id:
            partner_vals["user_id"] = self.backend_id.salesperson_id.id
        if self.backend_id.partner_categ_id:
            partner_vals["category_id"] = [(4, self.backend_id.partner_categ_id.id)]

        city_zip = self.env["res.better.zip"].search(
            [
                ("name", "=", self.partner_zip),
                ("country_id", "=", self.country_id.id),
            ]
        )
        if not city_zip:
            # Portugal
            city_zip = self.env["res.better.zip"].search(
                [
                    ("name", "=", self.partner_zip.replace(" ", "-")),
                    ("country_id", "=", self.country_id.id),
                ]
            )
            if not city_zip:
                # Portugal 2
                city_zip = self.env["res.better.zip"].search(
                    [
                        (
                            "name",
                            "=",
                            self.partner_zip[:4] + "-" + self.partner_zip[4:],
                        ),
                        ("country_id", "=", self.country_id.id),
                    ]
                )
        if city_zip:
            partner_vals["state_id"] = city_zip[0].state_id.id
            if len(city_zip) == 1:
                partner_vals["zip_id"] = city_zip.id

        if self.intracommunity:
            fpos = self.env['account.fiscal.position'].search(
                [('intracommunity_operations', '=', True)], limit=1)
            if not fpos:
                raise ValidationError(_('Fiscal position not found for intracommunity operations'))
        else:
            fpos = self.env['account.fiscal.position'].search(
                [('country_id', '=', self.country_id.id)], limit=1)
            if not fpos:
                fpos = self.backend_id.default_fiscal_position_id
        partner_vals['property_account_position'] = fpos.id
        self.partner_id = self.env["res.partner"].create(partner_vals)

    @api.multi
    def create_invoice(self):
        for rec in self:
            if not rec.partner_id:
                try:
                    rec.create_partner()
                except ValidationError as e:
                    rec.error(e.message)
                    continue
            journal = self.backend_id.get_journal(rec.invoice_type, rec.partner_id.vat)
            rec.invoice_id = self.env["account.invoice"].create(
                {
                    "journal_id": journal.id,
                    "partner_id": rec.partner_id.id,
                    "account_id": rec.partner_id.property_account_receivable.id,
                    "fiscal_position": rec.partner_id.property_account_position.id,
                    "reference_type": "none",
                    "name": rec.order_ref,
                    "comment": "{} \n {}".format(rec.invoice_number, rec.invoice_date),
                    "type": rec.invoice_type,
                    "sale_channel_id": rec.backend_id.sale_channel_id.id,
                }
            )
            for invoice_line in rec.invoice_line_ids:
                new_line = self.env['account.invoice.line'].create({
                    'product_id': invoice_line.product_id.id,
                    'name': invoice_line.product_id.name_get()[0][1],
                    'quantity': invoice_line.quantity,
                    'price_unit': invoice_line.amount_untaxed / invoice_line.quantity,
                    'invoice_id': rec.invoice_id.id,
                })
                onchange_vals = new_line.product_id_change(new_line.product_id.id, False, qty=new_line.quantity, name='', type=rec.invoice_id.type, partner_id=rec.invoice_id.partner_id.id, fposition_id=rec.invoice_id.fiscal_position.id, price_unit=new_line.price_unit, currency_id=rec.invoice_id.currency_id.id)['value']
                onchange_vals.pop('price_unit')
                onchange_vals['invoice_line_tax_id'] = [(4, x) for x in onchange_vals['invoice_line_tax_id']]
                new_line.write(onchange_vals)
            rec.invoice_id.button_reset_taxes()
            rec.state = 'invoiced'


class AmazonAccountInvoiceLine(models.Model):
    _name = "amazon.account.invoice.line"

    reference = fields.Char()
    amount_untaxed = fields.Float()
    amount_tax = fields.Float()
    amount_total = fields.Float()
    quantity = fields.Float()
    product_id = fields.Many2one("product.product")
    amazon_invoice_id = fields.Many2one("amazon.account.invoice")

    @api.model
    def create(self, vals):
        with_error = False
        reference = vals.get("reference")
        if reference:
            if reference.endswith("-PL"):
                reference = reference[:-3]
            product = self.env["product.product"].search(
                [("default_code", "=", reference)]
            )
            if len(product) != 1:
                with_error = True
            else:
                vals["product_id"] = product.id
        res = super(AmazonAccountInvoiceLine, self).create(vals)
        if with_error:
            res.amazon_invoice_id.error(
                _("Not found product with ref {}").format(reference)
            )
        return res


@job(default_channel="root.amazon")
def import_invoices_since(session, backend_id, since_date):
    """ Import orders from tax record report """
    backend = session.env["amazon.backend"].browse(backend_id)
    now_fmt = datetime.now()
    orders = call_script_list_orders(backend.get_credentials(), since_date, now_fmt)
    for key in orders:
        order_ref = orders[key]["order_ref"]
        invoice_number = orders[key]["invoice_number"]
        order_exist = session.env["amazon.account.invoice"].search(
            [("order_ref", "=", order_ref), ("invoice_number", "=", invoice_number)],
            limit=1,
        )
        if not order_exist:
            order_data = orders[key]
            order_data["backend_id"] = backend_id
            old_locale = locale.getlocale()
            # Las fechas vienen siempre en ingles p.ej: '03-Apr-2021 UTC'
            locale.setlocale(locale.LC_TIME, "en_US.utf8")
            order_data["invoice_date"] = datetime.strptime(
                order_data["invoice_date"], "%d-%b-%Y %Z"
            ).strftime(DEFAULT_SERVER_DATE_FORMAT)
            order_data["invoice_type"] = INVOICE_TYPES_MAP[order_data["invoice_type"]]
            locale.setlocale(locale.LC_TIME, old_locale)
            lines = order_data.pop("lines_data")
            new_lines = [(0, 0, x) for x in lines]
            order_data["invoice_line_ids"] = new_lines
            amazon_invoice = session.env["amazon.account.invoice"].create(order_data)
            if amazon_invoice.invoice_number == "N/A":
                # error en amazon. Se creará manualmente ya que primero se debe de hablar con soporte de amazon para crearla.
                amazon_invoice.error(
                    _(
                        "Order without invoice number. Contact amazon and create it manually"
                    )
                )
            import_order_data.delay(
                session,
                backend_id,
                amazon_invoice.id,
                priority=99,
            )


@job(default_channel="root.amazon")
def import_order_data(session, backend_id, amazon_invoice_id):
    backend = session.env["amazon.backend"].browse(backend_id)
    amz_invoice = session.env["amazon.account.invoice"].browse(amazon_invoice_id)
    order_data = call_script_get_order(backend.get_credentials(), amz_invoice.order_ref)
    order_data = order_data[0]
    order_data["partner_name"] = _formatFiscalName(order_data["partner_name"])
    if order_data["amz_status"] == "Shipped" and amz_invoice.state != "error":
        order_data["state"] = "downloaded"
    amz_invoice.write(order_data)
