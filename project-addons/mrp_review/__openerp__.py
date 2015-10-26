# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
    'name': "MRP review",
    'version': '1.0',
    'category': 'production',
    'description': """Adds the state review on mrp.production.""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['mrp', 'mrp_hoard', 'qweb_usertime', 'quality_management_menu',
                'quality_protocol_report', 'PHA_quality_documents'],
    "data": ['security/mrp_review_security.xml',
             'security/ir.model.access.csv',
             'mrp_workflow.xml',
             'views/quality_management_menu.xml',
             'views/mrp_view.xml',
             'views/mrp_review_production_view.xml',
             'views/mrp_review_quality_view.xml',
             'views/mrp_review_final_view.xml',
             'views/final_certificate_report.xml',
             'views/mrp_review_quality_report.xml',
             'views/mrp_review_report.xml',
             'views/product_category_view.xml'],
    "installable": True
}
