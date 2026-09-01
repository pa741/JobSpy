"""
Whether a LinkedIn posting applies on the employer's own system.

Every fixture here is synthetic. The markup is reduced to the attributes the parser
actually reads, copied from what the live guest page served on 2026-09-01 - no scraped
job content is committed, which is the same rule the platform repository's CSV fixture
follows and matters for the same reason: a real page carries a real employer's advert.

The cases are the ones that were wrong before this parser existed. A posting with no
apply URL used to be indistinguishable from Easy Apply, and on a live corpus of 4,470
LinkedIn postings that read every single one as Easy Apply.
"""

from bs4 import BeautifulSoup

from jobspy.linkedin import LinkedIn


def parse(html: str, job_url_direct: str | None = None) -> bool | None:
    return LinkedIn()._parse_offsite_apply(
        BeautifulSoup(html, "html.parser"), job_url_direct
    )


# The apply affordance every rendered posting carries, offsite or not.
APPLY_BUTTON = (
    '<button class="sign-up-modal__outlet top-card-layout__cta btn-primary" '
    'data-tracking-control-name="public_jobs_contextual-sign-in-modal_ssr-ui-lib-outlet-button" '
    'data-modal="job-details-topcard-apply-modal">Apply</button>'
)

OFFSITE_ICON = (
    '<icon data-svg-class-name="apply-button__offsite-apply-icon-svg" '
    'data-delayed-url="https://static.licdn.com/aero-v1/sc/h/x"></icon>'
)

OFFSITE_MODAL = (
    '<div class="contextual-sign-in-modal" '
    'data-impression-id="public_jobs_apply-link-offsite_contextual-sign-in-modal"></div>'
)


def test_a_published_url_settles_it_without_reading_the_page():
    # A URL is strictly better evidence than any marker, and it is what LinkedIn used to
    # publish. If it ever comes back, it wins.
    assert parse("<html></html>", "https://careers.example.invalid/123") is True


def test_the_offsite_icon_alone_is_enough():
    assert parse(f"<html><body>{APPLY_BUTTON}{OFFSITE_ICON}</body></html>") is True


def test_the_offsite_sign_in_modal_alone_is_enough():
    # The two markers are independent. Either surviving a redesign keeps the column
    # populated, which is the point of reading both.
    assert parse(f"<html><body>{APPLY_BUTTON}{OFFSITE_MODAL}</body></html>") is True


def test_the_offsite_tracking_name_alone_is_enough():
    html = (
        f"<html><body>{APPLY_BUTTON}"
        '<a data-tracking-control-name="public_jobs_apply-link-offsite_contextual-sign-in-modal_join-link"'
        ' href="https://www.linkedin.com/signup/cold-join">Join</a>'
        "</body></html>"
    )
    assert parse(html) is True


def test_an_apply_button_with_no_offsite_marker_is_easy_apply():
    # The board hosts it. Asserted only because the button was there to read - see below
    # for why that distinction is the whole point.
    assert parse(f"<html><body>{APPLY_BUTTON}</body></html>") is False


def test_a_page_with_no_apply_affordance_establishes_nothing():
    # The failure this parser exists to undo. A page that did not render its top card -
    # a signup wall, a truncated response, a redesign - says nothing about how the job
    # is applied to, and reporting that as "the board hosts it" is how 4,470 postings
    # came to be labelled Easy Apply.
    assert parse("<html><body><p>Some description</p></body></html>") is None


def test_a_signup_wall_is_not_read_as_easy_apply():
    html = (
        "<html><body>"
        '<div class="show-more-less-html__markup">A description that did load.</div>'
        '<code id="i18n_sign_in_form_show_text">Show</code>'
        "</body></html>"
    )
    assert parse(html) is None


def test_the_offsite_marker_wins_over_a_missing_url():
    # The case the live corpus is entirely made of: offsite, and no URL to be had.
    assert parse(f"<html><body>{APPLY_BUTTON}{OFFSITE_ICON}</body></html>", None) is True
