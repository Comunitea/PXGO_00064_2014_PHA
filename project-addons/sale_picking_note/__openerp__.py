# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
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
    'name': 'Sale to picking note',
    'version': '1.0',
    'author': 'Pharmadus I+D+i',
    'summary' : 'Write internal comments at sale form to view in picking',
    'description': "Write internal comments at sale form to view in picking",
    'category': 'Sale, Warehouse',
    'website': 'www.pharmadus.com',
    'depends' : [
        'base',
        'sale',
        'stock',
    ],
    'data' : [
        'views/sale_view.xml',
    ],
    'installable': True
}

