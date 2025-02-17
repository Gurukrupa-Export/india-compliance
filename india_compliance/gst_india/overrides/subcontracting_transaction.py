from pypika import Order

import frappe
from frappe import _, bold
from frappe.contacts.doctype.address.address import get_address_display
from frappe.utils import flt
from erpnext.accounts.party import get_address_tax_category
from erpnext.stock.get_item_details import get_item_tax_template

from india_compliance.gst_india.overrides.sales_invoice import (
    update_dashboard_with_gst_logs,
)
from india_compliance.gst_india.overrides.transaction import (
    GSTAccounts,
    get_place_of_supply,
    ignore_gst_validations,
    is_inter_state_supply,
    set_gst_tax_type,
    validate_gst_category,
    validate_gst_transporter_id,
    validate_gstin_status,
    validate_items,
    validate_mandatory_fields,
    validate_place_of_supply,
)
from india_compliance.gst_india.utils import (
    get_gst_accounts_by_type,
    is_api_enabled,
    is_outward_stock_entry,
)
from india_compliance.gst_india.utils import (
    validate_invoice_number as validate_transaction_name,
)
from india_compliance.gst_india.utils.e_waybill import get_e_waybill_info
from india_compliance.gst_india.utils.taxes_controller import (
    CustomTaxController,
    update_gst_details,
    validate_taxes,
)

STOCK_ENTRY_FIELD_MAP = {"total_taxable_value": "total_taxable_value"}
SUBCONTRACTING_ORDER_RECEIPT_FIELD_MAP = {"total_taxable_value": "total"}


# Functions to perform operations before and after mapping of transactions
def after_mapping_subcontracting_order(doc, method, source_doc):
    if source_doc.doctype != "Purchase Order":
        return

    doc.taxes_and_charges = ""
    doc.taxes = []

    if ignore_gst_validations(doc):
        return

    set_taxes(doc)

    if not doc.items:
        return

    tax_category = source_doc.tax_category

    if not tax_category:
        tax_category = get_address_tax_category(
            frappe.db.get_value("Supplier", source_doc.supplier, "tax_category"),
            source_doc.supplier_address,
        )

    args = {"company": doc.company, "tax_category": tax_category}

    for item in doc.items:
        out = {}
        item_doc = frappe.get_cached_doc("Item", item.item_code)
        get_item_tax_template(args, item_doc, out)
        item.item_tax_template = out.get("item_tax_template")


def after_mapping_stock_entry(doc, method, source_doc):
    if source_doc.doctype != "Subcontracting Order":
        doc.taxes_and_charges = ""
        doc.taxes = []

    if doc.purpose != "Material Transfer" or not doc.is_return:
        return

    doc.bill_to_address = source_doc.billing_address
    doc.bill_from_address = source_doc.supplier_address
    doc.bill_to_gstin = source_doc.company_gstin
    doc.bill_from_gstin = source_doc.supplier_gstin
    set_address_display(doc)


def before_mapping_subcontracting_receipt(doc, method, source_doc, table_maps):
    table_maps["India Compliance Taxes and Charges"] = {
        "doctype": "India Compliance Taxes and Charges",
        "add_if_empty": True,
    }


def set_taxes(doc):
    accounts = get_gst_accounts_by_type(doc.company, "Output", throw=False)
    if not accounts:
        return

    sales_tax_template = frappe.qb.DocType("Sales Taxes and Charges Template")
    sales_tax_template_row = frappe.qb.DocType("Sales Taxes and Charges")

    rate = (
        frappe.qb.from_(sales_tax_template_row)
        .left_join(sales_tax_template)
        .on(sales_tax_template.name == sales_tax_template_row.parent)
        .select(sales_tax_template_row.rate)
        .where(sales_tax_template_row.parenttype == "Sales Taxes and Charges Template")
        .where(sales_tax_template_row.account_head == accounts.get("igst_account"))
        .where(sales_tax_template.disabled == 0)
        .orderby(sales_tax_template.is_default, order=Order.desc)
        .orderby(sales_tax_template.modified, order=Order.desc)
        .limit(1)
        .run(pluck=True)
    )
    rate = rate[0] if rate else 0

    tax_types = ("igst",)
    if not is_inter_state_supply(doc):
        tax_types = ("cgst", "sgst")
        rate = flt(rate / 2)

    for tax_type in tax_types:
        account = accounts.get(tax_type + "_account")
        doc.append(
            "taxes",
            {
                "charge_type": "On Net Total",
                "account_head": account,
                "rate": rate,
                "gst_tax_type": tax_type,
                "description": account,
            },
        )


