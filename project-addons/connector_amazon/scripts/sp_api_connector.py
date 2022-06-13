#!/usr/bin/env python3.6
import csv
import sys
import time
from io import StringIO

from sp_api.api import Orders, Reports
from sp_api.base import (Marketplaces, SellingApiException,
                         SellingApiRequestThrottledException)

AMAZON_TIME_RATE_LIMIT = float(55)


def list_orders(credentials, start_date, end_date):
    reports_api = Reports(marketplace=Marketplaces.ES, credentials=credentials)
    try:
        report_created = reports_api.create_report(
            reportType="SC_VAT_TAX_REPORT",
            dataStartTime=start_date,
            dataEndTime=end_date,
        ).payload
    except SellingApiException as e:
        raise Exception(
            ("Amazon API Error. No order was created due to errors. '%s' \n") % e
        )
    report_state = ""
    while report_state != "DONE":
        try:
            report = reports_api.get_report(report_created.get("reportId")).payload
            report_state = report.get("processingStatus")
        except SellingApiRequestThrottledException:
            time.sleep(AMAZON_TIME_RATE_LIMIT)
            continue
        except SellingApiException as e:
            raise Exception(
                ("Amazon API Error. Report %s. '%s' \n")
                % (report_created.get("reportId"), e)
            )

    document_data = reports_api.get_report_document(
        report.get("reportDocumentId"), decrypt=True
    ).payload
    # para pruebas
    # with open('/home/comunitea/Escritorio/prueba2.csv', 'w') as f:
    #     f.write(document_data['document'])
    csvfile = StringIO(document_data["document"])
    csv_reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
    orders = {}
    for row in csv_reader:
        key = f"{row['Order ID']}_{row['VAT Invoice Number']}"
        if key not in orders:
            orders.setdefault(
                key,
                {
                    "order_ref": row["Order ID"],
                    "partner_vat": row["Buyer Tax Registration"],
                    "invoice_number": row["VAT Invoice Number"],
                    "partner_country": row["Ship To Country"],
                    "invoice_date": row["Tax Calculation Date"],
                    "invoice_type": row["Transaction Type"],
                    "intracommunity": False,
                    "lines_data": [
                        {
                            "reference": row["SKU"],
                            "amount_total": float(
                                row["OUR_PRICE Tax Inclusive Selling Price"]
                            ),
                            "amount_tax": float(row["OUR_PRICE Tax Amount"]),
                            "amount_untaxed": float(
                                row["OUR_PRICE Tax Exclusive Selling Price"]
                            ),
                            "quantity": row["Quantity"],
                        }
                    ],
                },
            )
            if row["Buyer Tax Registration Type"] == "VAT":
                orders[key]["partner_is_company"] = True
                if row['Tax Calculation Reason Code'] == 'Taxable' and row['Tax Rate'] == '0.00' and row['Buyer Tax Registration Jurisdiction'] != 'ES':
                    # Puede venir a 0 aunque no sea intracomunitaria por errores de amazon.
                    orders[key]['intracommunity'] = True
        else:
            orders[key]["lines_data"].append(
                {
                    "reference": row["SKU"],
                    "amount_total": float(row["OUR_PRICE Tax Inclusive Selling Price"]),
                    "amount_tax": float(row["OUR_PRICE Tax Amount"]),
                    "amount_untaxed": float(
                        row["OUR_PRICE Tax Exclusive Selling Price"]
                    ),
                    "quantity": row["Quantity"],
                }
            )
    print(orders)


def get_order(credentials, order_refs):
    orders_api = Orders(marketplace=Marketplaces.ES, credentials=credentials)
    orders = []
    for order in order_refs.split(","):
        order_data = None
        while not order_data:
            try:
                buyer_info = orders_api.get_order_buyer_info(order).payload
                address_info = orders_api.get_order_address(order).payload
                order_info = orders_api.get_order(order).payload
                order_data = {
                    "amz_status": order_info.get("OrderStatus"),
                    "partner_email": buyer_info.get("BuyerEmail"),
                    "partner_name": buyer_info.get("BuyerName"),
                    "partner_street": address_info.get("ShippingAddress", {}).get(
                        "AddressLine1"
                    ),
                    "partner_street2": address_info.get("ShippingAddress", {}).get(
                        "AddressLine2"
                    ),
                    "partner_city": address_info.get("ShippingAddress", {}).get("City"),
                    "partner_zip": address_info.get("ShippingAddress", {}).get(
                        "PostalCode"
                    ),
                    "partner_state": address_info.get("ShippingAddress", {}).get(
                        "StateOrRegion"
                    ),
                }
            except SellingApiRequestThrottledException as e:
                time.sleep(AMAZON_TIME_RATE_LIMIT)
                continue
        orders.append(order_data)
    print(orders)


if __name__ == "__main__":
    """
    argumentos script:
        - operaciona realizar (LIST_ORDERS/GET_ORDER)
        - refresh_token
        - lwa_app_id
        - lwa_client_secret
        - aws_secret_key
        - aws_access_key
        - role_arn
        * Si la operación es LIST_ORDERS
            - fecha inicio (YYYY-MM-DDTHH:MM:SS)
            -fecha fin (YYYY-MM-DDTHH:MM:SS)
        * Si la operacion es GET_ORDER
            -Referencia del pedido/referencias separadas por coma.
    """
    args = sys.argv
    args.pop(0)  # ruta script
    if len(args) < 7:
        sys.exit(1)
    operation = args[0]
    credentials = dict(
        refresh_token=args[1],
        lwa_app_id=args[2],
        lwa_client_secret=args[3],
        aws_secret_key=args[4],
        aws_access_key=args[5],
        role_arn=args[6],
    )

    if operation == "LIST_ORDERS":
        if len(args) < 9:
            sys.exit(1)
        list_orders(credentials, args[7], args[8])
    elif operation == "GET_ORDER":
        if len(args) < 8:
            sys.exit(1)
        get_order(credentials, args[7])
    else:
        sys.exit(2)
