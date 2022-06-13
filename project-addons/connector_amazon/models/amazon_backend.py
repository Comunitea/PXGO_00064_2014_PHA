# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from openerp import api, fields, models
from openerp.addons.connector.session import ConnectorSession

from .amazon_account_invoice import import_invoices_since


class AmazonBackend(models.Model):
    _name = "amazon.backend"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    refresh_token = fields.Text()
    lwa_app_id = fields.Char()
    lwa_client_secret = fields.Char()
    aws_secret_key = fields.Char()
    aws_access_key = fields.Char()
    role_arn = fields.Char()
    currency_id = fields.Many2one("res.currency", "Currency")
    marketplace = fields.Selection([("ES", "es")], default="ES")
    normal_journal_id = fields.Many2one(
        "account.journal", "Journal for invoices with vat", required=True
    )
    simplified_journal_id = fields.Many2one(
        "account.journal", "Journal for simplified invoices", required=True
    )
    refund_journal_id = fields.Many2one(
        "account.journal", "Journal for refund invoices with vat", required=True
    )
    refund_simplified_journal_id = fields.Many2one(
        "account.journal", "Journal for refund simplified invoices", required=True
    )
    sale_channel_id = fields.Many2one(
        "sale.channel", string="Sale channel", required=True
    )
    salesperson_id = fields.Many2one("res.users")
    default_fiscal_position_id = fields.Many2one('account.fiscal.position', 'Default fiscal position', required=True)
    partner_categ_id = fields.Many2one(
        "res.partner.category", "Category for partners", required=True
    )

    @api.multi
    def get_credentials(self):
        self.ensure_one()
        return dict(
            refresh_token=self.refresh_token,
            lwa_app_id=self.lwa_app_id,
            lwa_client_secret=self.lwa_client_secret,
            aws_secret_key=self.aws_secret_key,
            aws_access_key=self.aws_access_key,
            role_arn=self.role_arn,
        )

    @api.multi
    def import_invoices_last_month(self):
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            since_date = datetime.now() + timedelta(days=-30)
            import_invoices_since.delay(
                session,
                backend_record.id,
                since_date,
                priority=10,
            )
        return True

    @api.multi
    def get_journal(self, invoice_type, vat):
        self.ensure_one()
        if invoice_type == 'out_invoice':
            if vat:
                return self.normal_journal_id
            else:
                return self.simplified_journal_id
        elif invoice_type == 'out_refund':
            if vat:
                return self.refund_normal_journal_id
            else:
                return self.refund_simplified_journal_id