# Common Functions for Suncontracting Transactions
def get_dashboard_data(data):
    doctype = (
        "Subcontracting Receipt"
        if data.fieldname == "subcontracting_receipt"
        else "Stock Entry"
    )
    return update_dashboard_with_gst_logs(
        doctype,
        data,
        "e-Waybill Log",
        "Integration Request",
    )


def onload(doc, method=None):
    if doc.doctype == "Stock Entry":
        set_address_display(doc)

        # For e-Waybill data mapping
        doc.company_gstin = doc.bill_from_gstin
        doc.supplier_gstin = doc.bill_to_gstin
        doc.gst_category = doc.bill_to_gst_category

    if not doc.get("ewaybill"):
        return

    gst_settings = frappe.get_cached_doc("GST Settings")

    if not (
        is_api_enabled(gst_settings)
        and gst_settings.enable_e_waybill
        and gst_settings.enable_e_waybill_for_sc
    ):
        return

    doc.set_onload("e_waybill_info", get_e_waybill_info(doc))


def validate(doc, method=None):
    if ignore_gst_validations(doc):
        return

    if not is_e_waybill_applicable(doc):
        return

    if doc.doctype in ("Stock Entry", "Subcontracting Receipt"):
        validate_transaction_name(doc)

    field_map = (
        STOCK_ENTRY_FIELD_MAP
        if doc.doctype == "Stock Entry"
        else SUBCONTRACTING_ORDER_RECEIPT_FIELD_MAP
    )
    CustomTaxController(doc, field_map).set_taxes_and_totals()

    set_gst_tax_type(doc)
    validate_taxes(doc)

    if validate_transaction(doc) is False:
        return

    update_gst_details(doc)


def before_save(doc, method=None):
    if ignore_gst_validations(doc):
        return

    validate_doc_references(doc)


def before_submit(doc, method=None):
    if ignore_gst_validations(doc):
        return

    validate_doc_references(doc)


def validate_doc_references(doc):
    is_return_material_transfer = (
        doc.doctype == "Stock Entry"
        and doc.purpose == "Material Transfer"
        and doc.is_return
    )

    is_subcontracting_receipt = (
        doc.doctype == "Subcontracting Receipt" and not doc.is_return
    )

    if not (is_return_material_transfer or is_subcontracting_receipt):
        return

    if doc.doc_references:
        remove_duplicates(doc)
        return

    error_msg = _("Please Select Original Document Reference for ITC-04 Reporting")
    if is_return_material_transfer:
        frappe.throw(error_msg, title=_("Mandatory Field"))
    else:
        frappe.msgprint(error_msg, alert=True, indicator="yellow")


def validate_transaction(doc, method=None):
    validate_items(doc)

    if doc.doctype == "Stock Entry":
        company_gstin_field = "bill_from_gstin"
        party_gstin_field = "bill_to_gstin"
        company_address_field = "bill_from_address"
        gst_category_field = "bill_to_gst_category"
    else:
        company_gstin_field = "company_gstin"
        party_gstin_field = "supplier_gstin"
        company_address_field = "billing_address"
        gst_category_field = "gst_category"

    if doc.place_of_supply:
        validate_place_of_supply(doc)
    else:
        doc.place_of_supply = get_place_of_supply(doc, doc.doctype)

    if validate_company_address_field(doc, company_address_field) is False:
        return False

    if (
        validate_mandatory_fields(doc, (company_gstin_field, "place_of_supply"))
        is False
    ):
        return False

    if getattr(doc, company_address_field) and (
        validate_mandatory_fields(
            doc,
            gst_category_field,
            _(
                "{0} is a mandatory field for GST Transactions. Please ensure that"
                " it is set in the Party and / or Address."
            ),
        )
        is False
    ):
        return False

    elif not doc.get(gst_category_field):
        setattr(doc, gst_category_field, "Unregistered")

    gstin = getattr(doc, party_gstin_field)

    validate_gstin_status(gstin, doc.get("posting_date") or doc.get("transaction_date"))
    validate_gst_transporter_id(doc)
    validate_gst_category(doc.get(gst_category_field), gstin)

    SubcontractingGSTAccounts().validate(doc, True)


def validate_company_address_field(doc, company_address_field):
    if (
        validate_mandatory_fields(
            doc,
            company_address_field,
            _(
                "Please set {0} to ensure Bill From GSTIN is fetched in the transaction."
            ).format(bold(doc.meta.get_label(company_address_field))),
        )
        is False
    ):
        return False


