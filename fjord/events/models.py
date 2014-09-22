from product_details import product_details


def get_product_details_history():
    sections = [
        (u'Firefox', 'firefox_history_development_releases'),
        (u'Firefox', 'firefox_history_major_releases'),
        (u'Firefox', 'firefox_history_stability_releases'),
        (u'Firefox for Android', 'mobile_history_development_releases'),
        (u'Firefox for Android', 'mobile_history_major_releases'),
        (u'Firefox for Android', 'mobile_history_stability_releases')
    ]

    events = []
    for product, section in sections:
        data = getattr(product_details, section)
        events.extend([
            {
                'product': product,
                'date': date,
                'version': version
            } for version, date in data.items()
        ])

    # Sort the events list by (date, product)
    events.sort(key=lambda item: (item['date'], item['product']))
    return events
