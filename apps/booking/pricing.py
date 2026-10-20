from decimal import Decimal, ROUND_HALF_UP

from apps.booking.models import DiscountKind, PriceVariable, PriceVariableCategory, QuoteEstimate, QuoteLineItem, TaxSettings


CENT = Decimal("0.01")
DESTINATION_SERVICE_SLUGS = frozenset(
    {
        "moving-services-nyc",
        "apartment-moving-nyc",
        "small-moves-nyc",
        "moving-and-cleaning-nyc",
    }
)


def money(value):
    return Decimal(value or 0).quantize(CENT, rounding=ROUND_HALF_UP)


def service_needs_destination(service):
    return bool(service and service.slug in DESTINATION_SERVICE_SLUGS)


def calculate_quote(amounts, discount_amount, tax_rate):
    subtotal = money(sum((Decimal(amount) for amount in amounts), Decimal("0")))
    discount = money(discount_amount)
    if discount < 0:
        discount = Decimal("0.00")
    if discount > subtotal:
        discount = subtotal
    taxable = subtotal - discount
    rate = Decimal(tax_rate or 0)
    if rate < 0:
        rate = Decimal("0")
    tax_amount = money(taxable * rate / Decimal("100"))
    return {
        "subtotal": subtotal,
        "discount_amount": discount,
        "tax_rate": rate,
        "tax_amount": tax_amount,
        "total": taxable + tax_amount,
    }


def discount_dollars(subtotal, kind, value):
    subtotal = money(subtotal)
    value = money(value)
    if value < 0:
        value = Decimal("0.00")
    if kind == DiscountKind.PERCENT:
        if value > 100:
            value = Decimal("100.00")
        return money(subtotal * value / Decimal("100")), value
    if value > subtotal:
        value = subtotal
    return value, Decimal("0.00")


def discount_for_selection(variables, subtotal):
    best_amount = Decimal("0.00")
    best_kind = DiscountKind.AMOUNT
    best_rate = Decimal("0.00")
    for variable in variables:
        if variable.discount_kind == DiscountKind.AMOUNT:
            amount = money(variable.discount_amount)
            kind = DiscountKind.AMOUNT
            rate = Decimal("0.00")
        else:
            rate = Decimal(variable.discount_percent or 0)
            if rate < 0:
                rate = Decimal("0.00")
            amount = money(Decimal(subtotal) * rate / Decimal("100"))
            kind = DiscountKind.PERCENT
        if amount > best_amount:
            best_amount = amount
            best_kind = kind
            best_rate = rate
    if best_amount > money(subtotal):
        best_amount = money(subtotal)
    return best_amount, best_kind, best_rate


def normalize_selection(service, option_ids):
    ids = []
    for raw in option_ids or []:
        try:
            ids.append(int(raw))
        except (TypeError, ValueError):
            continue
    if not ids:
        return []
    found = PriceVariable.objects.filter(
        pk__in=ids,
        is_active=True,
        category__is_active=True,
        category__services=service,
    ).select_related("category")
    by_id = {variable.pk: variable for variable in found}
    chosen = []
    seen_single = set()
    for pk in ids:
        variable = by_id.get(pk)
        if variable is None:
            continue
        if variable.category.input_type == PriceVariableCategory.InputType.SINGLE:
            if variable.category_id in seen_single:
                continue
            seen_single.add(variable.category_id)
        chosen.append(variable)
    return chosen


def selection_is_complete(service, variables):
    chosen = {variable.category_id for variable in variables}
    required = (
        PriceVariableCategory.objects.filter(
            is_active=True,
            services=service,
            input_type=PriceVariableCategory.InputType.SINGLE,
            variables__is_active=True,
        )
        .distinct()
    )
    return all(category.pk in chosen for category in required)


def line_label(variable):
    return f"{variable.category.name}: {variable.name}"


def store_calculated_quote(quote, variables):
    amounts = [money(variable.price) for variable in variables]
    subtotal = money(sum(amounts, Decimal("0")))
    discount, kind, rate = discount_for_selection(variables, subtotal)
    totals = calculate_quote(amounts, discount, TaxSettings.get_tax_rate())
    QuoteLineItem.objects.bulk_create(
        [
            QuoteLineItem(
                quote=quote,
                price_variable=variable,
                label=line_label(variable),
                amount=money(variable.price),
                discount_kind=variable.discount_kind,
                discount_percent=variable.discount_percent or 0,
                discount_amount=variable.discount_amount or 0,
                sort_order=index,
            )
            for index, variable in enumerate(variables)
        ]
    )
    apply_totals(quote, totals)
    quote.discount_kind = kind
    quote.discount_rate = rate
    quote.save(update_fields=["discount_kind", "discount_rate"])
    return totals


def recalculate_stored_quote(quote, kind, value):
    amounts = [line.amount for line in quote.line_items.all()]
    subtotal = money(sum((Decimal(amount) for amount in amounts), Decimal("0")))
    discount, rate = discount_dollars(subtotal, kind, value)
    totals = calculate_quote(amounts, discount, TaxSettings.get_tax_rate())
    apply_totals(quote, totals)
    quote.discount_kind = kind if kind in DiscountKind.values else DiscountKind.AMOUNT
    quote.discount_rate = rate
    quote.save(update_fields=["discount_kind", "discount_rate"])
    return totals


def apply_totals(quote, totals):
    for field, value in totals.items():
        setattr(quote, field, value)
    quote.save(update_fields=list(totals.keys()))


def build_scope(quote):
    parts = [f"{line.label} ${money(line.amount)}" for line in quote.line_items.all()]
    if quote.discount_amount:
        if quote.discount_kind == DiscountKind.PERCENT:
            parts.append(f"Discount {money(quote.discount_rate)}% -${money(quote.discount_amount)}")
        else:
            parts.append(f"Discount -${money(quote.discount_amount)}")
    parts.append(f"Tax {quote.tax_rate}% ${money(quote.tax_amount)}")
    if not parts:
        return "Staff confirmed price"
    return "; ".join(parts)


def confirm_quote(quote, user):
    scope = build_scope(quote)
    estimate, _created = QuoteEstimate.objects.update_or_create(
        quote=quote,
        defaults={
            "price": quote.total,
            "scope": scope,
            "created_by": user,
        },
    )
    return estimate
