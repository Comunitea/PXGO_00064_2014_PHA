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

{
    'name': 'Custom sale commission',
    'version': '1.0',
    'category': 'sale',
    'description': """""",
    'author': 'Comunitea',
    'website': '',
    "depends": ['sale', 'sale_commission', 'stock_account', 'product_m2mcategories'],
    "data": ['saleagent_view.xml', 'settlement_view.xml', 'product_category_view.xml',
             'security/ir.model.access.csv'],
    "installable": True
}
