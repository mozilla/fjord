from fjord.events.models import get_product_details_history


def test_get_product_details_history():
    # FIXME: This just tests whether it crashes or not because we
    # don't want to test the data contents.
    data = get_product_details_history()
    assert len(data) > 0