class SubcontractingGSTAccounts(GSTAccounts):
    def validate(self, doc, is_sales_transaction=False):
        self.doc = doc
        self.is_sales_transaction = is_sales_transaction

        if not self.doc.taxes:
            return

        if not self.has_gst_tax_rows():
            return

        self.setup_defaults()

        self.validate_invalid_account_for_transaction()  # Sales / Purchase
        self.validate_for_same_party_gstin()
        self.validate_for_invalid_account_type()  # CGST / SGST / IGST
        self.validate_for_charge_type()

    def validate_for_same_party_gstin(self):
        if is_outward_stock_entry(self.doc):
            return

        company_gstin = self.doc.get("company_gstin") or self.doc.get("bill_from_gstin")
        party_gstin = self.doc.get("supplier_gstin") or self.doc.get("bill_to_gstin")

        if not party_gstin or company_gstin != party_gstin:
            return

        self._throw(
            _(
                "Cannot charge GST in Row #{0} since Bill From GSTIN and Bill To GSTIN are"
                " same"
            ).format(self.first_gst_idx)
        )

    def validate_for_charge_type(self):
        for row in self.gst_tax_rows:
            # validating charge type "On Item Quantity" and non_cess_advol_account
            self.validate_charge_type_for_cess_non_advol_accounts(row)


def set_address_display(doc):
    adddress_fields = (
        "bill_from_address",
        "bill_to_address",
        "ship_from_address",
        "ship_to_address",
    )

    for address in adddress_fields:
        if doc.get(address):
            setattr(doc, address + "_display", get_address_display(doc.get(address)))


@frappe.whitelist()
def get_relevant_references(filters=None):
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)

    receipt_returns = get_subcontracting_receipt_references(filters=filters)
    stock_entries = get_stock_entry_references(
        filters=filters, only_linked_references=True
    )

    return {
        "Subcontracting Receipt": [row[0] for row in receipt_returns],
        "Stock Entry": [row[0] for row in stock_entries],
    }


@frappe.whitelist()
def get_subcontracting_receipt_references(
    doctype=None, txt=None, searchfield=None, start=None, page_len=None, filters=None
):
    filters = frappe._dict(filters)

    _filters = [
        ["docstatus", "=", 1],
        ["is_return", "=", 1],
        ["supplier", "=", filters.supplier],
        ["Subcontracting Receipt Item", "item_code", "in", filters.received_items],
        [
            "Subcontracting Receipt Item",
            "subcontracting_order",
            "in",
            filters.subcontracting_orders,
        ],
    ]

    if txt:
        _filters.append(["name", "like", f"%{txt}%"])

    return frappe.db.get_all(
        "Subcontracting Receipt",
        filters=_filters,
        fields=["name", "posting_date"],
        group_by="name",
        as_list=True,
    )


@frappe.whitelist()
def get_stock_entry_references(
    doctype=None,
    txt=None,
    searchfield=None,
    start=None,
    page_len=None,
    filters=None,
    only_linked_references=False,
):
    filters = frappe._dict(filters)

    or_filters = []
    _filters = [
        ["docstatus", "=", 1],
        ["purpose", "=", "Send to Subcontractor"],
        ["supplier", "=", filters.supplier],
        ["Stock Entry Detail", "item_code", "in", filters.supplied_items],
    ]

    if txt:
        _filters.append(["name", "like", f"%{txt}%"])

    if only_linked_references:
        _filters.append(["subcontracting_order", "in", filters.subcontracting_orders])

    else:
        or_filters = [
            ["subcontracting_order", "is", "not set"],
            ["subcontracting_order", "in", filters.subcontracting_orders],
        ]

    return frappe.db.get_all(
        "Stock Entry",
        filters=_filters,
        or_filters=or_filters,
        fields=["name", "posting_date", "subcontracting_order"],
        group_by="name",
        as_list=True,
    )


def remove_duplicates(doc):
    references = []
    has_duplicates = False

    for row in doc.doc_references:
        ref = (row.link_doctype, row.link_name)

        if ref not in references:
            references.append(ref)
        else:
            has_duplicates = True

    if has_duplicates:
        doc.doc_references = []
        for row in references:
            doc.append("doc_references", dict(link_doctype=row[0], link_name=row[1]))


def is_e_waybill_applicable(doc):
    gst_settings = frappe.get_cached_doc("GST Settings")

    if not (
        gst_settings.enable_api
        and gst_settings.enable_e_waybill
        and gst_settings.enable_e_waybill_for_sc
    ):
        return False

    if doc.doctype != "Stock Entry":
        return True

    if doc.purpose not in [
        "Material Transfer",
        "Material Issue",
        "Send to Subcontractor",
    ]:
        return False

    return True
