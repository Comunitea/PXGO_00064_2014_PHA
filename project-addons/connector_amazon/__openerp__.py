# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Amazon connector for invoices",
    "version": "8.0.1.0.0",
    "category": "Connector",
    "author": "Comunitea",
    "license": "AGPL-3",
    "depends": [
        "connector",
    ],
    "data": [
        "views/amazon_backend.xml",
        "views/amazon_account_invoice.xml",
        "views/res_partner.xml",
        "security/ir.model.access.csv",
    ],
}
