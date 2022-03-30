def get_invoice_details(**kwargs):
    return """
{{
    "Version": "1.1",
    "TranDtls": {{
        "TaxSch": "{transaction_details.tax_scheme}",
        "SupTyp": "{transaction_details.supply_type}",
        "RegRev": "{transaction_details.reverse_charge}",
        "EcmGstin": "{transaction_details.ecom_gstin}",
        "IgstOnIntra": "{transaction_details.igst_on_intra}"
    }},
    "DocDtls": {{
        "Typ": "{doc_details.invoice_type}",
        "No": "{doc_details.invoice_name}",
        "Dt": "{doc_details.invoice_date}"
    }},
    "SellerDtls": {{
        "Gstin": "{seller_details.gstin}",
        "LglNm": "{seller_details.legal_name}",
        "TrdNm": "{seller_details.trade_name}",
        "Loc": "{seller_details.location}",
        "Pin": "{seller_details.pincode}",
        "Stcd": "{seller_details.state_code}",
        "Addr1": "{seller_details.address_line1}",
        "Addr2": "{seller_details.address_line2}",
        "Ph": "{seller_details.phone}",
        "Em": "{seller_details.email}"
    }},
    "BuyerDtls": {{
        "Gstin": "{buyer_details.gstin}",
        "LglNm": "{buyer_details.legal_name}",
        "TrdNm": "{buyer_details.trade_name}",
        "Addr1": "{buyer_details.address_line1}",
        "Addr2": "{buyer_details.address_line2}",
        "Loc": "{buyer_details.location}",
        "Pin": "{buyer_details.pincode}",
        "Stcd": "{buyer_details.state_code}",
        "Ph": "{buyer_details.phone}",
        "Em": "{buyer_details.email}",
        "Pos": "{buyer_details.place_of_supply}"
    }},
    "DispDtls": {{
        "Nm": "{dispatch_details.legal_name}",
        "Addr1": "{dispatch_details.address_line1}",
        "Addr2": "{dispatch_details.address_line2}",
        "Loc": "{dispatch_details.location}",
        "Pin": "{dispatch_details.pincode}",
        "Stcd": "{dispatch_details.state_code}"
    }},
    "ShipDtls": {{
        "Gstin": "{shipping_details.gstin}",
        "LglNm": "{shipping_details.legal_name}",
        "TrdNm": "{shipping_details.trader_name}",
        "Addr1": "{shipping_details.address_line1}",
        "Addr2": "{shipping_details.address_line2}",
        "Loc": "{shipping_details.location}",
        "Pin": "{shipping_details.pincode}",
        "Stcd": "{shipping_details.state_code}"
    }},
    "ItemList": [
        {item_list}
    ],
    "ValDtls": {{
        "AssVal": "{invoice_value_details.base_total}",
        "CgstVal": "{invoice_value_details.total_cgst_amt}",
        "SgstVal": "{invoice_value_details.total_sgst_amt}",
        "IgstVal": "{invoice_value_details.total_igst_amt}",
        "CesVal": "{invoice_value_details.total_cess_amt}",
        "Discount": "{invoice_value_details.invoice_discount_amt}",
        "RndOffAmt": "{invoice_value_details.round_off}",
        "OthChrg": "{invoice_value_details.total_other_charges}",
        "TotInvVal": "{invoice_value_details.base_grand_total}",
        "TotInvValFc": "{invoice_value_details.grand_total}"
    }},
    "PayDtls": {{
        "Nm": "{payment_details.payee_name}",
        "AccDet": "{payment_details.account_no}",
        "Mode": "{payment_details.mode_of_payment}",
        "FinInsBr": "{payment_details.ifsc_code}",
        "PayTerm": "{payment_details.terms}",
        "PaidAmt": "{payment_details.paid_amount}",
        "PaymtDue": "{payment_details.outstanding_amount}"
    }},
    "RefDtls": {{
        "DocPerdDtls": {{
            "InvStDt": "{period_details.start_date}",
            "InvEndDt": "{period_details.end_date}"
        }},
        "PrecDocDtls": [{{
            "InvNo": "{prev_doc_details.invoice_name}",
            "InvDt": "{prev_doc_details.invoice_date}"
        }}]
    }},
    "ExpDtls": {{
        "ShipBNo": "{export_details.bill_no}",
        "ShipBDt": "{export_details.bill_date}",
        "Port": "{export_details.port}",
        "ForCur": "{export_details.foreign_curr_code}",
        "CntCode": "{export_details.country_code}",
        "ExpDuty": "{export_details.export_duty}"
    }},
    "EwbDtls": {{
        "TransId": "{eway_bill_details.gstin}",
        "TransName": "{eway_bill_details.name}",
        "TransMode": "{eway_bill_details.mode_of_transport}",
        "Distance": "{eway_bill_details.distance}",
        "TransDocNo": "{eway_bill_details.document_name}",
        "TransDocDt": "{eway_bill_details.document_date}",
        "VehNo": "{eway_bill_details.vehicle_no}",
        "VehType": "{eway_bill_details.vehicle_type}"
    }}
}}
""".format(
        **kwargs
    )


def get_item_details(**kwargs):
    return """
{{
    "SlNo": "{item.sr_no}",
    "PrdDesc": "{item.description}",
    "IsServc": "{item.is_service_item}",
    "HsnCd": "{item.gst_hsn_code}",
    "Barcde": "{item.barcode}",
    "Unit": "{item.uom}",
    "Qty": "{item.qty}",
    "FreeQty": "{item.free_qty}",
    "UnitPrice": "{item.unit_rate}",
    "TotAmt": "{item.gross_amount}",
    "Discount": "{item.discount_amount}",
    "AssAmt": "{item.taxable_value}",
    "PrdSlNo": "{item.serial_no}",
    "GstRt": "{item.tax_rate}",
    "IgstAmt": "{item.igst_amount}",
    "CgstAmt": "{item.cgst_amount}",
    "SgstAmt": "{item.sgst_amount}",
    "CesRt": "{item.cess_rate}",
    "CesAmt": "{item.cess_amount}",
    "CesNonAdvlAmt": "{item.cess_nadv_amount}",
    "StateCesRt": "{item.state_cess_rate}",
    "StateCesAmt": "{item.state_cess_amount}",
    "StateCesNonAdvlAmt": "{item.state_cess_nadv_amount}",
    "OthChrg": "{item.other_charges}",
    "TotItemVal": "{item.total_value}",
    "BchDtls": {{
        "Nm": "{item.batch_no}",
        "ExpDt": "{item.batch_expiry_date}"
    }}
}}
""".format(
        **kwargs
    )

    # if row.batch_no:
    #     batch_expiry_date = frappe.db.get_value(
    #             "Batch", row.batch_no, "expiry_date"
    #         )
    #     batch_expiry_date_str = format_date(batch_expiry_date, self.DATE_FORMAT)
    # else:
    #     batch_expiry_date_str = ""

    # row.update(
    #         {
    #             "qty": abs(row.qty),
    #             "rate": abs(row.taxable_value)
    #             if flt(row.qty) == 0
    #             else abs(row.taxable_value / row.qty),
    #             "taxable_value": abs(row.taxable_value),
    #             "discount_amount": 0,
    #             "is_service_item": "Y"
    #             if row.gst_hsn_code and row.gst_hsn_code[:2] == "99"
    #             else "N",
    #             "hsn_code": int(row.gst_hsn_code),
    #             "batch_expiry_date_str": batch_expiry_date_str,
    #             "serial_no": "",
    #             "item_name": self.sanitize_data(row.item_name, "text"),
    #             "uom": "",
    #         }
    #     )
